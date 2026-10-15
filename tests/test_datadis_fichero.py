"""Tests del importador del fichero descargado de datadis.es, sin red ni BBDD."""

from __future__ import annotations

import io
from datetime import date

import pytest
from openpyxl import Workbook

from nijar_dti.config import Settings
from nijar_dti.connectors.datadis_fichero import FicheroDatadisError, leer_fichero
from nijar_dti.services import datadis_service as svc

CSV_WEB = """Existen 33 registros sobre los que no se van a mostrar datos de energía
Para los filtros aplicados hay un total de energía de 5.311,151 MWh
Comunidad;Provincia;Municipio;Fecha;Sector;Tensión;Contratos (Suma);Energía (Suma kWh)
Andalucía;Almería;NÍJAR;15/07/2026;INDUSTRIA;Baja tensión;408;24.271
Andalucía;Almería;NÍJAR;15/07/2026;RESIDENCIAL;Baja tensión;14.597;191.589
Andalucía;Almería;NÍJAR;15/07/2026;SERVICIOS;>= 14 kV y < 36 kV;99;80.333,5
;;;;;;;
"""


def test_csv_de_la_web_latin1_con_preambulo():
    regs = leer_fichero(CSV_WEB.encode("latin-1"), "consulta.csv")
    assert len(regs) == 3 and all(regs)
    assert [r.energia_kwh for r in regs if r] == [24271.0, 191589.0, 80333.5]
    assert regs[1] and regs[1].contratos == 14597 and regs[1].fecha == date(2026, 7, 15)
    assert regs[2] and regs[2].tension == ">= 14 kV y < 36 kV"


def test_csv_con_comas_y_cabecera_inglesa_en_mwh():
    txt = (
        "Community,Province,Municipality,Date,Sector,Voltage,Contracts (Sum),Energy (Sum MWh)\n"
        "Andalucía,Almería,NÍJAR,2026-07-16,RESIDENTIAL,Low,14600,191.5\n"
    )
    (r,) = leer_fichero(txt.encode(), "x.csv")
    assert r and r.energia_kwh == pytest.approx(191500.0) and r.sector == "RESIDENTIAL"


def test_excel():
    wb = Workbook()
    ws = wb.active
    ws.append(["Comunidad", "Provincia", "Municipio", "Fecha", "Sector", "Tensión",
               "Contratos (Suma)", "Energía (Suma kWh)"])  # fmt: skip
    ws.append(["Andalucía", "Almería", "NÍJAR", date(2026, 7, 17), "SERVICIOS", "Baja tensión",
               3936, 119702.4])  # fmt: skip
    buf = io.BytesIO()
    wb.save(buf)
    (r,) = leer_fichero(buf.getvalue(), "consulta.xlsx")
    assert r and r.fecha == date(2026, 7, 17) and r.energia_kwh == 119702.4


def test_fichero_ajeno_da_error_claro():
    with pytest.raises(FicheroDatadisError):
        leer_fichero(b"nombre;apellidos\nAna;Ruiz\n", "otro.csv")


def test_credenciales_de_plantilla_no_cuentan():
    plantilla = Settings(
        secret_key="x" * 40,
        database_url="postgresql+asyncpg://a:b@localhost/c",
        datadis_usuario="<NIF/CIF del usuario>",
        datadis_password="<contraseña>",
    )
    assert svc.datadis_configurado(plantilla) is False
    assert svc.nuevo_cliente(plantilla).tiene_credenciales is False
    real = plantilla.model_copy(update={"datadis_usuario": "B04000000", "datadis_password": "x"})
    assert svc.datadis_configurado(real) is True
