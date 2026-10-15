"""Tests de las ortofotos históricas del gemelo (PNOA histórico del IGN), sin red."""

from __future__ import annotations

import httpx
import pytest

from nijar_dti.services import ortofotos_service as svc

CAPABILITIES = """<?xml version="1.0"?>
<WMT_MS_Capabilities><Capability><Layer><Title>PNOA histórico</Title>
  <Layer><Name>AMS_1956-1957</Name><Title>Vuelo Americano Serie B 1956-1957</Title></Layer>
  <Layer><Name>PNOA2010</Name><Title>PNOA 2010</Title></Layer>
  <Layer><Name>PNOA2004</Name><Title>PNOA 2004</Title></Layer>
  <Layer><Name>Interministerial_1973-1986</Name><Title>Interministerial</Title></Layer>
  <Layer><Name>Mosaico</Name><Title>Sin fecha</Title></Layer>
</Layer></Capability></WMT_MS_Capabilities>"""


def test_parseo_ordena_y_etiqueta():
    capas = svc.parsear_capacidades(CAPABILITIES)
    assert [c.etiqueta for c in capas] == ["1956-57", "1973-86", "2004", "2010"]
    assert capas[0].nombre == "AMS_1956-1957"
    assert all(c.nombre != "Mosaico" for c in capas)


def _cliente_falso(con_imagen: set[str]):
    def manejador(req: httpx.Request) -> httpx.Response:
        if req.url.params.get("REQUEST") == "GetCapabilities":
            return httpx.Response(200, text=CAPABILITIES)
        capa = req.url.params["LAYERS"]
        cuerpo = b"x" * (8000 if capa in con_imagen else 600)
        return httpx.Response(200, content=cuerpo, headers={"content-type": "image/jpeg"})

    original = httpx.AsyncClient

    def fabrica(*a, **kw):
        kw["transport"] = httpx.MockTransport(manejador)
        return original(*a, **kw)

    return fabrica


@pytest.fixture(autouse=True)
def _sin_cache():
    svc._cache = None
    yield
    svc._cache = None


async def test_solo_vuelos_con_imagen_en_nijar(monkeypatch):
    monkeypatch.setattr(svc.httpx, "AsyncClient", _cliente_falso({"AMS_1956-1957", "PNOA2010"}))
    url, capas, verificada = await svc.listar_ortofotos()
    assert url.endswith("pnoa-historico")
    assert verificada is True
    assert [c.nombre for c in capas] == ["AMS_1956-1957", "PNOA2010"]


async def test_sin_cobertura_detectada_devuelve_todo(monkeypatch):
    monkeypatch.setattr(svc.httpx, "AsyncClient", _cliente_falso(set()))
    _, capas, verificada = await svc.listar_ortofotos()
    assert verificada is False
    assert len(capas) == 4
