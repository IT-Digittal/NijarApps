"""Campañas de promoción turística (bloque 9 del pliego).

Cada campaña define su periodo (relativo a la fecha de carga), objetivo,
canales, presupuesto orientativo y KPIs objetivo/resultados para poder medir
la eficacia (incremento de menciones/visitas, engagement y sentimiento).

Las fechas son relativas (``delta_inicio_dias`` / ``delta_fin_dias``) para que
la demo siempre tenga campañas pasadas (finalizadas, con resultados), una
activa y una planificada. El campo ``slug`` enlaza con las menciones/visitas
etiquetadas con la campaña.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

# delta_inicio_dias / delta_fin_dias: offset en días respecto a "ahora".
# recurso_urn: recurso turístico asociado (se resuelve a recurso_id en la carga).
CAMPANAS_SEED: list[dict] = [
    {
        "nombre": "Primavera en Cabo de Gata 2026",
        "slug": "primavera-2026",
        "descripcion": (
            "Campaña de temporada media para promover el turismo de naturaleza y "
            "senderismo fuera de los picos estivales, reduciendo la masificación."
        ),
        "objetivo": "visitas",
        "publico_objetivo": "Senderistas y turismo de naturaleza nacional (30-55 años)",
        "canales": ["web", "redes", "email", "prensa"],
        "presupuesto": 8500.00,
        "landing_url": "https://turismo.nijar.es/primavera",
        "recurso_urn": "urn:ngsi-ld:RecursoTuristico:nijar:ruta-vela-blanca",
        "estado": "finalizada",
        "delta_inicio_dias": -120,
        "delta_fin_dias": -75,
        "kpis_objetivo": {"menciones": 400, "visitas_web": 6000, "descargas_app": 300},
        "resultados": {
            "menciones": 512,
            "visitas_web": 7240,
            "descargas_app": 361,
            "interacciones": 9840,
            "alcance": 145000,
            "sentimiento_positivo_pct": 78.0,
            "incremento_menciones_pct": 41.0,
            "incremento_visitas_pct": 33.0,
        },
        "etiquetas": ["primavera", "naturaleza", "senderismo", "desestacionalizacion"],
    },
    {
        "nombre": "Descubre la Cerámica y las Jarapas de Níjar",
        "slug": "artesania-2026",
        "descripcion": (
            "Puesta en valor de la artesanía local (cerámica y jarapas) y del casco "
            "histórico de Níjar como producto turístico cultural."
        ),
        "objetivo": "difusion",
        "publico_objetivo": "Turismo cultural y de compras, visitantes internacionales",
        "canales": ["redes", "app", "prensa"],
        "presupuesto": 5200.00,
        "landing_url": "https://turismo.nijar.es/artesania",
        "recurso_urn": "urn:ngsi-ld:RecursoTuristico:nijar:nijar-pueblo",
        "estado": "finalizada",
        "delta_inicio_dias": -70,
        "delta_fin_dias": -40,
        "kpis_objetivo": {"menciones": 250, "visitas_web": 3000},
        "resultados": {
            "menciones": 268,
            "visitas_web": 3420,
            "interacciones": 5120,
            "alcance": 82000,
            "sentimiento_positivo_pct": 84.0,
            "incremento_menciones_pct": 22.0,
            "incremento_visitas_pct": 18.0,
        },
        "etiquetas": ["artesania", "ceramica", "jarapas", "cultura"],
    },
    {
        "nombre": "Verano Sostenible en Níjar",
        "slug": "verano-2026",
        "descripcion": (
            "Campaña estival de sensibilización sobre uso responsable de playas "
            "protegidas (aforo, transporte público y respeto al entorno)."
        ),
        "objetivo": "sensibilizacion",
        "publico_objetivo": "Turistas de sol y playa nacionales e internacionales",
        "canales": ["web", "redes", "app", "totem", "prensa"],
        "presupuesto": 12000.00,
        "landing_url": "https://turismo.nijar.es/verano-sostenible",
        "recurso_urn": "urn:ngsi-ld:RecursoTuristico:nijar:playa-monsul",
        "estado": "activa",
        "delta_inicio_dias": -10,
        "delta_fin_dias": 50,
        "kpis_objetivo": {"menciones": 800, "visitas_web": 15000, "descargas_app": 900},
        "resultados": {
            "menciones": 214,
            "visitas_web": 4180,
            "descargas_app": 248,
            "interacciones": 3960,
            "alcance": 61000,
            "sentimiento_positivo_pct": 71.0,
        },
        "etiquetas": ["verano", "playas", "sostenibilidad", "aforo"],
    },
    {
        "nombre": "Otoño de Rutas y Estrellas",
        "slug": "otono-2026",
        "descripcion": (
            "Campaña de temporada baja centrada en senderismo, cicloturismo y "
            "astroturismo (cielos del Parque Natural)."
        ),
        "objetivo": "reservas",
        "publico_objetivo": "Turismo activo y astroturismo, parejas y grupos reducidos",
        "canales": ["web", "redes", "email"],
        "presupuesto": 6800.00,
        "landing_url": "https://turismo.nijar.es/otono",
        "recurso_urn": "urn:ngsi-ld:RecursoTuristico:nijar:ruta-rodalquilar-albaricoques",
        "estado": "planificada",
        "delta_inicio_dias": 60,
        "delta_fin_dias": 120,
        "kpis_objetivo": {"menciones": 350, "visitas_web": 5000, "reservas": 120},
        "resultados": None,
        "etiquetas": ["otono", "senderismo", "astroturismo", "desestacionalizacion"],
    },
]


def generar_campanas_seed(ref: datetime | None = None) -> list[dict]:
    """Materializa las campañas con fechas absolutas relativas a ``ref``."""
    base = ref or datetime.now(UTC)
    campanas = []
    for c in CAMPANAS_SEED:
        inicio = (base + timedelta(days=c["delta_inicio_dias"])).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        fin = (base + timedelta(days=c["delta_fin_dias"])).replace(
            hour=23, minute=59, second=0, microsecond=0
        )
        campanas.append(
            {
                "nombre": c["nombre"],
                "slug": c["slug"],
                "descripcion": c.get("descripcion"),
                "objetivo": c.get("objetivo", "difusion"),
                "publico_objetivo": c.get("publico_objetivo"),
                "canales": c.get("canales"),
                "presupuesto": c.get("presupuesto"),
                "landing_url": c.get("landing_url"),
                "recurso_urn": c.get("recurso_urn"),
                "estado": c.get("estado", "planificada"),
                "kpis_objetivo": c.get("kpis_objetivo"),
                "resultados": c.get("resultados"),
                "etiquetas": c.get("etiquetas"),
                "fecha_inicio": inicio,
                "fecha_fin": fin,
            }
        )
    return campanas
