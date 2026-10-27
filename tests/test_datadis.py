"""Tests del conector y la carga de Datadis (consumo eléctrico), sin red."""

from __future__ import annotations

from datetime import UTC, date, datetime

import httpx
import pytest

from nijar_dti.connectors import datadis as dd
from nijar_dti.services import datadis_service as svc

FILA_PUBLICA = {
    "community": "Andalucía",
    "province": "Almería",
    "municipality": "NÍJAR",
    "date": "2026/07/15",
    "economicSector": "RESIDENCIAL",
    "tension": "Baja tensión",
    "sumContracts": "14.597",
    "sumEnergy": 191589,
}


@pytest.fixture(autouse=True)
def _sin_esperas(monkeypatch):
    async def nada(_s: float) -> None:
        return None

    monkeypatch.setattr(dd, "_esperar", nada)


def _cliente(manejador, **kw) -> dd.ClienteDatadis:
    return dd.ClienteDatadis(
        cliente_http=httpx.AsyncClient(transport=httpx.MockTransport(manejador)), **kw
    )


# ------------------------------------------------------------- parseo ----


def test_registro_publico_con_formato_espanol():
    r = dd.parsear_registro_publico(FILA_PUBLICA)
    assert r is not None
    assert r.fecha == date(2026, 7, 15)
    assert r.contratos == 14597 and r.energia_kwh == 191589.0
    assert r.sector == "RESIDENCIAL" and r.municipio == "NÍJAR"


def test_registro_publico_nombres_alternativos_y_basura():
    alt = {"fecha": "2026-07-16", "sector": "INDUSTRIA", "contracts": 406, "energy": "24.914,5"}
    r = dd.parsear_registro_publico(alt)
    assert r and r.energia_kwh == 24914.5 and r.tension == "—"
    assert dd.parsear_registro_publico({"foo": 1}) is None


def test_filas_envueltas():
    assert dd.filas_de_respuesta([FILA_PUBLICA]) == [FILA_PUBLICA]
    assert dd.filas_de_respuesta({"content": [FILA_PUBLICA], "totalPages": 1}) == [FILA_PUBLICA]
    assert dd.filas_de_respuesta({"data": {"items": [FILA_PUBLICA]}}) == [FILA_PUBLICA]


def test_suministros_curva_y_potencia_v2():
    sums = dd.parsear_suministros({
        "supplies": [{"cups": "es0031xx", "address": "AYUNTAMIENTO", "distributorCode": "2",
                      "pointType": 5, "distributor": "E-DISTRIBUCIÓN"}],
        "distributorError": [],
    })  # fmt: skip
    assert sums[0].cups == "ES0031XX" and sums[0].tipo_punto == 5
    curva = dd.parsear_curva({"timeCurve": [
        {"cups": "ES0031XX", "date": "2026/10/01", "time": "01:00", "consumptionKWh": 1.25,
         "obtainMethod": "Real", "selfConsumptionEnergyKWh": 0.0},
        {"cups": "ES0031XX", "date": "2026/10/01", "time": "24:00", "consumptionKWh": 0.5},
    ]})  # fmt: skip
    assert [(c.hora, c.consumo_kwh) for c in curva] == [(1, 1.25), (24, 0.5)]
    assert dd.potencia_contratada({"contract": [{"contractedPowerkW": [10.39, 15.0]}]}) == 15.0


def test_normalizar_municipio():
    assert dd.normalizar("  Níjar ") == "NIJAR"
    reg = dd.parsear_registro_publico({**FILA_PUBLICA, "municipality": "ALMERÍA"})
    assert reg is not None and not svc.es_del_municipio(reg, "Níjar")


# ------------------------------------------------------- autenticación ----


