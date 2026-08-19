"""Tests de la lógica pura de ANS y disponibilidad (informe mensual C.1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from nijar_dti.core.ans import (
    SLA_ANS,
    disponibilidad_porcentaje,
    evalua_ans,
    horas_entre,
)
from nijar_dti.services.incidencias_service import (
    calcular_disponibilidad,
    resumen_incidencias,
)

UTC = UTC


def test_horas_entre():
    a = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
    b = datetime(2026, 6, 1, 14, 30, tzinfo=UTC)
    assert horas_entre(a, b) == 4.5
    assert horas_entre(a, None) is None


class TestEvaluaANS:
    def test_critica_cumple(self):
        det = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
        ev = evalua_ans("critica", det, det + timedelta(minutes=30), det + timedelta(hours=6))
        # respuesta 0.5h <= 1h, resolución 6h <= 8h
        assert ev.cumple_respuesta is True
        assert ev.cumple_resolucion is True
        assert ev.cumple is True

    def test_critica_incumple_resolucion(self):
        det = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
        ev = evalua_ans("critica", det, det + timedelta(minutes=30), det + timedelta(hours=12))
        assert ev.cumple_resolucion is False
        assert ev.cumple is False

    def test_sin_resolver(self):
        det = datetime(2026, 6, 1, 10, 0, tzinfo=UTC)
        ev = evalua_ans("alta", det, None, None)
        assert ev.cumple_resolucion is None
        assert ev.cumple is None

    def test_matriz_definida(self):
        assert set(SLA_ANS) == {"critica", "alta", "media", "baja"}


class TestDisponibilidad:
    def test_sin_downtime_es_100(self):
        assert disponibilidad_porcentaje(0, 43_200) == 100.0

    def test_downtime_parcial(self):
        # 432 min de caída sobre 43200 (mes) = 1% -> 99%
        assert disponibilidad_porcentaje(432, 43_200) == 99.0

    def test_acotado_a_cero(self):
        assert disponibilidad_porcentaje(100_000, 43_200) == 0.0

    def test_periodo_cero(self):
        assert disponibilidad_porcentaje(10, 0) == 100.0


@dataclass
class _IncFake:
    severidad: str
    componente: str
    detectada_en: datetime
    resuelta_en: datetime | None = None
    afecta_disponibilidad: bool = False
    es_preventiva: bool = False
    es_evento_seguridad: bool = False
    incidente_confirmado: bool = False


def test_calcular_disponibilidad_descuenta_downtime():
    inicio = datetime(2026, 6, 1, tzinfo=UTC)
    fin = datetime(2026, 7, 1, tzinfo=UTC)
    incs = [
        _IncFake(
            "critica",
            "chatbot",
            datetime(2026, 6, 10, 10, 0, tzinfo=UTC),
            datetime(2026, 6, 10, 16, 0, tzinfo=UTC),
            afecta_disponibilidad=True,
        ),
    ]
    disp = calcular_disponibilidad(incs, inicio, fin)
    assert disp["chatbot"] < 100.0
    # un componente sin incidencias permanece al 100 %
    assert disp["plataforma"] == 100.0


def test_resumen_incidencias_cuenta_por_tipo():
    det = datetime(2026, 6, 5, tzinfo=UTC)
    incs = [
        _IncFake(
            "critica", "plataforma", det, det, es_evento_seguridad=True, incidente_confirmado=True
        ),
        _IncFake("alta", "totem_1", det, det),
        _IncFake("baja", "smart_office", det, None, es_preventiva=True),
    ]
    r = resumen_incidencias(incs)
    assert r["criticas"] == 1
    assert r["altas"] == 1
    assert r["resueltas"] == 2  # critica y alta resueltas; la preventiva no cuenta
    assert r["eventos_seguridad"] == 1
    assert r["incidentes_confirmados"] == 1
    assert r["preventivas"] == 1
