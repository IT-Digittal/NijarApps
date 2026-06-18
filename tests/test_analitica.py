"""Tests de las funciones puras de analítica (NPS proxy y composición lingüística)."""

from __future__ import annotations

from collections import Counter

from nijar_dti.services.analitica_service import (
    _normaliza_idioma,
    banda_confianza_pp,
    calcular_nps,
    componer_idiomas,
)


class TestCalcularNPS:
    def test_solo_promotores(self):
        assert calcular_nps(10, 0, 0) == 100.0

    def test_solo_detractores(self):
        assert calcular_nps(0, 0, 10) == -100.0

    def test_mezcla(self):
        # 60 pro, 20 pas, 20 det -> (60-20)/100 = 40
        assert calcular_nps(60, 20, 20) == 40.0

    def test_muestra_vacia(self):
        assert calcular_nps(0, 0, 0) == 0.0

    def test_rango_valido(self):
        v = calcular_nps(7, 2, 1)
        assert -100 <= v <= 100


class TestBandaConfianza:
    def test_sin_muestra(self):
        assert banda_confianza_pp(0, 0) == 0.0

    def test_decrece_con_mas_muestra(self):
        pocas = banda_confianza_pp(50, 100)
        muchas = banda_confianza_pp(500, 1000)
        assert muchas < pocas

    def test_valor_razonable(self):
        # p=0.5, n=100 -> 1.96*0.05*100 = 9.8 pp
        assert abs(banda_confianza_pp(50, 100) - 9.8) < 0.1


class TestComponerIdiomas:
    def test_aplica_k_anonimato_y_porcentajes(self):
        conteos = Counter({"es": 120, "en": 40, "de": 3})
        lista, total, suprimidos = componer_idiomas(conteos, k=5)
        # de(3) suprimido pero cuenta en el total
        assert total == 163
        assert suprimidos == 3
        idiomas = {i.idioma for i in lista}
        assert idiomas == {"es", "en"}
        # porcentaje sobre el total original (163), no sobre el publicable
        es = next(i for i in lista if i.idioma == "es")
        assert abs(es.porcentaje - round(120 * 100 / 163, 2)) < 0.01

    def test_orden_descendente(self):
        conteos = Counter({"es": 10, "en": 30, "fr": 20})
        lista, _, _ = componer_idiomas(conteos, k=1)
        assert [i.idioma for i in lista] == ["en", "fr", "es"]

    def test_vacio(self):
        lista, total, suprimidos = componer_idiomas(Counter())
        assert lista == []
        assert total == 0
        assert suprimidos == 0


def test_normaliza_idioma():
    assert _normaliza_idioma("es-ES") == "es"
    assert _normaliza_idioma("EN") == "en"
    assert _normaliza_idioma(None) == "desconocido"
    assert _normaliza_idioma("") == "desconocido"
