"""Registros de las verticales: detector de cambios, formato y rutas (sin BD)."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from nijar_dti.services import registros_service as rs


class TestNivel:
    def test_tramos(self):
        assert rs.nivel(None) == 0 and rs.nivel(79) == 0
        assert rs.nivel(80) == 80 and rs.nivel(95) == 90
        assert rs.nivel(96, (85, 95)) == 95


def _obs(**over):
    base = {
        "camaras": [SimpleNamespace(codigo="CCTV-01", nombre="Playa", estado="sin_comunicacion")],
        "contenedores": [
            SimpleNamespace(
                codigo="RSU-1",
                fraccion="envases",
                zona_id="sanjose",
                tiene_sensor=True,
                llenado_pct=92,
                estado="operativo",
            ),
            SimpleNamespace(
                codigo="RSU-2",
                fraccion="resto",
                zona_id="nijar",
                tiene_sensor=False,
                llenado_pct=None,
                estado="operativo",
            ),
        ],
        "puntos": [
            SimpleNamespace(
                codigo="MOV-1",
                nombre="Parking Genoveses",
                valor_actual=96,
                capacidad=100,
                unidad="plazas",
            )
        ],
        "sectores": [
            SimpleNamespace(
                codigo="SEC-1",
                nombre="San José",
                fugas_detectadas=2,
                estado="alerta",
                rendimiento_pct=80,
            )
        ],
        "cuadros": [
            SimpleNamespace(
                codigo="CM-001",
                nombre="Glorieta",
                comunicaciones="sin telemetría",
                estado="operativo",
                alarmas=None,
            ),
            SimpleNamespace(
                codigo="CM-002",
                nombre="Puerto",
                comunicaciones="online",
                estado="alerta",
                alarmas=["Fase caída"],
            ),
        ],
    }
    base.update(over)
    return rs.estados_observados(**base)


class TestEstadosObservados:
    def test_estados_y_mensajes(self):
        obs = {(o.vertical, o.codigo): o for o in _obs()}
        cam = obs[("seguridad", "CCTV-01")]
        assert cam.severidad == "critico" and "sin comunicación" in cam.mensaje
        rsu = obs[("residuos", "RSU-1")]
        assert rsu.estado == "llenado:90" and rsu.severidad == "critico"
        assert ("residuos", "RSU-2") not in obs  # sin sensor: no se vigila
        mov = obs[("movilidad", "MOV-1")]
        assert mov.estado == "ocupacion:95" and "96 %" in mov.mensaje
        assert obs[("agua", "SEC-1")].estado == "fuga"
        # el cuadro sin telegestión (inventario WeLight) no se vigila
        assert ("alumbrado", "CM-001") not in obs
        assert "Fase caída" in obs[("alumbrado", "CM-002")].mensaje

    def test_vuelta_a_la_normalidad(self):
        obs = _obs(camaras=[SimpleNamespace(codigo="CCTV-01", nombre="Playa", estado="operativo")])
        cam = next(o for o in obs if o.codigo == "CCTV-01")
        assert cam.severidad == "info" and "vuelve a estar operativo" in cam.mensaje


class TestCsv:
    def test_formato(self):
        r = SimpleNamespace(
            momento=datetime(2026, 11, 3, 10, 0, tzinfo=UTC),
            tipo="alarma",
            severidad="critico",
            activo_codigo="CCTV-01",
            activo_nombre="Playa",
            mensaje="SOS",
            origen="iot",
            demo=False,
        )
        txt = rs.csv_registros([r])  # type: ignore[list-item]
        assert txt.startswith("﻿")
        assert "03/11/2026 11:00:00;alarma;critico;CCTV-01;Playa;SOS;iot;no" in txt


class TestRutas:
    @pytest.mark.parametrize("sufijo", ["registros", "registros/resumen", "registros.csv"])
    def test_requieren_auth(self, client, sufijo):
        assert client.get(f"/api/v1/verticales/seguridad/{sufijo}").status_code == 401

    def test_vertical_desconocida(self, client):
        assert client.get("/api/v1/verticales/inventada/registros").status_code in (401, 404, 422)
