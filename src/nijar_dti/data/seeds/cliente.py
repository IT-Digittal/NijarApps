"""Ficha general del cliente / Ayuntamiento (bloque 1 del pliego).

Datos de cabecera del proyecto para identificar responsables, canales
oficiales, idiomas activos y periodo de explotación. Se carga una única vez
(idempotente por ``nombre``).
"""

from __future__ import annotations

from datetime import datetime, timezone

CLIENTE_SEED: dict = {
    "nombre": "Ayuntamiento de Níjar",
    "area_responsable": "Área de Turismo y Nuevas Tecnologías",
    "proyecto": "Plataforma Smart City DTI — Destino Turístico Inteligente",
    "descripcion": (
        "Plataforma DTI del municipio de Níjar: Smart Office, Social Listening / "
        "Big Data, chatbot turístico multilingüe, tótems interactivos, CMS y "
        "cuadro de mando de KPIs para el Parque Natural de Cabo de Gata-Níjar."
    ),
    "cif": "P0406600J",
    "direccion": "Plaza de la Glorieta, 1, 04100 Níjar (Almería)",
    "municipio": "Níjar",
    "provincia": "Almería",
    "responsable_municipal": {
        "nombre": "Responsable municipal de Turismo",
        "cargo": "Concejalía de Turismo",
        "email": "turismo@nijar.es",
        "telefono": "+34 950 360 012",
    },
    "responsables_tecnicos": [
        {
            "area": "TI municipal",
            "nombre": "Responsable de Informática",
            "email": "informatica@nijar.es",
            "telefono": "+34 950 360 012",
        },
        {
            "area": "Turismo",
            "nombre": "Técnico/a de Turismo",
            "email": "turismo@nijar.es",
            "telefono": "+34 950 360 012",
        },
        {
            "area": "Comunicación",
            "nombre": "Gabinete de Comunicación",
            "email": "comunicacion@nijar.es",
            "telefono": "+34 950 360 012",
        },
        {
            "area": "Mantenimiento",
            "nombre": "Servicio de mantenimiento (C.1)",
            "email": "soporte-dti@nijar.es",
            "telefono": "+34 950 360 012",
        },
    ],
    "canales_oficiales": {
        "web": "https://turismo.nijar.es",
        "app": "Vive Níjar",
        "facebook": "https://www.facebook.com/AyuntamientodeNijar",
        "instagram": "https://www.instagram.com/turismonijar",
        "otros": [
            "https://www.andalucia.org",
            "Tótems interactivos (Rodalquilar y Los Albaricoques)",
        ],
    },
    "idiomas_activos": ["es", "en", "fr", "de"],
    "fecha_inicio_explotacion": datetime(2026, 1, 15, tzinfo=timezone.utc),
    "fecha_fin_mantenimiento": datetime(2028, 1, 14, tzinfo=timezone.utc),
    "hitos": [
        {"nombre": "Puesta en producción de la plataforma", "fecha": "2026-01-15", "estado": "completado"},
        {"nombre": "Despliegue de tótems interactivos", "fecha": "2026-02-01", "estado": "completado"},
        {"nombre": "Chatbot multilingüe en producción", "fecha": "2026-02-15", "estado": "completado"},
        {"nombre": "Social Listening operativo", "fecha": "2026-03-01", "estado": "completado"},
        {"nombre": "Primer informe mensual de KPIs", "fecha": "2026-04-05", "estado": "completado"},
        {"nombre": "Revisión anual del servicio", "fecha": "2027-01-15", "estado": "planificado"},
    ],
    "activo": True,
    "metadata_adicional": {
        "espacio_protegido": "Parque Natural Cabo de Gata-Níjar",
        "reconocimientos": ["Reserva de la Biosfera", "Geoparque UNESCO"],
        "periodo_mantenimiento_meses": 24,
    },
}
