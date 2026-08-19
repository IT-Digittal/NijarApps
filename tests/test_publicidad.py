"""Tests del módulo de publicidad (empresas anunciantes)."""

from __future__ import annotations

import pytest

from nijar_dti.data.seeds.publicidad import EMPRESAS_SEED
from nijar_dti.models.empresa_anunciante import SECTORES_EMPRESA
from nijar_dti.schemas.publicidad import EmpresaIn, EmpresaPublicaOut
from nijar_dti.services.publicidad_service import PublicidadError, crear_empresa


async def test_sector_invalido_falla_antes_de_bbdd():
    payload = EmpresaIn(nombre="X", sector="astronautica")
    with pytest.raises(PublicidadError, match="no válido"):
        await crear_empresa(None, payload)  # type: ignore[arg-type]


def test_salida_publica_sin_datos_de_gestion():
    """El tótem no debe recibir email de contacto interno ni campos de campaña."""
    campos = set(EmpresaPublicaOut.model_fields)
    assert "email" not in campos
    assert "prioridad" not in campos
    assert "campana_desde" not in campos and "campana_hasta" not in campos
    assert {"nombre", "sector", "descripcion_i18n", "telefono", "web", "destacado"} <= campos


def test_seed_empresas_valido():
    assert len(EMPRESAS_SEED) >= 3
    for e in EMPRESAS_SEED:
        assert e["sector"] in SECTORES_EMPRESA, e["nombre"]
        assert e["publicado"] is True
        i18n = e.get("descripcion_i18n") or {}
        assert {"es", "en", "de", "fr"} <= set(i18n), f"{e['nombre']} sin 4 idiomas"
    assert sum(1 for e in EMPRESAS_SEED if e.get("destacado")) >= 1


def test_agrupar_eventos_suma_por_empresa():
    from uuid import UUID as U

    from nijar_dti.schemas.publicidad import EventoMetricaIn
    from nijar_dti.services.publicidad_service import agrupar_eventos

    a = U("00000000-0000-0000-0000-00000000000a")
    b = U("00000000-0000-0000-0000-00000000000b")
    grupos = agrupar_eventos(
        [
            EventoMetricaIn(empresa_id=a, tipo="impresion", n=1),
            EventoMetricaIn(empresa_id=a, tipo="impresion", n=2),
            EventoMetricaIn(empresa_id=a, tipo="toque", n=1),
            EventoMetricaIn(empresa_id=b, tipo="toque", n=5),
        ]
    )
    assert grupos[a] == {"impresiones": 3, "toques": 1}
    assert grupos[b] == {"impresiones": 0, "toques": 5}


def test_evento_metrica_valida_tipo_y_rango():
    import pydantic

    from nijar_dti.schemas.publicidad import EventoMetricaIn

    with pytest.raises(pydantic.ValidationError):
        EventoMetricaIn(empresa_id="00000000-0000-0000-0000-000000000001", tipo="scroll", n=1)
    with pytest.raises(pydantic.ValidationError):
        EventoMetricaIn(empresa_id="00000000-0000-0000-0000-000000000001", tipo="toque", n=0)
    with pytest.raises(pydantic.ValidationError):
        EventoMetricaIn(empresa_id="00000000-0000-0000-0000-000000000001", tipo="toque", n=101)


class TestRutasApi:
    def test_endpoints_en_openapi(self, client):
        rutas = client.get("/openapi.json").json()["paths"]
        assert "/api/v1/publicidad" in rutas
        assert "/api/v1/publicidad/publico/totem" in rutas
        # El endpoint del tótem es público; el CRUD exige sesión
        assert not rutas["/api/v1/publicidad/publico/totem"]["get"].get("security")
        assert rutas["/api/v1/publicidad"]["post"].get("security")
        assert rutas["/api/v1/publicidad"]["get"].get("security")

    def test_metricas_en_openapi(self, client):
        rutas = client.get("/openapi.json").json()["paths"]
        # El registro desde el tótem es público; el resumen exige sesión
        assert not rutas["/api/v1/publicidad/publico/metricas"]["post"].get("security")
        assert rutas["/api/v1/publicidad/metricas"]["get"].get("security")
