"""Tests unitarios del motor NLP de Social Listening."""

from __future__ import annotations

from nijar_dti.connectors.social.nlp import (
    analizar_sentimiento,
    detectar_entidades,
    detectar_idioma,
    extraer_temas,
)


class TestDetectarIdioma:
    def test_espanol(self):
        assert detectar_idioma("El atardecer en la playa de Mónsul es mágico") == "es"

    def test_ingles(self):
        assert detectar_idioma("The best beach is amazing and beautiful") == "en"

    def test_aleman(self):
        assert detectar_idioma("Der Strand ist sehr schön und wunderbar") == "de"

    def test_frances(self):
        assert detectar_idioma("La plage est magnifique et incroyable") == "fr"

    def test_texto_vacio_devuelve_default(self):
        assert detectar_idioma("") == "es"

    def test_texto_sin_marcadores_devuelve_default(self):
        # solo nombres propios y dígitos
        assert detectar_idioma("Níjar 2026") in {"es", "en", "de", "fr"}


class TestSentimiento:
    def test_positivo_es(self):
        a = analizar_sentimiento("La playa es preciosa y la gente súper amable", "es")
        assert a.etiqueta == "positivo"
        assert a.score > 0
        assert a.palabras_positivas >= 2

    def test_negativo_es(self):
        a = analizar_sentimiento("Una experiencia horrible y muy decepcionante", "es")
        assert a.etiqueta == "negativo"
        assert a.score < 0

    def test_negacion_invierte_polaridad(self):
        # "no recomiendo" debe contar como negativo, no positivo
        a = analizar_sentimiento("No lo recomiendo en absoluto", "es")
        assert a.etiqueta in {"negativo", "neutro"}
        assert a.score <= 0

    def test_neutro(self):
        a = analizar_sentimiento("Visité Níjar el martes pasado", "es")
        assert a.etiqueta == "neutro"
        assert a.score == 0.0

    def test_positivo_en(self):
        a = analizar_sentimiento("Best beach ever, amazing sunset and lovely people", "en")
        assert a.etiqueta == "positivo"

    def test_positivo_de(self):
        a = analizar_sentimiento("Wunderbar, sehr schön und einzigartig", "de")
        assert a.etiqueta == "positivo"

    def test_positivo_fr(self):
        a = analizar_sentimiento("Magnifique, je recommande vivement", "fr")
        assert a.etiqueta == "positivo"

    def test_texto_vacio(self):
        a = analizar_sentimiento("", "es")
        assert a.etiqueta == "neutro"
        assert a.score == 0.0


class TestExtraerTemas:
    def test_playa(self):
        temas = extraer_temas("Hoy fui a la playa de Mónsul, el atardecer fue mágico")
        assert "playa" in temas
        assert "atardecer" in temas

    def test_ruta_y_parque(self):
        temas = extraer_temas("Hicimos la ruta de Rodalquilar a Albaricoques en bici")
        assert "ruta" in temas

    def test_gastronomia(self):
        temas = extraer_temas("Comimos pescado fresco en un restaurante en Isleta del Moro")
        assert "gastronomia" in temas

    def test_alojamiento(self):
        temas = extraer_temas("We stayed in a beautiful hotel in San José")
        assert "alojamiento" in temas

    def test_accesibilidad(self):
        temas = extraer_temas("La playa accesible con silla de ruedas es genial")
        assert "accesibilidad" in temas

    def test_masificacion(self):
        temas = extraer_temas("Estaba muy masificado y con colas para entrar")
        assert "masificacion" in temas

    def test_max_temas(self):
        # texto con muchas categorías: solo devuelve hasta el máximo
        temas = extraer_temas(
            "playa ruta hotel restaurante museo foto silla masificado",
            max_temas=3,
        )
        assert len(temas) <= 3

    def test_texto_sin_temas(self):
        assert extraer_temas("xyz qwerty 1234") == []


class TestDetectarEntidades:
    def test_monsul(self):
        ent = detectar_entidades("El atardecer en Mónsul fue espectacular")
        assert "urn:ngsi-ld:RecursoTuristico:nijar:playa-monsul" in ent

    def test_san_jose(self):
        ent = detectar_entidades("Nos alojamos en San José esta semana")
        assert "urn:ngsi-ld:RecursoTuristico:nijar:san-jose" in ent

    def test_amoladeras(self):
        ent = detectar_entidades("Pasamos por el centro Las Amoladeras")
        assert "urn:ngsi-ld:RecursoTuristico:nijar:centro-amoladeras" in ent

    def test_rodalquilar_y_albaricoques(self):
        ent = detectar_entidades("Ruta Rodalquilar–Albaricoques en bicicleta, increíble")
        assert "urn:ngsi-ld:RecursoTuristico:nijar:rodalquilar-mina" in ent
        assert "urn:ngsi-ld:RecursoTuristico:nijar:los-albaricoques" in ent

    def test_sin_entidades(self):
        assert detectar_entidades("Algo genérico sin lugares conocidos") == []
