"""Tests de los datos seed: cobertura, formato y consistencia."""

from __future__ import annotations

from nijar_dti.data.seeds.faqs import FAQS_SEED
from nijar_dti.data.seeds.recursos_turisticos import RECURSOS_SEED
from nijar_dti.data.seeds.sensores import SENSORES_SEED


class TestRecursosSeed:
    def test_minimo_recursos(self):
        # Compromiso mínimo: cubrir las playas y POIs principales
        assert len(RECURSOS_SEED) >= 12

    def test_urns_unicos(self):
        urns = [r["urn"] for r in RECURSOS_SEED]
        assert len(urns) == len(set(urns))

    def test_categorias_validas(self):
        validas = {
            "playa", "monumento", "ruta", "mirador", "centro_visitantes",
            "parque_natural", "museo", "yacimiento", "punto_interes",
            "oficina_turismo",
        }
        for r in RECURSOS_SEED:
            assert r["categoria"] in validas, f"Categoría inválida en {r['urn']}"

    def test_coordenadas_dentro_nijar(self):
        # Bounding box aproximado de Níjar y su parque natural
        for r in RECURSOS_SEED:
            assert 36.5 <= r["lat"] <= 37.1, f"Lat fuera de rango: {r['urn']}"
            assert -2.4 <= r["lon"] <= -1.8, f"Lon fuera de rango: {r['urn']}"

    def test_urns_estandar_fiware(self):
        for r in RECURSOS_SEED:
            assert r["urn"].startswith("urn:ngsi-ld:RecursoTuristico:nijar:")


class TestSensoresSeed:
    def test_minimo_sensores_smart_office(self):
        # Compromiso A.2: sensores ambientales (CO2, temp, hum, ruido)
        tipos_smart_office = {
            "ambiental_co2", "ambiental_temperatura",
            "ambiental_humedad", "ambiental_ruido",
        }
        encontrados = {s["tipo"] for s in SENSORES_SEED if "smartoffice" in s["urn"]}
        assert tipos_smart_office.issubset(encontrados)

    def test_sensores_totems(self):
        # Compromiso A.1: 2 tótems con sensores asociados
        urns_totems = [s["urn"] for s in SENSORES_SEED if "totem" in s["urn"]]
        # Cada tótem (rodalquilar y albaricoques) tiene al menos 2 sensores (meteo + aforo)
        rodalquilar = [u for u in urns_totems if "rodalquilar" in u]
        albaricoques = [u for u in urns_totems if "albaricoques" in u]
        assert len(rodalquilar) >= 2
        assert len(albaricoques) >= 2

    def test_urns_unicos(self):
        urns = [s["urn"] for s in SENSORES_SEED]
        assert len(urns) == len(set(urns))


class TestFAQsSeed:
    def test_categorias_minimas_cubiertas(self):
        categorias_obligatorias = {"playas", "parque", "rutas", "servicios", "emergencias"}
        encontradas = {f["categoria"] for f in FAQS_SEED}
        assert categorias_obligatorias.issubset(encontradas)

    def test_intents_unicos(self):
        intents = [f["intent"] for f in FAQS_SEED]
        assert len(intents) == len(set(intents))

    def test_todas_tienen_respuesta_es(self):
        for f in FAQS_SEED:
            assert f.get("respuesta_es"), f"FAQ {f['intent']} sin respuesta_es"
            assert f.get("pregunta_es"), f"FAQ {f['intent']} sin pregunta_es"

    def test_cobertura_ingles(self):
        """Compromiso: cobertura mínima del 80% en inglés en la base inicial."""
        con_ingles = sum(1 for f in FAQS_SEED if f.get("respuesta_en"))
        ratio = con_ingles / len(FAQS_SEED)
        assert ratio >= 0.8, f"Cobertura EN insuficiente: {ratio:.0%}"

    def test_niveles_confianza_validos(self):
        validos = {"alta", "media", "fuera_de_dominio"}
        for f in FAQS_SEED:
            nivel = f.get("nivel_confianza", "alta")
            assert nivel in validos, f"Nivel de confianza inválido en {f['intent']}: {nivel}"

    def test_emergencias_son_alta_confianza(self):
        """Las FAQs de emergencias deben siempre estar marcadas como alta confianza."""
        for f in FAQS_SEED:
            if f["categoria"] == "emergencias":
                assert f.get("nivel_confianza", "alta") == "alta", (
                    f"FAQ de emergencia {f['intent']} no es de alta confianza"
                )
