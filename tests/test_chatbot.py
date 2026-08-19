"""Tests unitarios del motor de matching del chatbot.

Estos tests prueban la lógica pura (tokenización, similitud, selección de
intent) sin necesidad de BBDD.
"""

from __future__ import annotations

from nijar_dti.services.chatbot_service import (
    UMBRAL_CONFIANZA_ALTA,
    UMBRAL_CONFIANZA_MEDIA,
    _buscar_mejor_intent,
    _normalizar,
    _similitud,
    _tokenizar,
)


# Stub mínimo de FAQ para los tests (sin tocar BBDD)
class _FakeFAQ:
    def __init__(
        self,
        intent: str,
        pregunta_es: str,
        pregunta_en: str | None = None,
        pregunta_de: str | None = None,
        pregunta_fr: str | None = None,
        frases_entrenamiento_es: list[str] | None = None,
        frases_entrenamiento_en: list[str] | None = None,
        frases_entrenamiento_de: list[str] | None = None,
        frases_entrenamiento_fr: list[str] | None = None,
        respuesta_es: str = "respuesta",
    ) -> None:
        self.intent = intent
        self.pregunta_es = pregunta_es
        self.pregunta_en = pregunta_en
        self.pregunta_de = pregunta_de
        self.pregunta_fr = pregunta_fr
        self.frases_entrenamiento_es = frases_entrenamiento_es
        self.frases_entrenamiento_en = frases_entrenamiento_en
        self.frases_entrenamiento_de = frases_entrenamiento_de
        self.frases_entrenamiento_fr = frases_entrenamiento_fr
        self.respuesta_es = respuesta_es


class TestNormalizacion:
    def test_normalizar_quita_acentos(self):
        assert _normalizar("Mónsul") == "monsul"
        assert _normalizar("ÁÉÍÓÚáéíóúñ") == "aeiouaeioun"

    def test_normalizar_minusculas(self):
        assert _normalizar("HOLA Mundo") == "hola mundo"

    def test_normalizar_strip(self):
        assert _normalizar("  hola  ") == "hola"


class TestTokenizacion:
    def test_quita_stopwords_es(self):
        tokens = _tokenizar("¿Cuáles son las playas más bonitas?", "es")
        assert "playas" in tokens
        assert "bonitas" in tokens
        assert "las" not in tokens
        assert "son" not in tokens

    def test_quita_stopwords_en(self):
        tokens = _tokenizar("Where are the best beaches?", "en")
        assert "beaches" in tokens
        assert "best" in tokens
        assert "the" not in tokens

    def test_idioma_desconocido_no_falla(self):
        # idioma sin entrada en stop words → tokeniza igual
        tokens = _tokenizar("hello world", "zh")
        assert "hello" in tokens
        assert "world" in tokens


class TestSimilitud:
    def test_identicos(self):
        a = {"playa", "monsul"}
        assert _similitud(a, a) == 1.0

    def test_disjuntos(self):
        assert _similitud({"a"}, {"b"}) == 0.0

    def test_parcial(self):
        sim = _similitud({"a", "b"}, {"b", "c"})
        assert 0 < sim < 1

    def test_vacio(self):
        assert _similitud(set(), {"a"}) == 0.0


class TestMatchingIntent:
    def test_match_alto_es(self):
        faqs = [
            _FakeFAQ(
                intent="playas_destacadas",
                pregunta_es="¿Cuáles son las playas más conocidas?",
                frases_entrenamiento_es=["mejores playas", "playas turisticas"],
            ),
            _FakeFAQ(
                intent="otra",
                pregunta_es="¿Qué hora es?",
            ),
        ]
        intent, score = _buscar_mejor_intent("qué playas más conocidas hay", "es", faqs)
        assert intent is not None
        assert intent.intent == "playas_destacadas"
        assert score > 0

    def test_match_idioma_distinto(self):
        faqs = [
            _FakeFAQ(
                intent="playas",
                pregunta_es="playas",
                pregunta_en="What beaches are there?",
                frases_entrenamiento_en=["best beaches", "where to swim"],
            )
        ]
        intent, score = _buscar_mejor_intent("best beaches please", "en", faqs)
        assert intent is not None
        assert intent.intent == "playas"
        assert score > 0

    def test_no_match_devuelve_score_bajo(self):
        faqs = [
            _FakeFAQ(
                intent="playas",
                pregunta_es="playas conocidas",
            )
        ]
        intent, score = _buscar_mejor_intent("xyzzy plugh foobar", "es", faqs)
        # tokens distintos: score debe ser bajo (puede ser 0 si nada coincide)
        assert score < UMBRAL_CONFIANZA_MEDIA

    def test_pregunta_vacia(self):
        faqs = [_FakeFAQ(intent="x", pregunta_es="hola")]
        intent, score = _buscar_mejor_intent("   ", "es", faqs)
        assert intent is None
        assert score == 0.0

    def test_lista_faqs_vacia(self):
        intent, score = _buscar_mejor_intent("playas", "es", [])
        assert intent is None
        assert score == 0.0


class TestUmbrales:
    def test_orden_umbrales(self):
        # alta > media → coherencia del modelo
        assert UMBRAL_CONFIANZA_ALTA > UMBRAL_CONFIANZA_MEDIA
        assert 0 < UMBRAL_CONFIANZA_MEDIA < UMBRAL_CONFIANZA_ALTA <= 1
