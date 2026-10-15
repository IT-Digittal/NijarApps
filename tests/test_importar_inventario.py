"""Tests del importador del Inventario Municipal de Bienes (sin BBDD)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from nijar_dti.data import importar_inventario as inv
from nijar_dti.models.geografia import GrupoCapa

RAIZ = Path(__file__).resolve().parents[1]


def test_todas_las_categorias_del_convertidor_tienen_estilo():
    js = (RAIZ / "frontend/dashboard/assets/dwg2geojson.mjs").read_text(encoding="utf-8")
    bloque = js.split("export const CATEGORIAS = {")[1].split("};")[0]
    categorias = set(re.findall(r"^\s+(\w+):", bloque, re.MULTILINE))
    assert categorias and categorias <= set(inv.CATEGORIAS)


def test_nombre_y_ficha():
    props = {
        "nucleo": "El Viso",
        "categoria": "red_viaria",
        "codigos": ["V-VI-7"],
        "notas": ["Puesta a disposición 74,57m²"],
        "superficie_m2": 14262,
        "capa_dwg": "invent-viales-trama",
        "origen": "sombreado",
    }
    assert inv.nombre_elemento(props) == "V-VI-7"
    assert inv.nombre_elemento({**props, "codigos": []}) == "Red viaria · El Viso"
    ficha = inv.propiedades_ficha(props)
    assert ficha["categoría"] == "Red viaria" and ficha["códigos"] == "V-VI-7"
    assert ficha["_nucleo"] == "El Viso"  # clave de reimportación
    assert "notas" in ficha and ficha["superficie_m2"] == 14262
    assert "notas" not in inv.propiedades_ficha({**props, "notas": []})


def test_grupo_y_codigo_de_capa():
    assert GrupoCapa("inventario") is GrupoCapa.INVENTARIO
    assert inv.codigo_capa("equipamiento") == "inventario_equipamiento"


def test_leer_colecciones(tmp_path: Path):
    bueno = {"type": "FeatureCollection", "nucleo": "Pueblo Blanco", "features": []}
    (tmp_path / "pueblo-blanco.geojson").write_text(json.dumps(bueno), encoding="utf-8")
    assert [c["nucleo"] for c in inv.leer_colecciones([str(tmp_path)])] == ["Pueblo Blanco"]
    malo = tmp_path / "otro.geojson"
    malo.write_text(json.dumps({"type": "FeatureCollection", "features": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="nucleo"):
        inv.leer_colecciones([str(malo)])
    (tmp_path / "vacia").mkdir()
    with pytest.raises(ValueError, match="ningún"):
        inv.leer_colecciones([str(tmp_path / "vacia")])


def test_dentro_de_nijar_y_centro_utm():
    assert inv.dentro_de_nijar(36.9123, -2.1322)  # Pueblo Blanco
    assert inv.dentro_de_nijar(36.7600, -2.1100)  # San José
    assert not inv.dentro_de_nijar(36.6796, -2.2159)  # mar, al sur del Cabo de Gata
    assert inv._punto_utm({"centro_utm": [577300, 4085500]}) == (577300.0, 4085500.0)
    fc = {"features": [{"geometry": {"type": "Polygon", "coordinates": [[[1.0, 2.0], [3, 4]]]}}]}
    assert inv._punto_utm(fc) == (1.0, 2.0)


def test_validar_coleccion_del_panel():
    fc = {"type": "FeatureCollection", "nucleo": "Las Negras", "features": []}
    assert inv.validar_coleccion(fc) is fc
    for malo in (
        [],
        {"type": "FeatureCollection", "nucleo": " ", "features": []},
        {"type": "FeatureCollection", "nucleo": "X"},
        {"type": "Feature", "nucleo": "X", "features": []},
    ):
        with pytest.raises(ValueError, match="Colección 2"):
            inv.validar_coleccion(malo, "Colección 2")


def test_esquema_importar_inventario():
    from pydantic import ValidationError

    from nijar_dti.schemas.geografia import InventarioImportarIn

    datos = InventarioImportarIn(colecciones=[{"nucleo": "X"}])
    assert datos.dry_run is True and datos.srid == 25830 and datos.incluir_fuera is False
    assert InventarioImportarIn(colecciones=[{}], srid=23030).srid == 23030
    with pytest.raises(ValidationError):
        InventarioImportarIn(colecciones=[{}], srid=4326)  # no es UTM
    with pytest.raises(ValidationError):
        InventarioImportarIn(colecciones=[])


def test_endpoint_importar_inventario_exige_sesion():
    from fastapi.testclient import TestClient

    from nijar_dti.main import app

    r = TestClient(app).post("/api/v1/geo/inventario/importar", json={"colecciones": [{}]})
    assert r.status_code == 401
