"""Tests de validación de los esquemas Pydantic."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from nijar_dti.schemas.chatbot import ChatQueryIn
from nijar_dti.schemas.cms import ContenidoIn
from nijar_dti.schemas.common import GeoPoint, I18nText, PageParams, Paginated
from nijar_dti.schemas.iot import ObservacionIn
from nijar_dti.schemas.tourism import (
    EventoTuristicoIn,
    RecursoTuristicoIn,
    ServicioIn,
)


# -------------------------- Common --------------------------

class TestCommonSchemas:
    def test_geopoint_valido(self):
        p = GeoPoint(coordinates=[-2.139, 36.752])
        assert p.type == "Point"
        assert p.coordinates == [-2.139, 36.752]

    def test_geopoint_invalido_2d(self):
        with pytest.raises(Exception):
            GeoPoint(coordinates=[1, 2, 3])

    def test_page_params_offset(self):
        p = PageParams(page=3, page_size=10)
        assert p.offset == 20
        assert p.limit == 10

    def test_paginated_build(self):
        p = PageParams(page=1, page_size=20)
        result = Paginated[int].build(items=[1, 2, 3], total=42, params=p)
        assert result.items == [1, 2, 3]
        assert result.total == 42
        assert result.page == 1
        assert result.page_size == 20

    def test_i18n_completo(self):
        t = I18nText(es="Hola", en="Hi", de="Hallo", fr="Bonjour")
        assert t.es == "Hola"


# -------------------------- Tourism --------------------------

class TestTourismSchemas:
    def test_recurso_valido(self):
        r = RecursoTuristicoIn(
            urn="urn:ngsi-ld:RecursoTuristico:nijar:playa-monsul",
            nombre="Playa de Mónsul",
            categoria="playa",
        )
        assert r.urn.startswith("urn:ngsi-ld:")
        assert r.municipio == "Níjar"
        assert r.publicado is False

    def test_recurso_urn_invalido(self):
        with pytest.raises(Exception):
            RecursoTuristicoIn(
                urn="not-a-valid-urn",
                nombre="X",
                categoria="playa",
            )

    def test_recurso_categoria_invalida(self):
        with pytest.raises(Exception):
            RecursoTuristicoIn(
                urn="urn:ngsi-ld:RecursoTuristico:nijar:test",
                nombre="X",
                categoria="categoria_inexistente",
            )

    def test_recurso_codigo_postal_invalido(self):
        with pytest.raises(Exception):
            RecursoTuristicoIn(
                urn="urn:ngsi-ld:RecursoTuristico:nijar:test",
                nombre="X",
                categoria="playa",
                codigo_postal="12",  # menos de 5 dígitos
            )

    def test_evento_fecha_fin_anterior_inicio(self):
        with pytest.raises(Exception):
            EventoTuristicoIn(
                urn="urn:ngsi-ld:EventoTuristico:nijar:test",
                nombre="Test",
                tipo="cultural",
                fecha_inicio=datetime(2026, 8, 17, tzinfo=timezone.utc),
                fecha_fin=datetime(2026, 8, 15, tzinfo=timezone.utc),
            )

    def test_evento_valido(self):
        e = EventoTuristicoIn(
            urn="urn:ngsi-ld:EventoTuristico:nijar:fiesta",
            nombre="Fiesta",
            tipo="festivo",
            fecha_inicio=datetime(2026, 8, 15, tzinfo=timezone.utc),
            fecha_fin=datetime(2026, 8, 17, tzinfo=timezone.utc),
        )
        assert e.tipo == "festivo"

    def test_servicio_valoracion_fuera_rango(self):
        with pytest.raises(Exception):
            ServicioIn(
                urn="urn:ngsi-ld:Servicio:nijar:test",
                nombre="X",
                tipo="alojamiento_hotel",
                valoracion_media=6,  # > 5
            )

    def test_servicio_valido(self):
        s = ServicioIn(
            urn="urn:ngsi-ld:Servicio:nijar:hotel-x",
            nombre="Hotel X",
            tipo="alojamiento_hotel",
            valoracion_media=4.5,
        )
        assert s.valoracion_media == 4.5


# -------------------------- IoT --------------------------

class TestIoTSchemas:
    def test_observacion_valida(self):
        o = ObservacionIn(
            sensor_urn="urn:ngsi-ld:Device:nijar:co2:smartoffice-01",
            observado_en=datetime.now(timezone.utc),
            valor=825.5,
            unidades="ppm",
        )
        assert o.valor == 825.5

    def test_observacion_urn_invalido(self):
        with pytest.raises(Exception):
            ObservacionIn(
                sensor_urn="invalid-urn",
                observado_en=datetime.now(timezone.utc),
                valor=825,
            )


# -------------------------- CMS --------------------------

class TestCMSSchemas:
    def test_contenido_valido(self):
        c = ContenidoIn(
            titulo="Apertura de la temporada de baño",
            cuerpo="A partir del 1 de junio...",
            canales=["totem", "web", "app"],
        )
        assert c.canales == ["totem", "web", "app"]
        assert c.publicar is False


# -------------------------- Chatbot --------------------------

class TestChatbotSchemas:
    def test_query_valida(self):
        q = ChatQueryIn(
            sesion_id="sesion-123",
            canal="web",
            idioma="es",
            pregunta="¿Qué playas hay?",
        )
        assert q.canal == "web"
        assert q.idioma == "es"

    def test_query_idioma_invalido(self):
        with pytest.raises(Exception):
            ChatQueryIn(
                sesion_id="s1",
                canal="web",
                idioma="zh",  # no soportado
                pregunta="hola",
            )

    def test_query_canal_invalido(self):
        with pytest.raises(Exception):
            ChatQueryIn(
                sesion_id="s1",
                canal="inexistente",
                pregunta="hola",
            )

    def test_query_pregunta_vacia(self):
        with pytest.raises(Exception):
            ChatQueryIn(
                sesion_id="s1",
                canal="web",
                pregunta="",
            )
