"""Tests del informe mensual PDF por anunciante."""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from nijar_dti.services.informe_publicidad import agregar_semanas, render_pdf


def test_agregar_semanas_cubre_el_mes_completo():
    filas = [
        (date(2026, 7, 3), 10, 1),
        (date(2026, 7, 5), 5, 0),
        (date(2026, 7, 10), 7, 2),
        (date(2026, 7, 31), 4, 1),
    ]
    semanas = agregar_semanas(filas, 2026, 7)
    assert [s["etiqueta"] for s in semanas] == ["1-7", "8-14", "15-21", "22-28", "29-31"]
    assert semanas[0] == {"etiqueta": "1-7", "impresiones": 15, "toques": 1}
    assert semanas[1]["impresiones"] == 7 and semanas[1]["toques"] == 2
    assert semanas[2]["impresiones"] == 0  # semana sin datos: aparece a cero
    assert semanas[4]["impresiones"] == 4


def test_agregar_semanas_febrero_sin_datos():
    semanas = agregar_semanas([], 2026, 2)
    assert [s["etiqueta"] for s in semanas] == ["1-7", "8-14", "15-21", "22-28"]
    assert all(s["impresiones"] == 0 and s["toques"] == 0 for s in semanas)


def test_render_pdf_genera_documento():
    empresa = SimpleNamespace(
        nombre="Restaurante La Ola",
        sector="gastronomia",
        nucleo="San José",
        direccion="Paseo Marítimo, 12",
    )
    datos = {
        "empresa": empresa,
        "anio": 2026,
        "mes": 7,
        "semanas": agregar_semanas([(date(2026, 7, 3), 120, 9)], 2026, 7),
        "total_impresiones": 120,
        "total_toques": 9,
        "dias_con_datos": 1,
    }
    pdf = render_pdf(datos)
    assert pdf.startswith(b"%PDF"), "no es un PDF"
    assert len(pdf) > 1500, "PDF sospechosamente vacío"


class TestRutaApi:
    def test_informe_en_openapi_con_roles(self, client):
        rutas = client.get("/openapi.json").json()["paths"]
        ruta = rutas.get("/api/v1/publicidad/{empresa_id}/informe")
        assert ruta is not None
        assert ruta["get"].get("security"), "el informe de facturación exige rol de gestión"
