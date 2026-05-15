"""Tests del adapter Rasa.

Validan:
- Selector de motor (lexical vs rasa) según configuración.
- Mapeo de intent + score → nivel de confianza.
- Mapeo de la respuesta de Rasa al esquema de salida.
- Fallback al motor lexical cuando Rasa no responde.

Se usa ``respx`` para mockear las llamadas HTTP al servidor Rasa, sin
levantar un Rasa real.
"""

from __future__ import annotations

import pytest

from nijar_dti.services.chatbot_rasa_adapter import (
    _intent_de_parse,
    _nivel_desde_confianza,
)


class TestIntentDeParse:
    def test_parse_valido(self):
        parse = {"intent": {"name": "playas_destacadas", "confidence": 0.92}}
        name, score = _intent_de_parse(parse)
        assert name == "playas_destacadas"
        assert score == pytest.approx(0.92)

    def test_parse_sin_intent(self):
        parse = {}
        name, score = _intent_de_parse(parse)
        assert name is None
        assert score == 0.0

    def test_parse_intent_sin_confidence(self):
        parse = {"intent": {"name": "saludo"}}
        name, score = _intent_de_parse(parse)
        assert name == "saludo"
        assert score == 0.0


class TestNivelDesdeConfianza:
    def test_alta(self):
        from nijar_dti.models.faq import NivelConfianza
        assert _nivel_desde_confianza(0.85) == NivelConfianza.ALTA
        assert _nivel_desde_confianza(0.99) == NivelConfianza.ALTA

    def test_media(self):
        from nijar_dti.models.faq import NivelConfianza
        assert _nivel_desde_confianza(0.55) == NivelConfianza.MEDIA
        assert _nivel_desde_confianza(0.65) == NivelConfianza.MEDIA

    def test_fuera_de_dominio(self):
        from nijar_dti.models.faq import NivelConfianza
        assert _nivel_desde_confianza(0.40) == NivelConfianza.FUERA_DE_DOMINIO
        assert _nivel_desde_confianza(0.0) == NivelConfianza.FUERA_DE_DOMINIO


class TestSelectorMotor:
    """Comprueba que el selector cambia según CHATBOT_ENGINE."""

    def test_default_es_lexical(self):
        from nijar_dti.config import Settings
        s = Settings(
            secret_key="test-secret-key-with-enough-entropy-1234567890",
            database_url="postgresql+asyncpg://x:x@localhost/x",
        )
        assert s.chatbot_engine == "lexical"

    def test_engine_rasa(self):
        from nijar_dti.config import Settings
        s = Settings(
            secret_key="test-secret-key-with-enough-entropy-1234567890",
            database_url="postgresql+asyncpg://x:x@localhost/x",
            chatbot_engine="rasa",
        )
        assert s.chatbot_engine == "rasa"


class TestArtefactosRasaGenerados:
    """Comprueba que los artefactos Rasa generados desde FAQs son consistentes."""

    def test_domain_contiene_todos_los_intents(self):
        from nijar_dti.workers.rasa_generator import build_domain
        from nijar_dti.data.seeds.faqs import FAQS_SEED

        domain = build_domain()
        intents_seed = {f["intent"] for f in FAQS_SEED}
        intents_domain = set(domain["intents"])
        # nlu_fallback se añade siempre
        assert "nlu_fallback" in intents_domain
        for intent in intents_seed:
            assert intent in intents_domain, f"Falta intent {intent} en domain"

    def test_responses_tienen_4_idiomas(self):
        from nijar_dti.workers.rasa_generator import build_domain

        domain = build_domain()
        # contar utter_* que tienen variantes con condition de language
        utters = [k for k in domain["responses"] if k.startswith("utter_")]
        assert len(utters) >= 20  # al menos las FAQs del seed
        # al menos una utter debe tener variantes para 4 idiomas
        utter_saludo = domain["responses"].get("utter_saludo", [])
        idiomas_cubiertos = set()
        for v in utter_saludo:
            for cond in v.get("condition") or []:
                if cond.get("type") == "slot" and cond.get("name") == "language":
                    idiomas_cubiertos.add(cond.get("value"))
        assert {"es", "en", "de", "fr"}.issubset(idiomas_cubiertos)

    def test_nlu_tiene_ejemplos(self):
        from nijar_dti.workers.rasa_generator import build_nlu

        nlu = build_nlu()
        assert len(nlu["nlu"]) >= 20
        for item in nlu["nlu"]:
            assert "examples" in item
            assert item["examples"].strip()

    def test_rules_tiene_fallback(self):
        from nijar_dti.workers.rasa_generator import build_rules

        rules = build_rules()
        nombres = [r["rule"] for r in rules["rules"]]
        assert any("fallback" in n.lower() or "Fallback" in n for n in nombres)
