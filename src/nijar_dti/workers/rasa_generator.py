"""Generador de los artefactos Rasa a partir de las FAQs del seed.

Lee :mod:`nijar_dti.data.seeds.faqs.FAQS_SEED` y produce:

- ``rasa/domain.yml``  — intents y respuestas multilingües
- ``rasa/data/nlu.yml`` — ejemplos de entrenamiento
- ``rasa/data/rules.yml`` — reglas intent → utter
- ``rasa/data/stories.yml`` — historia mínima por intent

Mantiene **una única fuente de verdad**: las FAQs del seed. Si se añade una
FAQ, basta con re-ejecutar este script para regenerar la configuración Rasa.

Uso::

    python -m nijar_dti.workers.rasa_generator
    # o, fuera del contenedor:
    python scripts/generate_rasa_from_faqs.py
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# El generador es una herramienta CLI puramente offline: no necesita BBDD
# real. Si el entorno no tiene configurada la app, asignamos valores mínimos
# antes del primer import del paquete para evitar errores de Pydantic.
os.environ.setdefault("SECRET_KEY", "rasa-generator-dummy-secret-key-32bytes-min")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://x:x@localhost:5432/x",
)

import yaml

from nijar_dti.data.seeds.faqs import FAQS_SEED

log = logging.getLogger(__name__)

_DEFAULT_OUT = Path(__file__).resolve().parents[3] / "rasa"


def _utter_name(intent: str) -> str:
    return f"utter_{intent}"


def _representar_cadena(dumper: yaml.SafeDumper, data: str) -> yaml.ScalarNode:
    """Serializa cadenas multilínea como bloque literal (``|``), formato canónico Rasa."""
    estilo = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=estilo)


yaml.SafeDumper.add_representer(str, _representar_cadena)


def _yaml_dump(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        # Cabecera Rasa
        fh.write("# Generado automáticamente desde nijar_dti.data.seeds.faqs\n")
        fh.write("# NO EDITAR A MANO — ejecutar `python -m nijar_dti.workers.rasa_generator`\n\n")
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)


def build_domain() -> dict:
    intents = [faq["intent"] for faq in FAQS_SEED]
    intents.append("nlu_fallback")

    responses: dict[str, list[dict]] = {}
    for faq in FAQS_SEED:
        utter = _utter_name(faq["intent"])
        # Rasa permite múltiples variantes por idioma usando el campo `condition`
        # (channel/language). Aquí publicamos las 4 traducciones como variantes.
        variantes: list[dict] = []
        for lang in ("es", "en", "de", "fr"):
            txt = faq.get(f"respuesta_{lang}")
            if not txt:
                continue
            variantes.append({"text": txt, "condition": [{"type": "slot", "name": "language", "value": lang}]})
        # fallback: respuesta en español sin condición
        variantes.append({"text": faq["respuesta_es"]})
        responses[utter] = variantes

    # Respuesta de fallback fuera de dominio
    responses["utter_default"] = [
        {"text": "No dispongo de información sobre esa consulta. ¿Puedo ayudarte con rutas, playas, eventos o servicios turísticos de Níjar?",
         "condition": [{"type": "slot", "name": "language", "value": "es"}]},
        {"text": "I don't have information about that. Can I help you with routes, beaches, events, or services in Níjar?",
         "condition": [{"type": "slot", "name": "language", "value": "en"}]},
        {"text": "Dazu habe ich leider keine Informationen. Kann ich Ihnen bei Routen, Stränden, Veranstaltungen oder Dienstleistungen in Níjar helfen?",
         "condition": [{"type": "slot", "name": "language", "value": "de"}]},
        {"text": "Je ne dispose pas d'informations sur ce sujet. Puis-je vous aider avec les itinéraires, plages, événements ou services à Níjar ?",
         "condition": [{"type": "slot", "name": "language", "value": "fr"}]},
        {"text": "No dispongo de información sobre esa consulta. ¿Puedo ayudarte con rutas, playas, eventos o servicios turísticos de Níjar?"},
    ]

    return {
        "version": "3.1",
        "intents": sorted(set(intents)),
        "slots": {
            "language": {
                "type": "categorical",
                "values": ["es", "en", "de", "fr"],
                "initial_value": "es",
                "influence_conversation": True,
                "mappings": [{"type": "from_text"}],
            },
        },
        "responses": responses,
        "session_config": {
            "session_expiration_time": 60,
            "carry_over_slots_to_new_session": True,
        },
    }


def build_nlu() -> dict:
    nlu_items: list[dict] = []
    for faq in FAQS_SEED:
        ejemplos: list[str] = []
        for lang in ("es", "en", "de", "fr"):
            preg = faq.get(f"pregunta_{lang}")
            if preg:
                ejemplos.append(preg)
            for frase in faq.get(f"frases_entrenamiento_{lang}") or []:
                if frase:
                    ejemplos.append(frase)
        # Si solo hubiera una pregunta canónica, evitamos duplicados
        ejemplos_dedup = []
        seen: set[str] = set()
        for e in ejemplos:
            key = e.strip().lower()
            if key and key not in seen:
                seen.add(key)
                ejemplos_dedup.append(e.strip())
        if not ejemplos_dedup:
            continue
        bloque = "\n".join(f"- {e}" for e in ejemplos_dedup)
        # El valor NO debe incluir el carácter "|": el estilo de bloque literal
        # lo aplica el representer de _yaml_dump. Incluirlo aquí hacía que Rasa
        # recibiera una línea "|" espuria y la descartara con un aviso.
        nlu_items.append({"intent": faq["intent"], "examples": f"{bloque}\n"})
    return {"version": "3.1", "nlu": nlu_items}


def build_rules() -> dict:
    rules: list[dict] = []
    for faq in FAQS_SEED:
        rules.append({
            "rule": f"Responder a {faq['intent']}",
            "steps": [
                {"intent": faq["intent"]},
                {"action": _utter_name(faq["intent"])},
            ],
        })
    rules.append({
        "rule": "Fallback fuera de dominio",
        "steps": [
            {"intent": "nlu_fallback"},
            {"action": "utter_default"},
        ],
    })
    return {"version": "3.1", "rules": rules}


def build_stories() -> dict:
    stories: list[dict] = []
    for faq in FAQS_SEED[:5]:
        stories.append({
            "story": f"happy path {faq['intent']}",
            "steps": [
                {"intent": faq["intent"]},
                {"action": _utter_name(faq["intent"])},
            ],
        })
    return {"version": "3.1", "stories": stories}


def write_all(out_dir: Path) -> None:
    domain_path = out_dir / "domain.yml"
    nlu_path = out_dir / "data" / "nlu.yml"
    rules_path = out_dir / "data" / "rules.yml"
    stories_path = out_dir / "data" / "stories.yml"
    _yaml_dump(build_domain(), domain_path)
    _yaml_dump(build_nlu(), nlu_path)
    _yaml_dump(build_rules(), rules_path)
    _yaml_dump(build_stories(), stories_path)
    log.info("Archivos Rasa generados en %s", out_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=_DEFAULT_OUT)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    write_all(args.out_dir)


if __name__ == "__main__":
    main()
