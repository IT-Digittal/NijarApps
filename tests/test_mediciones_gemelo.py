"""Tests de las mediciones guardadas de la regla del gemelo (cálculo + esquema)."""

from __future__ import annotations

import math

import pytest

from nijar_dti.schemas.geografia import MedicionGemeloIn
from nijar_dti.services.geografia_service import area_esferica_m2, distancia_geodesica_m


class TestDistanciaGeodesica:
    def test_un_grado_de_latitud(self):
        # 1° de latitud ≈ 111,2 km en cualquier meridiano
        d = distancia_geodesica_m([(36.0, -2.1), (37.0, -2.1)])
        assert d == pytest.approx(111_195, rel=0.01)

    def test_acumula_tramos(self):
        pts = [(36.0, -2.1), (36.5, -2.1), (37.0, -2.1)]
        assert distancia_geodesica_m(pts) == pytest.approx(
            distancia_geodesica_m(pts[:2]) + distancia_geodesica_m(pts[1:]), rel=1e-9
        )

    def test_mismo_punto_es_cero(self):
        assert distancia_geodesica_m([(36.9, -2.1), (36.9, -2.1)]) == 0.0


class TestAreaEsferica:
    def test_cuadrado_conocido_en_nijar(self):
        # «Cuadrado» de 0,01° × 0,01° a ~36,95° N ≈ 1.113 m × 889 m ≈ 0,99 km²
        anillo = [(36.95, -2.10), (36.95, -2.09), (36.96, -2.09), (36.96, -2.10)]
        lado_ns = 0.01 * 111_195
        lado_eo = lado_ns * math.cos(math.radians(36.955))
        assert area_esferica_m2(anillo) == pytest.approx(lado_ns * lado_eo, rel=0.01)

    def test_orientacion_indiferente(self):
        anillo = [(36.95, -2.10), (36.95, -2.09), (36.96, -2.09), (36.96, -2.10)]
        assert area_esferica_m2(anillo) == pytest.approx(
            area_esferica_m2(list(reversed(anillo))), rel=1e-9
        )


class TestMedicionGemeloIn:
    def test_valida(self):
        m = MedicionGemeloIn(nombre="Sendero", puntos=[(36.9, -2.1), (36.91, -2.09)])
        assert m.tipo == "linea"

    def test_minimo_dos_puntos(self):
        with pytest.raises(ValueError):
            MedicionGemeloIn(nombre="Corta", puntos=[(36.9, -2.1)])

    def test_coordenadas_fuera_de_rango(self):
        with pytest.raises(ValueError, match="fuera de rango"):
            MedicionGemeloIn(nombre="Mala", puntos=[(96.0, -2.1), (36.9, -2.1)])

    def test_tipo_invalido(self):
        with pytest.raises(ValueError):
            MedicionGemeloIn(nombre="X", tipo="circulo", puntos=[(36.9, -2.1), (36.91, -2.09)])
