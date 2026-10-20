"""Tests de la traducción automática de contenidos del tótem (sin BBDD ni OpenAI)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from nijar_dti.schemas.cms import AvisoPublicoOut
from nijar_dti.schemas.common import I18nText
from nijar_dti.schemas.noticias import NoticiaOut
from nijar_dti.services import traduccion_service as svc


@pytest.fixture
def traductor_falso(monkeypatch):
    """Sustituye ``traducir`` por uno que marca el texto con el idioma."""
    llamadas: list[list[str | None]] = []

    async def falso(db, textos, idioma, **_):
        llamadas.append(list(textos))
        return [f"[{idioma}] {t}" if t else t for t in textos]

    monkeypatch.setattr(svc, "traducir", falso)
    return llamadas


def test_lotes_respetan_el_tamano_maximo():
    textos = ["a" * 4000, "b" * 4000, "c" * 100]
    lotes = svc._lotes(textos)
    assert lotes == [["a" * 4000], ["b" * 4000, "c" * 100]]


def test_clave_depende_del_idioma_y_del_texto():
    assert svc._clave("en", "Hola") != svc._clave("de", "Hola")
    assert svc._clave("en", "Hola") == svc._clave("en", "Hola")
    assert len(svc._clave("en", "Hola")) == 64


async def test_espanol_no_se_traduce(traductor_falso):
    aviso = AvisoPublicoOut(id=uuid4(), titulo="Corte de agua", cuerpo="Mañana")
    assert await svc.traducir_avisos(None, [aviso], "es") == [aviso]  # type: ignore[arg-type]
    assert traductor_falso == []


async def test_avisos_rellenan_el_idioma_que_falta(traductor_falso):
    con_en = AvisoPublicoOut(
        id=uuid4(),
        titulo="Feria",
        titulo_i18n=I18nText(es="Feria", en="Fair"),
        cuerpo="Texto",
    )
    sin_nada = AvisoPublicoOut(id=uuid4(), titulo="Corte de agua", cuerpo="Mañana de 9 a 12")
    out = await svc.traducir_avisos(None, [con_en, sin_nada], "en")  # type: ignore[arg-type]
    # La traducción manual del CMS manda: no se vuelve a traducir
    assert out[0].titulo_i18n.en == "Fair"
    assert out[0].cuerpo_i18n.en == "[en] Texto"
    assert out[1].titulo_i18n.en == "[en] Corte de agua"
    assert out[1].titulo_i18n.es == "Corte de agua"
    assert out[1].cuerpo_i18n.en == "[en] Mañana de 9 a 12"
    assert traductor_falso[0] == [None, "Texto", "Corte de agua", "Mañana de 9 a 12"]


async def test_noticias_devuelven_copias(traductor_falso):
    original = NoticiaOut(
        document_id="d1",
        titulo="Nueva ruta",
        descripcion="Resumen",
        slug="nueva-ruta",
        contenido="<p>Texto</p>",
        publicado_en=datetime.now(UTC),
    )
    [tr] = await svc.traducir_noticias(None, [original], "fr")  # type: ignore[arg-type]
    assert tr.titulo == "[fr] Nueva ruta"
    assert tr.contenido == "[fr] <p>Texto</p>"
    # El listado en memoria del servicio de noticias no se modifica
    assert original.titulo == "Nueva ruta"


async def test_sin_clave_devuelve_el_original(monkeypatch):
    class Sesion:
        async def execute(self, *_a, **_k):
            class R:
                def all(self):
                    return []

            return R()

    ajustes = type("S", (), {"openai_api_key": "", "openai_model": "x"})()
    out = await svc.traducir(Sesion(), ["Hola", None], "en", settings=ajustes)  # type: ignore[arg-type]
    assert out == ["Hola", None]
