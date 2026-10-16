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


# ------------------------- Vuelos de la Junta de Andalucía -------------------------

CAP_JUNTA = """<WMT_MS_Capabilities><Capability><Request><GetMap>
<Format>image/png</Format><Format>image/jpeg</Format></GetMap></Request>
<Layer><Name>ortofoto_2019</Name><Title>Ortofoto 2019</Title>
  <Layer><Name>distribucion_ortofotos</Name><Title>Distribución de hojas</Title></Layer>
  <Layer><Name>ortofotografia_2019_pancromatico</Name><Title>Pancromático</Title>
    <Style><Name>default</Name><Title>defecto</Title></Style></Layer>
  <Layer><Name>ortofotografia_2019_rgb</Name><Title>Color</Title></Layer>
</Layer></Capability></WMT_MS_Capabilities>"""


def test_elegir_capa_de_la_junta():
    capa, nombres, formato = svc.elegir_capa(CAP_JUNTA, ())
    assert capa == "ortofotografia_2019_rgb"  # hoja, no auxiliar, en color
    assert "distribucion_ortofotos" in nombres and formato == "image/jpeg"
    assert svc.elegir_capa(CAP_JUNTA, ("x", "ortofotografia_2019_pancromatico"))[0] == (
        "ortofotografia_2019_pancromatico"
    )
    solo_png = "<GetMap><Format>image/png</Format></GetMap><Layer><Name>a</Name></Layer>"
    assert svc.elegir_capa(solo_png, ()) == ("a", ["a"], "image/png")


@pytest.fixture
def _sin_cache_junta():
    svc._cache_junta = None
    yield
    svc._cache_junta = None


async def test_junta_solo_servicios_que_responden_con_imagen(monkeypatch, _sin_cache_junta):
    pedidas: list[str] = []

    def manejador(req: httpx.Request) -> httpx.Response:
        url = str(req.url).split("?")[0]
        if req.url.params.get("REQUEST") == "GetCapabilities":
            pedidas.append(url)
            if url.endswith("ortofoto_2019"):
                return httpx.Response(200, text=CAP_JUNTA)
            if url.endswith("ortofoto2013"):
                return httpx.Response(200, text=CAP_JUNTA.replace("2019", "2013"))
            return httpx.Response(404)
        assert req.url.params["SRS"] == "EPSG:3857"
        con_imagen = req.url.params["LAYERS"] == "ortofotografia_2019_rgb"
        cuerpo = b"x" * (9000 if con_imagen else 500)
        return httpx.Response(200, content=cuerpo, headers={"content-type": "image/jpeg"})

    original = httpx.AsyncClient
    monkeypatch.setattr(
        svc.httpx,
        "AsyncClient",
        lambda *a, **kw: original(*a, **{**kw, "transport": httpx.MockTransport(manejador)}),
    )
    vuelos, diags = await svc.listar_ortofotos_junta()
    assert [(v.etiqueta, v.capa, v.organismo) for v in vuelos] == [
        ("2019", "ortofotografia_2019_rgb", "IECA")
    ]
    assert vuelos[0].id == "junta:2019" and vuelos[0].url.endswith("/wms/ortofoto_2019")
    d2013 = next(d for d in diags if d.etiqueta == "2013")
    assert d2013.capa and not d2013.con_imagen  # responde, pero sin imagen sobre Níjar
    # Se prueban las URL alternativas cuando la primera falla (serie renombrada del IECA)
    assert any(u.endswith("ortofoto2016") for u in pedidas)


async def test_junta_desactivable(monkeypatch, _sin_cache_junta):
    monkeypatch.setattr(svc.get_settings(), "ortofotos_junta_activas", False)
    assert await svc.listar_ortofotos_junta() == ([], [])
