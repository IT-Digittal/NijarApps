"""Tests del endpoint público de contenidos del tótem (CMS multicanal)."""

from __future__ import annotations

from datetime import datetime

from nijar_dti.schemas.cms import AvisoPublicoOut


class TestEndpointPublicoTotem:
    def test_ruta_en_openapi_y_sin_autenticacion(self, client):
        spec = client.get("/openapi.json").json()
        ruta = spec["paths"].get("/api/v1/cms/publico/totem")
        assert ruta is not None, "falta la ruta pública del tótem"
        get = ruta["get"]
        # Público: sin requisito de seguridad (el tótem no tiene sesión)
        assert not get.get("security"), "el endpoint del tótem no debe exigir autenticación"

    def test_gemelo_aire_resumen_tambien_publico(self, client):
        spec = client.get("/openapi.json").json()
        get = spec["paths"]["/api/v1/gemelo/aire/resumen"]["get"]
        assert not get.get("security")


def test_aviso_publico_schema_serializa_i18n():
    aviso = AvisoPublicoOut.model_validate(
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "titulo": "Corte de agua en San José",
            "titulo_i18n": {"es": "Corte de agua en San José", "en": "Water cut in San José"},
            "cuerpo": "El martes de 9:00 a 13:00.",
            "cuerpo_i18n": None,
            "publicar_hasta": datetime(2026, 7, 20, 12, 0),
        }
    )
    assert aviso.titulo_i18n is not None and aviso.titulo_i18n.en == "Water cut in San José"
    assert aviso.publicar_hasta is not None
