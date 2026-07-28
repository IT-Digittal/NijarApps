"""Seed de las capas geográficas del gemelo 2D (concepto «geoportal Níjar»).

Reproduce sobre Níjar el esquema de capas de un geoportal municipal de
urbanismo (clasificación del suelo, calificación y usos, ordenación
estructural, partidos rurales y parcelario catastral).

IMPORTANTE — datos de demostración: las geometrías son ilustrativas y sirven
para dejar la infraestructura de capas montada y visible. La cartografía real
(PGOU de Níjar y parcelario del Catastro) se cargará como filas de estas
mismas tablas cuando el Ayuntamiento la aporte, sin cambios de esquema. Por eso
cada capa lleva `fuente` = «Demostración…» y el prefijo «(demo)» en su nombre.
"""

from __future__ import annotations

from typing import Any

# Núcleos de referencia del término municipal (lon, lat)
NIJAR_CASCO = (-2.2074, 36.9660)
SAN_JOSE = (-2.1060, 36.7600)
RODALQUILAR = (-2.0410, 36.8470)
LAS_NEGRAS = (-2.0000, 36.8800)


def _rect(lon: float, lat: float, dlon: float, dlat: float) -> str:
    """Polígono rectangular WKT (anillo cerrado) centrado en (lon, lat)."""
    x0, x1 = lon - dlon, lon + dlon
    y0, y1 = lat - dlat, lat + dlat
    anillo = f"{x0} {y0}, {x1} {y0}, {x1} {y1}, {x0} {y1}, {x0} {y0}"
    return f"POLYGON(({anillo}))"


