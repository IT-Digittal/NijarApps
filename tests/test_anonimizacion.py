"""Tests de la utilidad de k-anonimato."""

from __future__ import annotations

from nijar_dti.core.anonimizacion import (
    K_ANONIMATO_MIN,
    cumple_k_anonimato,
    suprimir_k_anonimato,
)


def test_umbral_por_defecto_es_cinco():
    assert K_ANONIMATO_MIN == 5


def test_cumple_k_anonimato():
    assert cumple_k_anonimato(5) is True
    assert cumple_k_anonimato(4) is False
    assert cumple_k_anonimato(0) is False


def test_suprime_celdas_pequenas():
    conteos = {"es": 120, "en": 40, "de": 3, "fr": 6, "it": 1}
    publicables, suprimido = suprimir_k_anonimato(conteos)
    assert publicables == {"es": 120, "en": 40, "fr": 6}
    # de(3) + it(1) suprimidos
    assert suprimido == 4


def test_umbral_personalizado():
    conteos = {"a": 10, "b": 8, "c": 9}
    publicables, suprimido = suprimir_k_anonimato(conteos, k=9)
    assert publicables == {"a": 10, "c": 9}
    assert suprimido == 8


def test_diccionario_vacio():
    publicables, suprimido = suprimir_k_anonimato({})
    assert publicables == {}
    assert suprimido == 0
