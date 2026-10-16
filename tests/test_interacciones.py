"""Tests de los listados de interacciones (chatbot y tótem) sin BBDD."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from nijar_dti.main import app
from nijar_dti.schemas.interacciones import EventosTotemIn
from nijar_dti.services import interacciones_service as svc


def test_totem_de_sesion():
    assert svc.totem_de_sesion("totem-urn:ngsi-ld:Totem:nijar:albaricoques-1760600000000") == (
        "albaricoques"
    )
    assert svc.totem_de_sesion("totem-urn:ngsi-ld:Totem:nijar:rodalquilar-1") == "rodalquilar"
    assert svc.totem_de_sesion("demo-session-001") is None
    assert svc.totem_de_sesion(None) is None


def test_busqueda_escapa_comodines_y_hasta_incluye_el_dia():
    assert svc._like("50%_x") == "%50\\%\\_x%"
    fin = svc._hasta_inclusivo(datetime(2026, 10, 16))
    assert fin is not None and (fin.day, fin.hour, fin.minute) == (16, 23, 59)
    con_hora = datetime(2026, 10, 16, 10, 30)
    assert svc._hasta_inclusivo(con_hora) == con_hora


def test_atributos_solo_con_claves_conocidas():
    assert "atributos ->> 'evento'" in str(svc._attr("evento"))
    with pytest.raises(ValueError):
        svc._attr("evento'; drop table visitas; --")


def test_esquema_eventos_totem():
    lote = EventosTotemIn(
        totem="albaricoques",
        sesion_id="totem-urn:ngsi-ld:Totem:nijar:albaricoques-1",
        eventos=[{"evento": "ficha", "seccion": "playas", "contenido": "Playa de Mónsul"}],
    )
    assert lote.idioma == "es" and lote.eventos[0].contenido == "Playa de Mónsul"
    for malo in (
        {"totem": "Tótem 1", "sesion_id": "abcd", "eventos": [{"evento": "ficha"}]},
        {"totem": "x", "sesion_id": "abcd", "eventos": []},
        {"totem": "x", "sesion_id": "abcd", "eventos": [{"evento": "Ficha!"}]},
        {"totem": "x", "sesion_id": "abcd", "eventos": [{"evento": "ficha"}] * 51},
    ):
        with pytest.raises(ValidationError):
            EventosTotemIn(**malo)


@pytest.mark.parametrize(
    "ruta",
    [
        "/api/v1/chatbot/interacciones",
        "/api/v1/chatbot/interacciones/export",
        "/api/v1/chatbot/interacciones/sesion/x",
        "/api/v1/dashboards/totems/interacciones",
        "/api/v1/dashboards/totems/interacciones/export",
        "/api/v1/dashboards/totems/interacciones/sesion/x",
    ],
)
def test_listados_exigen_sesion(ruta: str):
    assert TestClient(app).get(ruta).status_code == 401


def test_eventos_totem_valida_el_lote():
    r = TestClient(app).post(
        "/api/v1/dashboards/totems/eventos", json={"totem": "x y", "sesion_id": "s", "eventos": []}
    )
    assert r.status_code == 422
