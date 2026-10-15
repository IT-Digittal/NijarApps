"""Tests del conector de noticias del Ayuntamiento (Strapi), parseo sin red.

El fixture reproduce la forma real de un artículo de
``GET /api/articles`` de ``api.nijaraldia.es`` (Strapi 5).
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from nijar_dti.config import Settings
from nijar_dti.connectors.noticias import ClienteNoticiasStrapi
from nijar_dti.schemas.noticias import NoticiaOut
from nijar_dti.services.noticias_service import estado_noticias, noticias_configurado

BASE = "https://api.nijaraldia.es"


def _articulo() -> dict:
    return {
        "id": 1780,
        "documentId": "olmngz7bjhng942rbwkkunmd",
        "title": "Título de prueba",
        "description": "Entradilla de prueba",
        "slug": "titulo-de-prueba",
        "content": "<p>Cuerpo de la noticia</p>",
        "date": "2026-08-18",
        "publishedAt": "2026-08-18T11:30:17.078Z",
        "cover": {
            "url": "/uploads/PLENO_1_cc1990cc58.webp",
            "formats": {
                "medium": {"url": "/uploads/medium_PLENO_1_cc1990cc58.webp"},
                "thumbnail": {"url": "/uploads/thumbnail_PLENO_1_cc1990cc58.webp"},
            },
        },
        "categories": [
            {"documentId": "ryio", "name": "Níjar Informa", "slug": "nijar-informa"},
            {"documentId": "lj6b", "name": "Turismo", "slug": "turismo"},
        ],
    }


def _cliente() -> ClienteNoticiasStrapi:
    return ClienteNoticiasStrapi(BASE, "bs261ckcuumnj68xcjncw7rf")


def test_parseo_campos_basicos():
    n = _cliente()._parsear(_articulo(), con_contenido=False)
    assert n["id"] == 1780
    assert n["document_id"] == "olmngz7bjhng942rbwkkunmd"
    assert n["titulo"] == "Título de prueba"
    assert n["descripcion"] == "Entradilla de prueba"
    assert n["slug"] == "titulo-de-prueba"
    assert n["categorias"] == ["Níjar Informa", "Turismo"]


def test_imagen_se_hace_absoluta_y_prefiere_medium():
    n = _cliente()._parsear(_articulo(), con_contenido=False)
    assert n["imagen_url"] == f"{BASE}/uploads/medium_PLENO_1_cc1990cc58.webp"


def test_imagen_absoluta_no_se_altera():
    art = _articulo()
    art["cover"] = {"url": "https://cdn.example.com/x.webp", "formats": {}}
    n = _cliente()._parsear(art, con_contenido=False)
    assert n["imagen_url"] == "https://cdn.example.com/x.webp"


def test_sin_cover_imagen_none():
    art = _articulo()
    art["cover"] = None
    n = _cliente()._parsear(art, con_contenido=False)
    assert n["imagen_url"] is None


def test_contenido_solo_con_flag():
    c = _cliente()
    assert c._parsear(_articulo(), con_contenido=False)["contenido"] is None
    assert c._parsear(_articulo(), con_contenido=True)["contenido"] == "<p>Cuerpo de la noticia</p>"


def test_schema_coacciona_fechas():
    n = NoticiaOut(**_cliente()._parsear(_articulo(), con_contenido=True))
    assert isinstance(n.fecha, date) and n.fecha == date(2026, 8, 18)
    assert isinstance(n.publicado_en, datetime)


def test_estado_y_configurado():
    s = Settings(
        secret_key="x" * 32,
        app_env="development",
        database_url="postgresql+asyncpg://u:p@localhost/db",
    )
    assert noticias_configurado(s) is True
    est = estado_noticias(s)
    assert est.configurado is True
    assert est.base_url.startswith("https://")


def test_no_configurado_si_falta_base_url():
    c = ClienteNoticiasStrapi("", "pid")
    assert c.is_configured is False


async def test_turismo_sirve_ultimo_listado_si_strapi_falla(monkeypatch):
    from nijar_dti.connectors.noticias import NoticiasError
    from nijar_dti.schemas.noticias import NoticiasPageOut
    from nijar_dti.services import noticias_service as svc

    bueno = NoticiasPageOut(page=1, page_size=3, page_count=1, total=0, items=[])

    async def ok(**_kw):
        return bueno

    async def falla(**_kw):
        raise NoticiasError("timeout")

    svc._ultimo_listado.clear()
    monkeypatch.setattr(svc, "listar_noticias", falla)
    with pytest.raises(NoticiasError):
        await svc.listar_turismo(page=1, page_size=3)

    monkeypatch.setattr(svc, "listar_noticias", ok)
    assert await svc.listar_turismo(page=1, page_size=3) is bueno
    monkeypatch.setattr(svc, "listar_noticias", falla)
    assert await svc.listar_turismo(page=1, page_size=3) is bueno
    svc._ultimo_listado.clear()


async def test_listar_por_slug_de_categoria(monkeypatch):
    cli = ClienteNoticiasStrapi(base_url="https://x", project_id="p")
    capturado: dict = {}

    async def fake_get(ruta, params):
        capturado["params"] = params
        return {"data": [], "meta": {"pagination": {"page": 1, "pageSize": 5, "total": 0}}}

    monkeypatch.setattr(cli, "_get", fake_get)
    await cli.listar(page_size=5, categoria_slug="cultura")
    assert ("filters[categories][slug][$eqi]", "cultura") in capturado["params"]


async def test_agenda_usa_categoria_cultura(monkeypatch):
    from nijar_dti.schemas.noticias import NoticiasPageOut
    from nijar_dti.services import noticias_service as svc

    llamadas: list[dict] = []

    async def fake(**kw):
        llamadas.append(kw)
        return NoticiasPageOut(page=1, page_size=6, page_count=0, total=0, items=[])

    svc._ultimo_listado.clear()
    monkeypatch.setattr(svc, "listar_noticias", fake)
    await svc.listar_agenda(page_size=6)
    assert llamadas[0]["categoria_slug"] == "cultura"
    svc._ultimo_listado.clear()


async def test_listado_general_sin_categoria(monkeypatch):
    from nijar_dti.schemas.noticias import NoticiasPageOut
    from nijar_dti.services import noticias_service as svc

    llamadas: list[dict] = []

    async def fake(**kw):
        llamadas.append(kw)
        return NoticiasPageOut(page=1, page_size=12, page_count=0, total=0, items=[])

    svc._ultimo_listado.clear()
    monkeypatch.setattr(svc, "listar_noticias", fake)
    await svc.listar_todas(page_size=12)
    assert llamadas[0]["categoria_document_id"] is None
    assert llamadas[0]["categoria_slug"] is None
    svc._ultimo_listado.clear()
