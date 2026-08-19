"""Tests del conector de noticias del Ayuntamiento (Strapi), parseo sin red.

El fixture reproduce la forma real de un artículo de
``GET /api/articles`` de ``api.nijaraldia.es`` (Strapi 5).
"""

from __future__ import annotations

from datetime import date, datetime

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