def generar_capas_seed() -> list[dict[str, Any]]:
    """Catálogo de capas de demostración con sus elementos vectoriales."""
    demo = "Demostración — pendiente de carga del PGOU / Catastro de Níjar"
    lon, lat = NIJAR_CASCO

    return [
        {
            "codigo": "clasificacion_suelo",
            "nombre": "Clasificación del suelo (demo)",
            "grupo": "clasificacion",
            "tipo_geometria": "poligono",
            "descripcion": "Clasificación urbanística del término municipal: "
            "urbano, urbanizable y no urbanizable.",
            "color": "#E5673B",
            "color_borde": "#8A3A1E",
            "opacidad": 0.35,
            "campo_etiqueta": "clasificacion",
            "orden": 10,
            "fuente": demo,
            "elementos": [
                {
                    "nombre": "Suelo Urbano — casco de Níjar",
                    "codigo": "SU-01",
                    "propiedades": {
                        "clasificacion": "Suelo Urbano Consolidado",
                        "superficie_ha": 42.0, "_color": "#E5484D",
                    },
                    "wkt": _rect(lon, lat, 0.012, 0.008),
                },
                {
                    "nombre": "Suelo Urbanizable — sector este",
                    "codigo": "SUZ-02",
                    "propiedades": {
                        "clasificacion": "Suelo Urbanizable Sectorizado",
                        "superficie_ha": 18.5, "_color": "#F0B429",
                    },
                    "wkt": _rect(lon + 0.020, lat + 0.001, 0.007, 0.006),
                },
                {
                    "nombre": "Suelo No Urbanizable — Especial Protección",
                    "codigo": "SNU-EP",
                    "propiedades": {
                        "clasificacion": "No Urbanizable (Especial Protección)",
                        "superficie_ha": 3200.0, "_color": "#12A150",
                    },
                    "wkt": _rect(lon + 0.06, lat - 0.05, 0.09, 0.06),
                },
            ],
        },
        {
            "codigo": "calificacion_usos",
            "nombre": "Calificación, usos y sistemas (demo)",
            "grupo": "planeamiento",
            "tipo_geometria": "poligono",
            "descripcion": "Calificación pormenorizada del suelo urbano: usos "
            "residencial, industrial/terciario y sistemas (equipamientos y zonas verdes).",
            "color": "#7C6BF0",
            "color_borde": "#4A3AB0",
            "opacidad": 0.45,
            "campo_etiqueta": "uso",
            "orden": 20,
            "fuente": demo,
            "elementos": [
                {
                    "nombre": "Residencial casco antiguo",
                    "codigo": "R1",
                    "propiedades": {
                        "uso": "Residencial", "ordenanza": "R-1 casco tradicional",
                        "edificabilidad_m2m2": 1.2, "_color": "#C084E8",
                    },
                    "wkt": _rect(lon - 0.004, lat + 0.001, 0.006, 0.004),
                },
                {
                    "nombre": "Industrial / terciario",
                    "codigo": "I1",
                    "propiedades": {
                        "uso": "Industrial-Terciario", "ordenanza": "I-1",
                        "edificabilidad_m2m2": 0.8, "_color": "#7B5A3A",
                    },
                    "wkt": _rect(lon + 0.009, lat - 0.004, 0.004, 0.003),
                },
                {
                    "nombre": "Sistema general — zona verde",
                    "codigo": "SGV",
                    "propiedades": {
                        "uso": "Sistema General", "tipo": "Espacio libre / zona verde",
                        "_color": "#18794E",
                    },
                    "wkt": _rect(lon + 0.003, lat + 0.006, 0.005, 0.003),
                },
            ],
        },
        {
            "codigo": "ordenacion_estructural",
            "nombre": "Ordenación estructural (demo)",
            "grupo": "planeamiento",
            "tipo_geometria": "poligono",
            "descripcion": "Determinaciones estructurales del planeamiento general "
            "(sistemas generales y sectores).",
            "color": "#1F6FE5",
            "color_borde": "#12448F",
            "opacidad": 0.30,
            "campo_etiqueta": "elemento",
            "orden": 30,
            "fuente": demo,
            "elementos": [
                {
                    "nombre": "Núcleo urbano principal",
                    "codigo": "OE-NU",
                    "propiedades": {"elemento": "Núcleo urbano", "categoria": "Estructural"},
                    "wkt": _rect(lon, lat, 0.014, 0.010),
                },
                {
                    "nombre": "Sistema general viario — acceso A-7",
                    "codigo": "OE-SGV",
                    "propiedades": {"elemento": "Sistema general viario", "categoria": "Comunicaciones"},
                    "wkt": _rect(lon + 0.030, lat - 0.006, 0.020, 0.003),
                },
            ],
        },
        {
            "codigo": "partidos_rurales",
            "nombre": "Partidos rurales (demo)",
            "grupo": "otras",
            "tipo_geometria": "poligono",
            "descripcion": "División del término municipal en partidos rurales / "
            "núcleos diseminados.",
            "color": "#0E9BD8",
            "color_borde": "#0A6E99",
            "opacidad": 0.25,
            "campo_etiqueta": "nucleo",
            "orden": 40,
            "fuente": demo,
            "elementos": [
                {
                    "nombre": "Partido de Níjar (casco)",
                    "codigo": "PR-NIJAR",
                    "propiedades": {"nucleo": "Níjar"},
                    "wkt": _rect(lon, lat, 0.04, 0.03),
                },
                {
                    "nombre": "Partido de San José",
                    "codigo": "PR-SANJOSE",
                    "propiedades": {"nucleo": "San José"},
                    "wkt": _rect(SAN_JOSE[0], SAN_JOSE[1], 0.04, 0.03),
                },
                {
                    "nombre": "Partido de Rodalquilar",
                    "codigo": "PR-RODALQUILAR",
                    "propiedades": {"nucleo": "Rodalquilar"},
                    "wkt": _rect(RODALQUILAR[0], RODALQUILAR[1], 0.035, 0.025),
                },
                {
                    "nombre": "Partido de Las Negras",
                    "codigo": "PR-LASNEGRAS",
                    "propiedades": {"nucleo": "Las Negras"},
                    "wkt": _rect(LAS_NEGRAS[0], LAS_NEGRAS[1], 0.03, 0.022),
                },
            ],
        },
        {
            "codigo": "catastro_parcelas",
            "nombre": "Parcelario catastral (demo)",
            "grupo": "catastro",
            "tipo_geometria": "poligono",
            "descripcion": "Parcelas catastrales con su referencia catastral. Se "
            "cargará el parcelario oficial cuando se integren los registros del Catastro.",
            "color": "#C8102E",
            "color_borde": "#8A0A1F",
            "opacidad": 0.15,
            "campo_etiqueta": "referencia_catastral",
            "orden": 50,
            "fuente": demo,
            "elementos": [
                {
                    "nombre": "Parcela demo 1",
                    "referencia_catastral": "0000001AB1234S0001AA",
                    "propiedades": {"uso_catastral": "Residencial", "superficie_m2": 210},
                    "wkt": _rect(lon - 0.0015, lat + 0.0010, 0.0009, 0.0006),
                },
                {
                    "nombre": "Parcela demo 2",
                    "referencia_catastral": "0000002AB1234S0001AB",
                    "propiedades": {"uso_catastral": "Comercial", "superficie_m2": 145},
                    "wkt": _rect(lon + 0.0006, lat + 0.0004, 0.0008, 0.0005),
                },
                {
                    "nombre": "Parcela demo 3",
                    "referencia_catastral": "0000003AB1234S0001AC",
                    "propiedades": {"uso_catastral": "Equipamiento", "superficie_m2": 320},
                    "wkt": _rect(lon + 0.0022, lat - 0.0008, 0.0011, 0.0007),
                },
            ],
        },
    ]