async def test_publico_sin_credenciales_funciona():
    vistas: list[httpx.Request] = []

    def manejador(req: httpx.Request) -> httpx.Response:
        vistas.append(req)
        return httpx.Response(200, json=[FILA_PUBLICA])

    async with _cliente(manejador) as cli:
        filas, _ = await cli.buscar_publico(
            date(2026, 7, 15), date(2026, 7, 25), {"community": "01"}
        )
    assert filas == [FILA_PUBLICA]
    assert "authorization" not in vistas[0].headers
    assert vistas[0].url.params["startDate"] == "2026/07/15"


async def test_publico_exige_login_sin_credenciales_da_error_claro():
    async with _cliente(lambda req: httpx.Response(401)) as cli:
        with pytest.raises(dd.DatadisAutenticacionError):
            await cli.buscar_publico(date(2026, 7, 1), date(2026, 7, 2), {})


async def test_publico_exige_login_con_credenciales_reintenta_con_token():
    def manejador(req: httpx.Request) -> httpx.Response:
        if req.url.path == dd.URL_LOGIN:
            assert b"username=B04000000" in req.content
            return httpx.Response(200, text="token-jwt")
        if req.headers.get("authorization") != "Bearer token-jwt":
            return httpx.Response(403)
        return httpx.Response(200, json={"content": [FILA_PUBLICA]})

    async with _cliente(manejador, usuario="B04000000", password="x") as cli:
        filas, _ = await cli.buscar_publico(date(2026, 7, 1), date(2026, 7, 2), {})
    assert len(filas) == 1


async def test_privado_con_nif_autorizado_y_reintento_429():
    llamadas = {"supplies": 0}

    def manejador(req: httpx.Request) -> httpx.Response:
        if req.url.path == dd.URL_LOGIN:
            return httpx.Response(200, text='"tok"')
        llamadas["supplies"] += 1
        if llamadas["supplies"] == 1:
            return httpx.Response(429, headers={"retry-after": "1"})
        assert req.url.params["authorizedNif"] == "P0406600J"
        return httpx.Response(200, json={"supplies": [{"cups": "ES1", "distributorCode": "2"}]})

    async with _cliente(manejador, usuario="u", password="p", nif_autorizado="P0406600J") as cli:
        sums = await cli.suministros()
    assert [s.cups for s in sums] == ["ES1"]


# ------------------------------------------------------------ utilidades ----


def test_tramos_mensuales_respetan_el_mes():
    assert svc.tramos_mensuales(date(2026, 1, 20), date(2026, 3, 5)) == [
        (date(2026, 1, 20), date(2026, 1, 31)),
        (date(2026, 2, 1), date(2026, 2, 28)),
        (date(2026, 3, 1), date(2026, 3, 5)),
    ]


def test_momento_utc_hora_de_fin_y_horario_de_verano():
    lec = dd.LecturaHoraria("ES1", date(2026, 7, 15), 1, 1.0, None, None, None)
    assert svc.momento_utc(lec) == datetime(2026, 7, 14, 22, 0, tzinfo=UTC)  # 00:00 CEST
    lec = dd.LecturaHoraria("ES1", date(2026, 1, 15), 24, 1.0, None, None, None)
    assert svc.momento_utc(lec) == datetime(2026, 1, 15, 22, 0, tzinfo=UTC)  # 23:00 CET


def test_ventana_por_defecto():
    assert svc.ventana_por_defecto(date(2026, 10, 15)) == (
        date(2026, 10, 1), date(2026, 10, 14), "2026/10", "2026/10",
    )  # fmt: skip
    assert svc.ventana_por_defecto(date(2026, 10, 3)) == (
        date(2026, 9, 1), date(2026, 10, 2), "2026/09", "2026/10",
    )  # fmt: skip


def test_suministros_duplicados_en_la_autorizacion_se_cuentan_una_vez():
    fila = {"cups": "ES0031000000000001AB", "address": "CL REAL 1", "distributorCode": "2"}
    sums = dd.parsear_suministros(
        {"supplies": [fila, dict(fila), {**fila, "cups": "es0031000000000002ab"}]}
    )
    assert [s.cups for s in sums] == ["ES0031000000000001AB", "ES0031000000000002AB"]
