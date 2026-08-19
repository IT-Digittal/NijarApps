"""Tests unitarios del parser MQTT."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from nijar_dti.mqtt.parser import MessageParseError, parse_message, parse_topic


class TestParseTopic:
    def test_topic_estandar(self):
        slug, measurement = parse_topic("nijar/sensors/smartoffice-01/co2")
        assert slug == "smartoffice-01"
        assert measurement == "co2"

    def test_topic_con_subniveles(self):
        slug, measurement = parse_topic("nijar/sensors/totem-rodalquilar/meteo/extra")
        assert slug == "totem-rodalquilar"
        assert measurement == "meteo"

    def test_topic_sin_prefijo_nijar(self):
        with pytest.raises(MessageParseError):
            parse_topic("otro/sensors/x/y")

    def test_topic_demasiado_corto(self):
        with pytest.raises(MessageParseError):
            parse_topic("nijar/sensors/x")

    def test_topic_con_wildcard(self):
        with pytest.raises(MessageParseError):
            parse_topic("nijar/sensors/+/co2")


class TestParseMessage:
    def _build_payload(self, **kwargs) -> bytes:
        return json.dumps(kwargs).encode("utf-8")

    def test_payload_valor_unico(self):
        payload = self._build_payload(
            valor=825.5,
            unidades="ppm",
            observado_en="2026-05-15T10:23:45+00:00",
        )
        msg = parse_message("nijar/sensors/smartoffice-01/co2", payload)
        assert msg.sensor_slug == "smartoffice-01"
        assert msg.observacion.valor == 825.5
        assert msg.observacion.unidades == "ppm"
        assert msg.observacion.sensor_urn == "urn:ngsi-ld:Device:nijar:co2:smartoffice-01"

    def test_payload_valores_multiples(self):
        payload = self._build_payload(
            valores={"temperatura_c": 24.5, "humedad_porc": 62},
            observado_en=1747299425,
        )
        msg = parse_message("nijar/sensors/totem-rodalquilar/meteo", payload)
        assert msg.observacion.valor is None
        assert msg.observacion.valores == {"temperatura_c": 24.5, "humedad_porc": 62}

    def test_timestamp_epoch_milisegundos(self):
        payload = self._build_payload(valor=10, observado_en=1747299425000)
        msg = parse_message("nijar/sensors/x/y", payload)
        # debe aceptarlo y convertir a segundos
        assert msg.observacion.observado_en.year == 2025

    def test_timestamp_iso_con_z(self):
        payload = self._build_payload(valor=10, observado_en="2026-05-15T10:23:45Z")
        msg = parse_message("nijar/sensors/x/y", payload)
        assert msg.observacion.observado_en.tzinfo is not None

    def test_timestamp_omitido_usa_now(self):
        payload = self._build_payload(valor=10)
        antes = datetime.now(UTC)
        msg = parse_message("nijar/sensors/x/y", payload)
        despues = datetime.now(UTC)
        assert antes <= msg.observacion.observado_en <= despues

    def test_payload_no_json(self):
        with pytest.raises(MessageParseError, match="JSON"):
            parse_message("nijar/sensors/x/y", b"no-es-json")

    def test_payload_lista_no_objeto(self):
        with pytest.raises(MessageParseError, match="objeto"):
            parse_message("nijar/sensors/x/y", b"[1, 2, 3]")

    def test_payload_no_utf8(self):
        with pytest.raises(MessageParseError):
            parse_message("nijar/sensors/x/y", b"\xff\xfe\x00\x00")

    def test_payload_sin_valor_ni_valores(self):
        payload = self._build_payload(unidades="ppm")
        with pytest.raises(MessageParseError, match="valor"):
            parse_message("nijar/sensors/x/y", payload)

    def test_payload_valor_no_numerico(self):
        payload = self._build_payload(valor="no-es-numero")
        with pytest.raises(MessageParseError, match="float"):
            parse_message("nijar/sensors/x/y", payload)

    def test_payload_valores_no_objeto(self):
        payload = self._build_payload(valores=[1, 2, 3])
        with pytest.raises(MessageParseError, match="valores"):
            parse_message("nijar/sensors/x/y", payload)

    def test_sensor_urn_explicito_tiene_prioridad(self):
        payload = self._build_payload(
            sensor_urn="urn:ngsi-ld:Device:nijar:co2:custom-id",
            valor=100,
        )
        msg = parse_message("nijar/sensors/topic-slug/co2", payload)
        assert msg.observacion.sensor_urn == "urn:ngsi-ld:Device:nijar:co2:custom-id"
