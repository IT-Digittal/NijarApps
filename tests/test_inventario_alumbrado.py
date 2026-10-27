"""Importación del inventario de alumbrado de WeLight (lectura del Excel, sin BD)."""

from __future__ import annotations

import io

import openpyxl

from nijar_dti.services import inventario_alumbrado_service as inv_svc

CABECERA = [
    "LUMINARY IDENTIFIER\n(*)",
    "LUMINARY MANUFACTURER\n(C)",
    "LUMINARY TYPE\n(C)",
    "LUMINARY LATITUDE\n(*)",
    "LUMINARY LONGITUDE\n(*)",
    "LUMINARY INSTALLATION DATE\n[DD/MM/AAAA] (*)",
    "LAMP TYPE\n(C)",
    "LAMP POWER\n[W] (*)",
    "PANEL NAME\n(*)",
    "PANEL LATITUDE\n(*)",
    "PANEL LONGITUDE\n(*)",
    "PANEL CUPS",
    "PANEL TELEMANAGEMENT DEVICE\n(C)",
    "PANEL TELEMANAGEMENT MANUFACTURER\n(C)",
]


def _excel(filas: list[list]) -> bytes:
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.title = "Inventory para Níjar"
    hoja.append(CABECERA)
    for f in filas:
        hoja.append(f)
    buf = io.BytesIO()
    libro.save(buf)
    return buf.getvalue()


def _fila(ident, lampara, w, cuadro, lat=36.76, lon=-2.11, cups="ES0031000000000001AB"):
    return [
        ident,
        "PHILIPS",
        "VIAL",
        lat,
        lon,
        1684879200,
        lampara,
        w,
        cuadro,
        lat,
        lon,
        cups,
        "UCA",
        "SOL-X",
    ]


class TestLectura:
    def test_jerarquia_zona_cuadro_luminaria(self):
        inv = inv_svc.leer_inventario_welight(
            _excel(
                [
                    _fila("001", "LED", 30, "SAN JOSE - CM 001"),
                    _fila("002", "VAPOR DE SODIO A ALTA PRESION", 150, "SAN JOSE - CM 001"),
                    _fila("003", "HM", 70, "FERNAN PEREZ - CM 002", 36.88, -2.06, None),
                    _fila("004", "DESCONOCIDO", 0, "CM GLORIETA", 36.761, -2.111, None),
                ]
            )
        )
        r = inv.resumen()
        assert r["luminarias"] == 4 and r["cuadros"] == 3 and r["cups"] == 1
        assert r["tecnologia"] == {"led": 1, "vsap": 1, "hm": 1, "desconocida": 1}
        assert r["telegestion"] == {"SOL-X": 3}
        zonas = {z["id"]: z for z in inv.zonas}
        assert zonas["sanjose"]["nombre"] == "San José" and zonas["sanjose"]["luminarias"] == 3
        assert zonas["fernan-perez"]["nombre"] == "Fernán Pérez"
        # el cuadro sin núcleo en el nombre va al núcleo más cercano
        assert any("CM GLORIETA" in a and "San José" in a for a in inv.avisos)
        cm = next(c for c in inv.cuadros if c["nombre"] == "SAN JOSE - CM 001")
        assert cm["potencia_kw"] == 0.18 and cm["comunicaciones"] == "sin telemetría"
        assert cm["metadatos"]["cups"] == ["ES0031000000000001AB"]
        lum = next(x for x in inv.luminarias if x["codigo"] == "WL-001")
        assert lum["cuadro_codigo"] == cm["codigo"] and lum["anio_instalacion"] == 2023
        assert lum["consumo_mes_kwh"] == inv_svc.consumo_mes_estimado(30)

    def test_rechaza_excel_que_no_es_de_welight(self):
        libro = openpyxl.Workbook()
        libro.active.append(["A", "B"])
        buf = io.BytesIO()
        libro.save(buf)
        try:
            inv_svc.leer_inventario_welight(buf.getvalue())
        except ValueError as exc:
            assert "WeLight" in str(exc)
        else:
            raise AssertionError("debía rechazar el fichero")

    def test_identificadores_repetidos(self):
        inv = inv_svc.leer_inventario_welight(
            _excel([_fila("001", "LED", 30, "SAN JOSE - CM 001")] * 2)
        )
        assert len(inv.luminarias) == 1 and inv.avisos


class TestUtilidades:
    def test_fechas_sin_dato(self):
        assert inv_svc.anio_de(0) is None and inv_svc.anio_de(3600) is None
        assert inv_svc.anio_de(1739000000) == 2025

    def test_nombres(self):
        assert inv_svc.nombre_zona("LA ISLETA DEL MORO") == "La Isleta del Moro"
        assert inv_svc.zona_de_cuadro("VILLA DE NÍJAR - CM 003") == ("nijar", "Níjar casco")
        assert inv_svc.zona_de_cuadro("SIN GUION") is None
