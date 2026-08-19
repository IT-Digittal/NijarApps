"""Datos de demostración para poblar los dashboards.

Genera observaciones IoT, opiniones de social listening,
interacciones de tótems y sesiones de chatbot para que el
dashboard muestre datos realistas sin necesidad de workers activos.
"""

from __future__ import annotations

import hashlib
import random
from datetime import UTC, datetime, timedelta

# ---------- Observaciones IoT (últimas 48h, cada 15 min) ----------

_NOW = datetime.now(UTC)
_INTERVALO_MIN = 15
_HORAS_ATRAS = 48
_NUM_PUNTOS = (_HORAS_ATRAS * 60) // _INTERVALO_MIN  # 192

# Rangos realistas por tipo de sensor
_SENSOR_RANGES: dict[str, tuple[float, float, str]] = {
    "ambiental_co2": (400.0, 900.0, "ppm"),
    "ambiental_temperatura": (19.0, 28.0, "°C"),
    "ambiental_humedad": (35.0, 65.0, "%"),
    "ambiental_ruido": (35.0, 58.0, "dB"),
}


def generar_observaciones_seed(sensores_por_tipo: dict[str, str]) -> list[dict]:
    """Genera observaciones sintéticas para los sensores ambientales.

    Args:
        sensores_por_tipo: dict de tipo_sensor -> sensor_id (UUID como string).
    """
    observaciones = []
    for tipo, sensor_id in sensores_por_tipo.items():
        if tipo not in _SENSOR_RANGES:
            continue
        vmin, vmax, unidades = _SENSOR_RANGES[tipo]
        centro = (vmin + vmax) / 2
        amplitud = (vmax - vmin) / 2
        valor_actual = centro
        for i in range(_NUM_PUNTOS):
            ts = _NOW - timedelta(minutes=_INTERVALO_MIN * (_NUM_PUNTOS - i))
            # Paseo aleatorio con tendencia a volver al centro
            delta = random.uniform(-amplitud * 0.05, amplitud * 0.05)
            valor_actual += delta + (centro - valor_actual) * 0.02
            valor_actual = max(vmin, min(vmax, valor_actual))
            observaciones.append(
                {
                    "sensor_id": sensor_id,
                    "observado_en": ts,
                    "valor": round(valor_actual, 2),
                    "unidades": unidades,
                    "valido": True,
                }
            )
    return observaciones


# ---------- Salud/telemetría de tótems (últimos 7 días, cada hora) ----------

_TOTEM_HORAS_ATRAS = 7 * 24  # 168 puntos horarios por tótem


def generar_observaciones_totem_seed(sensores_totem: dict[str, str]) -> list[dict]:
    """Genera telemetría de salud de los tótems (online, temperatura, reinicios).

    Alimenta los KPIs del pliego de tótems: disponibilidad (horas online / horas
    totales), temperatura interna (mantenimiento preventivo) y reinicios.

    Args:
        sensores_totem: dict de urn -> sensor_id (UUID como string) de los
            sensores de tipo ``totem``.
    """
    observaciones: list[dict] = []
    for idx, (_urn, sensor_id) in enumerate(sensores_totem.items()):
        # Ventanas de indisponibilidad simuladas (distintas por tótem)
        offline_horas = set()
        # Un corte corto y otro más largo, desfasados por tótem
        inicio_corte = 30 + idx * 20
        for h in range(inicio_corte, inicio_corte + 2 + idx):
            offline_horas.add(h)
        reinicios_acum = 0
        for i in range(_TOTEM_HORAS_ATRAS):
            ts = _NOW - timedelta(hours=(_TOTEM_HORAS_ATRAS - i))
            online = i not in offline_horas
            # Un reinicio justo al recuperar el servicio
            if not online and (i + 1) not in offline_horas:
                reinicios_acum += 1
            # Temperatura interna: base 32 °C + ciclo diario + ruido
            hora_dia = ts.hour
            temp = 32 + 8 * (1 if 12 <= hora_dia <= 18 else 0) + random.uniform(-3, 4)
            observaciones.append(
                {
                    "sensor_id": sensor_id,
                    "observado_en": ts,
                    "unidades": "estado",
                    "valores": {
                        "online": 1 if online else 0,
                        "temperatura_interna": round(temp, 1),
                        "reinicios_acumulados": reinicios_acum,
                        "conectividad_pct": round(random.uniform(96, 100), 1) if online else 0.0,
                    },
                    "valido": True,
                }
            )
    return observaciones


# ---------- Opiniones Social Listening (últimos 30 días) ----------

_OPINION_TEMPLATES = [
    {
        "fuente": "twitter_x",
        "texto": "Increíble atardecer en la Playa de Mónsul 🌅 #CaboDeGata #Níjar",
        "sentimiento": "positivo",
        "score": 0.85,
        "idioma": "es",
        "temas": ["playa", "naturaleza", "fotografia"],
    },
    {
        "fuente": "instagram",
        "texto": "Amazing day hiking from Rodalquilar to Los Albaricoques! The old gold mine is stunning 🏔️",
        "sentimiento": "positivo",
        "score": 0.92,
        "idioma": "en",
        "temas": ["ruta", "senderismo", "patrimonio"],
    },
    {
        "fuente": "facebook",
        "texto": "El centro de visitantes Las Amoladeras es muy interesante, pero el horario es corto",
        "sentimiento": "neutro",
        "score": 0.45,
        "idioma": "es",
        "temas": ["informacion", "horario"],
    },
    {
        "fuente": "twitter_x",
        "texto": "Wunderschöner Strand Genoveses! Kristallklares Wasser 💎 #CaboDeGata",
        "sentimiento": "positivo",
        "score": 0.90,
        "idioma": "de",
        "temas": ["playa", "naturaleza"],
    },
    {
        "fuente": "instagram",
        "texto": "La Isleta del Moro, un pueblo con encanto. El pescado a la sal, espectacular 🐟",
        "sentimiento": "positivo",
        "score": 0.88,
        "idioma": "es",
        "temas": ["gastronomia", "pueblo"],
    },
    {
        "fuente": "facebook",
        "texto": "Demasiada gente en Mónsul en agosto, imposible aparcar. Necesitan mejor transporte público",
        "sentimiento": "negativo",
        "score": 0.20,
        "idioma": "es",
        "temas": ["masificacion", "transporte"],
    },
    {
        "fuente": "twitter_x",
        "texto": "Les plages de Cabo de Gata sont magnifiques, un vrai paradis naturel 🏖️",
        "sentimiento": "positivo",
        "score": 0.87,
        "idioma": "fr",
        "temas": ["playa", "naturaleza"],
    },
    {
        "fuente": "instagram",
        "texto": "Ruta en bici por los paisajes mineros de Rodalquilar. ¡Totalmente recomendable! 🚴",
        "sentimiento": "positivo",
        "score": 0.91,
        "idioma": "es",
        "temas": ["ruta", "ciclismo", "patrimonio"],
    },
    {
        "fuente": "twitter_x",
        "texto": "Cala de Enmedio worth every step of the hike! Crystal clear water and almost no people",
        "sentimiento": "positivo",
        "score": 0.93,
        "idioma": "en",
        "temas": ["playa", "senderismo"],
    },
    {
        "fuente": "facebook",
        "texto": "Las jarapas de Níjar son una artesanía única. Compré varias en los talleres del casco antiguo",
        "sentimiento": "positivo",
        "score": 0.82,
        "idioma": "es",
        "temas": ["artesania", "cultura", "compras"],
    },
    {
        "fuente": "instagram",
        "texto": "Mirador de la Amatista al amanecer. No hay palabras. #CaboDeGata #Almería",
        "sentimiento": "positivo",
        "score": 0.95,
        "idioma": "es",
        "temas": ["mirador", "fotografia", "naturaleza"],
    },
    {
        "fuente": "twitter_x",
        "texto": "El chatbot del ayuntamiento me ayudó a encontrar las rutas, muy útil 👍",
        "sentimiento": "positivo",
        "score": 0.78,
        "idioma": "es",
        "temas": ["chatbot", "tecnologia", "turismo"],
    },
    {
        "fuente": "tripadvisor",
        "texto": "Great visit to San José. Beautiful beaches and good restaurants, though parking is a challenge in August.",
        "sentimiento": "positivo",
        "score": 0.74,
        "idioma": "en",
        "temas": ["playa", "gastronomia", "transporte"],
    },
    {
        "fuente": "google_reviews",
        "texto": "Oficina de turismo de Níjar muy atenta, nos dieron mapas y rutas en varios idiomas. Recomendable.",
        "sentimiento": "positivo",
        "score": 0.86,
        "idioma": "es",
        "temas": ["informacion", "servicios", "atencion"],
    },
    {
        "fuente": "tripadvisor",
        "texto": "Las Negras is lovely but the beach could be cleaner after busy weekends. More bins needed.",
        "sentimiento": "negativo",
        "score": 0.28,
        "idioma": "en",
        "temas": ["limpieza", "playa", "servicios"],
    },
    {
        "fuente": "google_reviews",
        "texto": "Rodalquilar mine area is amazing but signage on the trails is poor, we got a bit lost.",
        "sentimiento": "neutro",
        "score": 0.48,
        "idioma": "en",
        "temas": ["ruta", "senalizacion", "patrimonio"],
    },
    {
        "fuente": "facebook",
        "texto": "Nos encantó la Noche de las Salinas, gran ambiente y organización. ¡Repetiremos! #ViveNíjar",
        "sentimiento": "positivo",
        "score": 0.9,
        "idioma": "es",
        "temas": ["evento", "musica", "cultura"],
    },
    {
        "fuente": "twitter_x",
        "texto": "Der Bus nach San José war überfüllt und unpünktlich. Der öffentliche Verkehr muss besser werden.",
        "sentimiento": "negativo",
        "score": 0.24,
        "idioma": "de",
        "temas": ["transporte", "movilidad"],
    },
]

# Reparto de fuentes para el alcance estimado (seguidores medios por plataforma)
_ALCANCE_BASE = {
    "twitter_x": 1800,
    "instagram": 3200,
    "facebook": 2500,
    "tripadvisor": 900,
    "google_reviews": 600,
}

# Menciones etiquetadas dentro de la ventana de una campaña (para KPI de eficacia).
# slug -> (dias_desde, dias_hasta) relativo a _NOW; alineado con campanas.py.
_CAMPANA_VENTANAS = {
    "primavera-2026": (75, 120),
    "artesania-2026": (40, 70),
    "verano-2026": (0, 10),
}

_NUM_OPINIONES = 90


def _campana_para(dias_atras: int) -> str | None:
    for slug, (desde, hasta) in _CAMPANA_VENTANAS.items():
        if desde <= dias_atras <= hasta:
            return slug
    return None


def generar_opiniones_seed() -> list[dict]:
    opiniones = []
    for i in range(_NUM_OPINIONES):
        tmpl = _OPINION_TEMPLATES[i % len(_OPINION_TEMPLATES)]
        # Repartir en 120 días para cubrir las ventanas de campaña.
        dias_atras = random.randint(0, 120)
        horas_atras = random.randint(0, 23)
        ts = _NOW - timedelta(days=dias_atras, hours=horas_atras)
        base_alcance = _ALCANCE_BASE.get(tmpl["fuente"], 800)
        likes = random.randint(2, 120)
        metricas = {
            "likes": likes,
            "comentarios": random.randint(0, 25),
            "compartidos": random.randint(0, 40),
            "alcance_estimado": base_alcance + random.randint(-400, 1200),
        }
        campana = _campana_para(dias_atras)
        if campana:
            metricas["campana"] = campana
        opiniones.append(
            {
                "fuente": tmpl["fuente"],
                "fuente_id_externo": f"demo-{i:04d}",
                "texto_original": tmpl["texto"],
                "publicado_en": ts,
                "idioma": tmpl["idioma"],
                "sentimiento": tmpl["sentimiento"],
                "score_sentimiento": round(tmpl["score"] + random.uniform(-0.05, 0.05), 4),
                "temas": tmpl["temas"],
                "metricas": metricas,
                "autor_handle": f"@demo_user_{i % 25}",
                "capturado_en": ts + timedelta(minutes=random.randint(1, 30)),
            }
        )
    return opiniones


# ---------- Interacciones de tótems (últimos 7 días) ----------

_SECCIONES_TOTEM = ["mapa", "rutas", "playas", "eventos", "chatbot", "idioma", "accesibilidad"]
_NUM_VISITAS_TOTEM = 80


def generar_visitas_totem_seed() -> list[dict]:
    visitas = []
    for i in range(_NUM_VISITAS_TOTEM):
        dias_atras = random.randint(0, 7)
        horas_atras = random.randint(8, 21)  # horario diurno
        ts = _NOW - timedelta(days=dias_atras, hours=horas_atras - 12)
        visitas.append(
            {
                "tipo": "interaccion_totem",
                "ocurrido_en": ts,
                "visitante_hash": hashlib.sha256(f"visitor-{i % 40}".encode()).hexdigest(),
                "idioma": random.choice(["es", "en", "de", "fr"]),
                "canal": random.choice(["totem_rodalquilar", "totem_albaricoques"]),
                "atributos": {
                    "seccion": random.choice(_SECCIONES_TOTEM),
                    "duracion_seg": random.randint(15, 180),
                },
            }
        )
    return visitas


# ---------- Interacciones de chatbot (últimos 14 días) ----------

_CHATBOT_SAMPLES = [
    (
        "playas_destacadas",
        "es",
        "¿Cuáles son las mejores playas?",
        "Las playas más conocidas son: Mónsul, Genoveses, Playazo y Cala de Enmedio.",
        "alta",
        0.92,
    ),
    (
        "acceso_playa_monsul",
        "es",
        "¿Cómo llego a Mónsul en verano?",
        "Durante la temporada alta el acceso está regulado por aforo.",
        "alta",
        0.88,
    ),
    (
        "ruta_rodalquilar_albaricoques",
        "en",
        "Tell me about the cycling route",
        "An 8.5 km route of low-medium difficulty connecting Rodalquilar with Los Albaricoques.",
        "alta",
        0.85,
    ),
    (
        "donde_comer",
        "es",
        "¿Dónde puedo comer bien?",
        "La gastronomía local se basa en pescado fresco, gurullos y ajoblanco.",
        "alta",
        0.90,
    ),
    ("emergencias", "de", "Notrufnummer?", "Die Notrufnummer in Spanien ist 112.", "alta", 0.95),
    (
        "mejor_epoca_visita",
        "fr",
        "Meilleure période pour visiter?",
        "Le printemps et l'automne sont idéaux.",
        "alta",
        0.87,
    ),
    (
        "saludo",
        "es",
        "Hola, buenos días",
        "¡Hola! Soy el asistente turístico de Níjar.",
        "alta",
        0.99,
    ),
    (
        "artesania_jarapas",
        "en",
        "What are jarapas?",
        "The jarapa is a traditional handcrafted textile from Níjar.",
        "alta",
        0.83,
    ),
    (
        "horario_amoladeras",
        "es",
        "¿Horario del centro de visitantes?",
        "El Centro de Visitantes Las Amoladeras abre de 10:00 a 14:00.",
        "media",
        0.72,
    ),
    (
        "normativa_parque",
        "es",
        "¿Qué está prohibido en el parque?",
        "Está prohibido hacer fuego, acampar fuera de zonas habilitadas...",
        "alta",
        0.91,
    ),
]

# Preguntas fuera de dominio / no cubiertas (KPI de "preguntas sin respuesta").
_CHATBOT_NO_RESUELTAS = [
    ("es", "¿Puedo pagar el parking con bizum en Mónsul?"),
    ("en", "Is there a direct bus from Almería airport to San José at night?"),
    ("fr", "Peut-on louer des vélos électriques à Rodalquilar ?"),
    ("de", "Gibt es einen Hundestrand in der Nähe von Las Negras?"),
    ("es", "¿Hay wifi gratis en la playa de los Genoveses?"),
]

_NUM_INTERACCIONES_CHATBOT = 60
# ~15 % de las consultas quedan sin resolver (derivación / base de conocimiento)
_NUM_CHATBOT_NO_RESUELTAS = 9


# ---------- Eventos turísticos (próximas 2 semanas) ----------

_EVENTOS_SEED = [
    {
        "urn": "urn:ngsi-ld:EventoTuristico:nijar:concierto-salinas",
        "nombre": "Concierto Noche de las Salinas",
        "tipo": "musical",
        "descripcion": "Concierto de flamenco fusión al aire libre en el entorno de las antiguas salinas de Cabo de Gata. Entrada gratuita.",
        "nombre_i18n": {
            "es": "Concierto Noche de las Salinas",
            "en": "Salt Flats Night Concert",
            "de": "Konzert Nacht der Salinen",
            "fr": "Concert Nuit des Salines",
        },
        "descripcion_i18n": {
            "es": "Concierto de flamenco fusión al aire libre en el entorno de las antiguas salinas de Cabo de Gata. Entrada gratuita.",
            "en": "Open-air flamenco fusion concert in the historic Cabo de Gata salt flats. Free admission.",
            "de": "Open-Air-Flamenco-Fusion-Konzert in den historischen Salinen von Cabo de Gata. Eintritt frei.",
            "fr": "Concert de flamenco fusion en plein air dans les anciennes salines de Cabo de Gata. Entrée libre.",
        },
        "direccion": "Salinas de Cabo de Gata",
        "organizador": "Ayuntamiento de Níjar",
        "precio": "Gratuito",
        "capacidad_aforo": 200,
        "etiquetas": ["musica", "flamenco", "gratis", "nocturno"],
        "delta_dias": 3,
        "hora_inicio": 21,
        "duracion_h": 3,
    },
    {
        "urn": "urn:ngsi-ld:EventoTuristico:nijar:ruta-vela-blanca",
        "nombre": "Ruta guiada a Vela Blanca",
        "tipo": "naturaleza",
        "descripcion": "Senderismo guiado por el espectacular sendero costero del Faro de Cabo de Gata a Vela Blanca. 8 km, dificultad media. Inscripción previa obligatoria.",
        "nombre_i18n": {
            "es": "Ruta guiada a Vela Blanca",
            "en": "Guided hike to Vela Blanca",
            "de": "Geführte Wanderung nach Vela Blanca",
            "fr": "Randonnée guidée à Vela Blanca",
        },
        "descripcion_i18n": {
            "es": "Senderismo guiado por el espectacular sendero costero del Faro de Cabo de Gata a Vela Blanca. 8 km, dificultad media. Inscripción previa obligatoria.",
            "en": "Guided hike along the coastal trail from Cabo de Gata Lighthouse to Vela Blanca. 8 km, medium difficulty. Pre-registration required.",
            "de": "Geführte Wanderung auf dem spektakulären Küstenpfad vom Leuchtturm Cabo de Gata nach Vela Blanca. 8 km, mittel. Voranmeldung erforderlich.",
            "fr": "Randonnée guidée le long du sentier côtier du phare de Cabo de Gata à Vela Blanca. 8 km, difficulté moyenne. Inscription préalable obligatoire.",
        },
        "direccion": "Centro de Visitantes Las Amoladeras",
        "organizador": "Junta de Andalucía",
        "precio": "Gratuito · inscripción previa",
        "capacidad_aforo": 20,
        "etiquetas": ["senderismo", "naturaleza", "guiada"],
        "delta_dias": 5,
        "hora_inicio": 9,
        "duracion_h": 4,
    },
    {
        "urn": "urn:ngsi-ld:EventoTuristico:nijar:mercado-ceramica",
        "nombre": "Mercado de cerámica y artesanía",
        "tipo": "cultural",
        "descripcion": "Mercado artesanal con puestos de cerámica, jarapas y productos locales en la Plaza La Glorieta de Níjar.",
        "nombre_i18n": {
            "es": "Mercado de cerámica y artesanía",
            "en": "Pottery and crafts market",
            "de": "Keramik- und Handwerksmarkt",
            "fr": "Marché de poterie et d'artisanat",
        },
        "descripcion_i18n": {
            "es": "Mercado artesanal con puestos de cerámica, jarapas y productos locales en la Plaza La Glorieta de Níjar.",
            "en": "Craft market with pottery, traditional rugs (jarapas) and local products at Plaza La Glorieta in Níjar.",
            "de": "Kunsthandwerksmarkt mit Keramik, traditionellen Teppichen (jarapas) und regionalen Produkten am Plaza La Glorieta in Níjar.",
            "fr": "Marché artisanal avec poterie, tapis traditionnels (jarapas) et produits locaux à Plaza La Glorieta de Níjar.",
        },
        "direccion": "Plaza La Glorieta, Níjar",
        "organizador": "Asociación de Artesanos de Níjar",
        "precio": "Entrada libre",
        "etiquetas": ["artesania", "ceramica", "mercado"],
        "delta_dias": 6,
        "hora_inicio": 10,
        "duracion_h": 5,
    },
    {
        "urn": "urn:ngsi-ld:EventoTuristico:nijar:cine-aire-libre",
        "nombre": "Cine al aire libre — Cortometrajes",
        "tipo": "cultural",
        "descripcion": "Proyección de cortometrajes del Festival Cortos en Femenino en el Centro de Visitantes. Entrada gratuita.",
        "nombre_i18n": {
            "es": "Cine al aire libre — Cortometrajes",
            "en": "Open-air cinema — Short films",
            "de": "Freiluftkino — Kurzfilme",
            "fr": "Cinéma en plein air — Courts-métrages",
        },
        "descripcion_i18n": {
            "es": "Proyección de cortometrajes del Festival Cortos en Femenino en el Centro de Visitantes. Entrada gratuita.",
            "en": "Screening of short films from the Cortos en Femenino festival at the Visitors Centre. Free admission.",
            "de": "Vorführung von Kurzfilmen des Festivals Cortos en Femenino im Besucherzentrum. Eintritt frei.",
            "fr": "Projection de courts-métrages du festival Cortos en Femenino au Centre des visiteurs. Entrée libre.",
        },
        "direccion": "Centro de Visitantes Las Amoladeras",
        "organizador": "Ayuntamiento de Níjar",
        "precio": "Gratuito",
        "capacidad_aforo": 80,
        "etiquetas": ["cine", "cultura", "gratis", "nocturno"],
        "delta_dias": 6,
        "hora_inicio": 21,
        "duracion_h": 2,
    },
    {
        "urn": "urn:ngsi-ld:EventoTuristico:nijar:taller-fotografia",
        "nombre": "Taller de fotografía de paisaje",
        "tipo": "educativo",
        "descripcion": "Taller práctico de fotografía de paisaje volcánico y costero. Nivel intermedio. Punto de encuentro en el Mirador de la Amatista.",
        "nombre_i18n": {
            "es": "Taller de fotografía de paisaje",
            "en": "Landscape photography workshop",
            "de": "Workshop Landschaftsfotografie",
            "fr": "Atelier de photographie de paysage",
        },
        "descripcion_i18n": {
            "es": "Taller práctico de fotografía de paisaje volcánico y costero. Nivel intermedio. Punto de encuentro en el Mirador de la Amatista.",
            "en": "Hands-on workshop on volcanic and coastal landscape photography. Intermediate level. Meeting point at Mirador de la Amatista.",
            "de": "Praktischer Workshop zur Fotografie von Vulkan- und Küstenlandschaften. Mittleres Niveau. Treffpunkt am Aussichtspunkt Amatista.",
            "fr": "Atelier pratique de photographie de paysages volcaniques et côtiers. Niveau intermédiaire. Point de rencontre au Mirador de la Amatista.",
        },
        "direccion": "Mirador de la Amatista, Rodalquilar",
        "organizador": "Club Fotográfico Almería",
        "precio": "15 €",
        "capacidad_aforo": 15,
        "etiquetas": ["fotografia", "taller", "paisaje"],
        "delta_dias": 8,
        "hora_inicio": 17,
        "duracion_h": 3,
    },
    {
        "urn": "urn:ngsi-ld:EventoTuristico:nijar:charla-sostenibilidad",
        "nombre": "Charla: Turismo sostenible en Cabo de Gata",
        "tipo": "educativo",
        "descripcion": "Mesa redonda sobre buenas prácticas de turismo sostenible en espacios naturales protegidos.",
        "nombre_i18n": {
            "es": "Charla: Turismo sostenible en Cabo de Gata",
            "en": "Talk: Sustainable tourism in Cabo de Gata",
            "de": "Vortrag: Nachhaltiger Tourismus in Cabo de Gata",
            "fr": "Conférence : Tourisme durable à Cabo de Gata",
        },
        "descripcion_i18n": {
            "es": "Mesa redonda sobre buenas prácticas de turismo sostenible en espacios naturales protegidos.",
            "en": "Round table on best practices for sustainable tourism in protected natural areas.",
            "de": "Podiumsdiskussion über bewährte Praktiken für nachhaltigen Tourismus in Naturschutzgebieten.",
            "fr": "Table ronde sur les bonnes pratiques du tourisme durable dans les espaces naturels protégés.",
        },
        "direccion": "Sala de actos del Ayuntamiento de Níjar",
        "organizador": "Ayuntamiento de Níjar",
        "precio": "Gratuito",
        "capacidad_aforo": 50,
        "etiquetas": ["sostenibilidad", "charla", "medioambiente"],
        "delta_dias": 2,
        "hora_inicio": 18,
        "duracion_h": 2,
    },
    {
        "urn": "urn:ngsi-ld:EventoTuristico:nijar:kayak-monsul",
        "nombre": "Excursión en kayak — Mónsul a Genoveses",
        "tipo": "deportivo",
        "descripcion": "Travesía en kayak por la costa volcánica entre las playas de Mónsul y Genoveses. Incluye equipo y guía certificado.",
        "nombre_i18n": {
            "es": "Excursión en kayak — Mónsul a Genoveses",
            "en": "Kayak trip — Mónsul to Genoveses",
            "de": "Kajaktour — Mónsul nach Genoveses",
            "fr": "Excursion en kayak — Mónsul à Genoveses",
        },
        "descripcion_i18n": {
            "es": "Travesía en kayak por la costa volcánica entre las playas de Mónsul y Genoveses. Incluye equipo y guía certificado.",
            "en": "Kayak crossing along the volcanic coast between Mónsul and Genoveses beaches. Equipment and certified guide included.",
            "de": "Kajaktour entlang der vulkanischen Küste zwischen den Stränden Mónsul und Genoveses. Ausrüstung und zertifizierter Guide inklusive.",
            "fr": "Traversée en kayak le long de la côte volcanique entre les plages de Mónsul et Genoveses. Équipement et guide certifié inclus.",
        },
        "direccion": "Playa de Mónsul, San José",
        "organizador": "Cabo de Gata Activo",
        "precio": "35 €/persona",
        "capacidad_aforo": 12,
        "etiquetas": ["kayak", "deportivo", "mar", "costa"],
        "delta_dias": 4,
        "hora_inicio": 10,
        "duracion_h": 3,
    },
    {
        "urn": "urn:ngsi-ld:EventoTuristico:nijar:degustacion-vinos",
        "nombre": "Degustación de vinos del desierto",
        "tipo": "gastronomico",
        "descripcion": "Cata comentada de vinos ecológicos producidos en la zona semiárida de Níjar, con maridaje de tapas locales.",
        "nombre_i18n": {
            "es": "Degustación de vinos del desierto",
            "en": "Desert wine tasting",
            "de": "Wüstenweinverkostung",
            "fr": "Dégustation de vins du désert",
        },
        "descripcion_i18n": {
            "es": "Cata comentada de vinos ecológicos producidos en la zona semiárida de Níjar, con maridaje de tapas locales.",
            "en": "Guided tasting of organic wines from Níjar's semi-arid region, paired with local tapas.",
            "de": "Geführte Verkostung von Bio-Weinen aus der halbtrockenen Region Níjar, kombiniert mit lokalen Tapas.",
            "fr": "Dégustation commentée de vins biologiques produits dans la zone semi-aride de Níjar, accompagnés de tapas locales.",
        },
        "direccion": "Bodega Las Albinas, San Isidro",
        "organizador": "Bodega Las Albinas",
        "precio": "20 €",
        "capacidad_aforo": 25,
        "etiquetas": ["vino", "gastronomia", "cata", "ecologico"],
        "delta_dias": 7,
        "hora_inicio": 19,
        "duracion_h": 2,
    },
    {
        "urn": "urn:ngsi-ld:EventoTuristico:nijar:fiesta-san-juan",
        "nombre": "Noche de San Juan en Las Negras",
        "tipo": "festivo",
        "descripcion": "Celebración de la Noche de San Juan en la playa de Las Negras con hoguera, música en vivo y chiringuito.",
        "nombre_i18n": {
            "es": "Noche de San Juan en Las Negras",
            "en": "Saint John's Eve at Las Negras",
            "de": "Johannisnacht in Las Negras",
            "fr": "Nuit de la Saint-Jean à Las Negras",
        },
        "descripcion_i18n": {
            "es": "Celebración de la Noche de San Juan en la playa de Las Negras con hoguera, música en vivo y chiringuito.",
            "en": "Saint John's Eve celebration on Las Negras beach with bonfire, live music and beach bar.",
            "de": "Johannisnacht-Feier am Strand von Las Negras mit Lagerfeuer, Live-Musik und Strandbar.",
            "fr": "Célébration de la nuit de la Saint-Jean sur la plage de Las Negras avec feu de joie, musique live et bar de plage.",
        },
        "direccion": "Playa de Las Negras",
        "organizador": "Ayuntamiento de Níjar",
        "precio": "Gratuito",
        "etiquetas": ["fiesta", "playa", "nocturno", "tradicion"],
        "delta_dias": 10,
        "hora_inicio": 22,
        "duracion_h": 4,
    },
]


def generar_eventos_seed(ref: datetime | None = None) -> list[dict]:
    base = ref or datetime.now(UTC)
    eventos = []
    for ev in _EVENTOS_SEED:
        inicio = base + timedelta(days=ev["delta_dias"])
        inicio = inicio.replace(hour=ev["hora_inicio"], minute=0, second=0, microsecond=0)
        fin = inicio + timedelta(hours=ev["duracion_h"])
        eventos.append(
            {
                "urn": ev["urn"],
                "nombre": ev["nombre"],
                "tipo": ev["tipo"],
                "descripcion": ev.get("descripcion"),
                "nombre_i18n": ev.get("nombre_i18n"),
                "descripcion_i18n": ev.get("descripcion_i18n"),
                "direccion": ev.get("direccion"),
                "organizador": ev.get("organizador"),
                "precio": ev.get("precio"),
                "capacidad_aforo": ev.get("capacidad_aforo"),
                "etiquetas": ev.get("etiquetas"),
                "fecha_inicio": inicio,
                "fecha_fin": fin,
                "publicado": True,
                "activo": True,
            }
        )
    return eventos


def generar_interacciones_chatbot_seed() -> list[dict]:
    interacciones = []
    # Consultas resueltas
    for i in range(_NUM_INTERACCIONES_CHATBOT):
        sample = _CHATBOT_SAMPLES[i % len(_CHATBOT_SAMPLES)]
        intent, idioma, pregunta, respuesta, nivel, score = sample
        interacciones.append(
            {
                "sesion_id": f"demo-session-{i % 30:03d}",
                "canal": random.choice(["web", "web", "app", "totem"]),
                "idioma": idioma,
                "pregunta": pregunta,
                "respuesta": respuesta,
                "intent_detectado": intent,
                "nivel_confianza": nivel,
                "score_confianza": round(score + random.uniform(-0.03, 0.03), 3),
                # ~82 % útil, algo de feedback negativo y sin feedback
                "util": random.choice([True, True, True, True, False, None]),
                "latencia_ms": random.randint(50, 400),
            }
        )
    # Consultas no resueltas (fuera de dominio → derivación a humano)
    for j in range(_NUM_CHATBOT_NO_RESUELTAS):
        idioma, pregunta = _CHATBOT_NO_RESUELTAS[j % len(_CHATBOT_NO_RESUELTAS)]
        derivada = j % 3 == 0
        interacciones.append(
            {
                "sesion_id": f"demo-session-nr-{j % 20:03d}",
                "canal": random.choice(["web", "app", "totem"]),
                "idioma": idioma,
                "pregunta": pregunta,
                "respuesta": (
                    "No dispongo de información suficiente sobre eso. Te derivo con la "
                    "oficina de turismo de Níjar (turismo@nijar.es)."
                    if derivada
                    else "Lo siento, todavía no tengo una respuesta para esa consulta."
                ),
                "intent_detectado": None,
                "nivel_confianza": "fuera_de_dominio",
                "score_confianza": round(random.uniform(0.1, 0.45), 3),
                "util": random.choice([False, False, None]),
                "comentario": "derivada_a_humano" if derivada else "pregunta_no_cubierta",
                "latencia_ms": random.randint(60, 500),
            }
        )
    return interacciones


# ---------- Incidencias del mantenimiento (mes natural anterior) ----------


def _mes_anterior(ref: datetime) -> tuple[datetime, datetime]:
    """Devuelve (inicio, fin) del último mes natural completo respecto a ``ref``."""
    primero_actual = ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    fin = primero_actual
    ultimo_mes = primero_actual - timedelta(days=1)
    inicio = ultimo_mes.replace(day=1)
    return inicio, fin


def generar_incidencias_seed() -> list[dict]:
    """Incidencias y acciones preventivas realistas del mes natural anterior.

    Pensadas para que el informe mensual del C.1 muestre cifras coherentes:
    disponibilidad alta (>=99 %), cumplimiento ANS mayoritario con algún caso
    de incumplimiento, acciones preventivas y un evento de seguridad contenido.
    """
    inicio, _ = _mes_anterior(_NOW)

    def en(dia: int, hora: int = 9) -> datetime:
        return inicio + timedelta(days=dia - 1, hours=hora)

    incidencias = [
        # Crítica resuelta dentro de ANS (respuesta <1h, resolución <8h)
        {
            "severidad": "critica",
            "titulo": "Caída temporal de la API de la plataforma",
            "componente": "plataforma",
            "origen": "monitorizacion",
            "descripcion": "Errores 5xx por saturación de conexiones a BBDD durante un pico.",
            "detectada_en": en(6, 11),
            "respondida_en": en(6, 11) + timedelta(minutes=25),
            "resuelta_en": en(6, 11) + timedelta(hours=3, minutes=40),
            "estado": "resuelta",
            "afecta_disponibilidad": True,
            "incidente_confirmado": False,
        },
        # Alta resuelta en ANS
        {
            "severidad": "alta",
            "titulo": "Tótem de Rodalquilar sin conexión",
            "componente": "totem_1",
            "origen": "monitorizacion",
            "descripcion": "Pérdida de enlace 4G; conmutación a modo local degradado.",
            "detectada_en": en(12, 8),
            "respondida_en": en(12, 8) + timedelta(hours=1),
            "resuelta_en": en(12, 8) + timedelta(hours=6),
            "estado": "resuelta",
            "afecta_disponibilidad": True,
        },
        # Alta que INCUMPLE resolución (para mostrar cumplimiento <100 %)
        {
            "severidad": "alta",
            "titulo": "Retraso en sincronización del CMS al tótem",
            "componente": "totem_2",
            "origen": "usuario",
            "descripcion": "Contenido publicado tardó en propagarse por incidencia en caché.",
            "detectada_en": en(18, 17),
            "respondida_en": en(18, 17) + timedelta(hours=2),
            "resuelta_en": en(18, 17) + timedelta(hours=20),
            "estado": "resuelta",
            "afecta_disponibilidad": True,
        },
        # Media resuelta
        {
            "severidad": "media",
            "titulo": "Sensor de ruido con lecturas erráticas",
            "componente": "smart_office",
            "origen": "monitorizacion",
            "descripcion": "Calibración desviada; sustituido y recalibrado.",
            "detectada_en": en(9, 10),
            "respondida_en": en(9, 12),
            "resuelta_en": en(10, 10),
            "estado": "resuelta",
            "afecta_disponibilidad": False,
        },
        # Baja resuelta
        {
            "severidad": "baja",
            "titulo": "Ajuste de copy en una FAQ del chatbot",
            "componente": "chatbot",
            "origen": "ticketing",
            "descripcion": "Corrección menor de redacción en respuesta de horarios.",
            "detectada_en": en(22, 9),
            "respondida_en": en(22, 15),
            "resuelta_en": en(23, 12),
            "estado": "resuelta",
            "afecta_disponibilidad": False,
        },
        # Evento de seguridad contenido (WAF), confirmado, sin impacto
        {
            "severidad": "alta",
            "titulo": "Intento de inyección bloqueado por WAF",
            "componente": "plataforma",
            "origen": "monitorizacion",
            "descripcion": "Patrón SQLi bloqueado por el WAF; sin acceso a datos.",
            "detectada_en": en(15, 3),
            "respondida_en": en(15, 3) + timedelta(minutes=20),
            "resuelta_en": en(15, 3) + timedelta(hours=2),
            "estado": "resuelta",
            "afecta_disponibilidad": False,
            "es_evento_seguridad": True,
            "incidente_confirmado": True,
        },
        # Acciones preventivas ejecutadas
        {
            "severidad": "baja",
            "titulo": "Patching mensual en ventana nocturna",
            "componente": "plataforma",
            "origen": "preventivo",
            "descripcion": "Actualización de dependencias con verificación de regresión.",
            "detectada_en": en(2, 2),
            "respondida_en": en(2, 2),
            "resuelta_en": en(2, 4),
            "estado": "resuelta",
            "afecta_disponibilidad": False,
            "es_preventiva": True,
        },
        {
            "severidad": "baja",
            "titulo": "Inspección de tótems (protocolo costero)",
            "componente": "totem_1",
            "origen": "preventivo",
            "descripcion": "Revisión de juntas IP65, filtros y brillo; sin incidencias.",
            "detectada_en": en(20, 9),
            "respondida_en": en(20, 9),
            "resuelta_en": en(20, 13),
            "estado": "resuelta",
            "afecta_disponibilidad": False,
            "es_preventiva": True,
        },
    ]
    return incidencias


# ---------- Analítica web/app "Vive Níjar" y movilidad (últimos 30 días) ----------

# Origen geográfico (procedencia del visitante) con peso aproximado.
_ORIGENES = [
    ("ES", "Almería", 0.28),
    ("ES", "Madrid", 0.14),
    ("ES", "Granada", 0.08),
    ("ES", "Barcelona", 0.07),
    ("GB", "Londres", 0.09),
    ("DE", "Múnich", 0.08),
    ("FR", "París", 0.07),
    ("NL", "Ámsterdam", 0.05),
    ("BE", "Bruselas", 0.03),
    ("IT", "Milán", 0.03),
    ("US", "Nueva York", 0.02),
]
_DISPOSITIVOS = [("movil", 0.68), ("escritorio", 0.22), ("tablet", 0.10)]
_PANTALLAS_WEB = [
    "inicio",
    "playas",
    "rutas",
    "eventos",
    "mapa",
    "recurso-detalle",
    "servicios",
    "como-llegar",
    "chatbot",
    "buscador",
]
_BUSQUEDAS = [
    "mónsul aparcamiento",
    "rutas senderismo",
    "playas nudistas",
    "san josé restaurantes",
    "cabo de gata mapa",
    "eventos julio",
    "cala de enmedio",
    "rodalquilar mina",
    "horario oficina turismo",
    "alojamiento rural",
]
_IDIOMAS_APP = [("es", 0.55), ("en", 0.22), ("de", 0.12), ("fr", 0.11)]


def _elegir_pesado(opciones: list[tuple]) -> tuple:
    """Elige una tupla (…, peso) según su peso (último elemento)."""
    r = random.random()
    acum = 0.0
    for op in opciones:
        acum += op[-1]
        if r <= acum:
            return op
    return opciones[-1]


_NUM_VISITAS_WEB = 260
_NUM_VISITAS_APP = 140
_NUM_CONEXIONES_WIFI = 90
_NUM_PROXIMIDAD_BLE = 70


def generar_visitas_web_app_seed(recursos_ids: list[str] | None = None) -> list[dict]:
    """Genera visitas web/app, conexiones WiFi y detecciones BLE (anonimizadas).

    Alimenta los KPIs del pliego de uso de web/app (usuarios, sesiones, páginas
    vistas, origen, idioma, dispositivo, rebote, búsquedas, errores) y de
    movilidad/afluencia (WiFi único, proximidad a POIs).

    Args:
        recursos_ids: lista de UUID (str) de recursos para asociar algunas
            visitas a POIs concretos.
    """
    recursos_ids = recursos_ids or []
    visitas: list[dict] = []

    def _hash(n: int) -> str:
        return hashlib.sha256(f"visitor-web-{n}".encode()).hexdigest()

    # Web (páginas vistas, sesiones, rebote, errores, búsquedas)
    for i in range(_NUM_VISITAS_WEB):
        dias = random.randint(0, 30)
        ts = _NOW - timedelta(days=dias, hours=random.randint(6, 23), minutes=random.randint(0, 59))
        pais, ciudad, _ = _elegir_pesado(_ORIGENES)
        disp, _ = _elegir_pesado(_DISPOSITIVOS)
        idioma, _ = _elegir_pesado(_IDIOMAS_APP)
        pantalla = random.choice(_PANTALLAS_WEB)
        atributos = {
            "pantalla": pantalla,
            "dispositivo": disp,
            "pais": pais,
            "ciudad": ciudad,
            "duracion_seg": random.randint(5, 480),
            "rebote": random.random() < 0.34,  # tasa de rebote ~34 %
            "error": random.random() < 0.02,  # 2 % errores técnicos (SLA)
        }
        if random.random() < 0.25:
            atributos["busqueda"] = random.choice(_BUSQUEDAS)
        if pantalla == "recurso-detalle" and recursos_ids:
            recurso_id = random.choice(recursos_ids)
        else:
            recurso_id = None
        visitas.append(
            {
                "tipo": "web_vista",
                "ocurrido_en": ts,
                "visitante_hash": _hash(i % 130),
                "recurso_id": recurso_id,
                "idioma": idioma,
                "canal": "web",
                "atributos": atributos,
            }
        )

    # App Vive Níjar (pantallas, clics en rutas/POIs, descargas de mapas)
    eventos_app = [
        "ver_ruta",
        "abrir_mapa",
        "descargar_mapa",
        "clic_poi",
        "ver_evento",
        "abrir_chatbot",
    ]
    for i in range(_NUM_VISITAS_APP):
        dias = random.randint(0, 30)
        ts = _NOW - timedelta(days=dias, hours=random.randint(7, 22), minutes=random.randint(0, 59))
        pais, ciudad, _ = _elegir_pesado(_ORIGENES)
        idioma, _ = _elegir_pesado(_IDIOMAS_APP)
        recurso_id = random.choice(recursos_ids) if recursos_ids and random.random() < 0.6 else None
        visitas.append(
            {
                "tipo": "app_vista",
                "ocurrido_en": ts,
                "visitante_hash": _hash(1000 + i % 80),
                "recurso_id": recurso_id,
                "idioma": idioma,
                "canal": "app",
                "atributos": {
                    "evento": random.choice(eventos_app),
                    "dispositivo": random.choice(["movil", "tablet"]),
                    "pais": pais,
                    "ciudad": ciudad,
                    "duracion_seg": random.randint(10, 360),
                },
            }
        )

    # WiFi público (dispositivos únicos diarios — afluencia aproximada)
    for i in range(_NUM_CONEXIONES_WIFI):
        dias = random.randint(0, 30)
        ts = _NOW - timedelta(days=dias, hours=random.randint(9, 21), minutes=random.randint(0, 59))
        visitas.append(
            {
                "tipo": "wifi_conexion",
                "ocurrido_en": ts,
                "visitante_hash": _hash(2000 + i % 60),
                "canal": "wifi_plaza_glorieta",
                "idioma": None,
                "atributos": {
                    "tiempo_conexion_seg": random.randint(120, 5400),
                    "zona": "plaza_glorieta",
                },
            }
        )

    # Proximidad BLE (beacons en POIs — visitas a puntos de interés)
    for i in range(_NUM_PROXIMIDAD_BLE):
        dias = random.randint(0, 30)
        ts = _NOW - timedelta(days=dias, hours=random.randint(9, 20), minutes=random.randint(0, 59))
        recurso_id = random.choice(recursos_ids) if recursos_ids else None
        visitas.append(
            {
                "tipo": "proximidad_ble",
                "ocurrido_en": ts,
                "visitante_hash": _hash(3000 + i % 50),
                "recurso_id": recurso_id,
                "canal": "beacon",
                "idioma": None,
                "atributos": {
                    "permanencia_seg": random.randint(30, 1800),
                    "rssi": random.randint(-90, -55),
                },
            }
        )

    return visitas


# ---------- Contenidos del CMS con ciclo editorial (KPI tiempo de publicación) ----------

_CONTENIDOS_SEED = [
    {
        "titulo": "Guía de playas vírgenes de Cabo de Gata",
        "cuerpo": "Recorrido por las calas y playas más singulares del Parque Natural: Mónsul, "
        "Genoveses, Cala de Enmedio y el Playazo de Rodalquilar, con consejos de acceso "
        "responsable y aforo.",
        "canales": ["web", "app", "totem"],
        "etiquetas": ["playas", "guia", "naturaleza"],
        "estado": "publicado",
        "delta_creado_dias": 20,
        "horas_a_aprobacion": 30,
        "horas_aprob_a_pub": 6,
    },
    {
        "titulo": "Rutas de senderismo para el otoño",
        "cuerpo": "Selección de senderos de dificultad baja y media ideales para los meses de "
        "temporada media, con desniveles, duración y puntos de interés.",
        "canales": ["web", "app"],
        "etiquetas": ["rutas", "senderismo", "otono"],
        "estado": "publicado",
        "delta_creado_dias": 14,
        "horas_a_aprobacion": 18,
        "horas_aprob_a_pub": 20,
    },
    {
        "titulo": "La artesanía de Níjar: cerámica y jarapas",
        "cuerpo": "Historia y talleres vivos de la cerámica nijareña y las jarapas, un textil "
        "tradicional tejido a mano en el casco histórico.",
        "canales": ["web", "totem"],
        "etiquetas": ["artesania", "cultura", "compras"],
        "estado": "publicado",
        "delta_creado_dias": 10,
        "horas_a_aprobacion": 40,
        "horas_aprob_a_pub": 12,
    },
    {
        "titulo": "Agenda de eventos del verano",
        "cuerpo": "Conciertos, mercados artesanales, cine al aire libre y actividades náuticas "
        "programadas para la temporada estival.",
        "canales": ["web", "app", "totem"],
        "etiquetas": ["eventos", "agenda", "verano"],
        "estado": "programado",
        "delta_creado_dias": 5,
        "horas_a_aprobacion": 10,
        "horas_aprob_a_pub": None,
    },
    {
        "titulo": "Consejos de turismo sostenible en el Parque Natural",
        "cuerpo": "Buenas prácticas para disfrutar del espacio protegido: gestión de residuos, "
        "respeto a la fauna y uso del transporte público.",
        "canales": ["web", "app"],
        "etiquetas": ["sostenibilidad", "parque", "concienciacion"],
        "estado": "aprobado",
        "delta_creado_dias": 3,
        "horas_a_aprobacion": 22,
        "horas_aprob_a_pub": None,
    },
    {
        "titulo": "Astroturismo: cielos de Cabo de Gata",
        "cuerpo": "Los mejores miradores para la observación de estrellas y consejos para la "
        "fotografía nocturna en el Parque Natural.",
        "canales": ["web"],
        "etiquetas": ["astroturismo", "naturaleza", "fotografia"],
        "estado": "pendiente_aprobacion",
        "delta_creado_dias": 2,
        "horas_a_aprobacion": None,
        "horas_aprob_a_pub": None,
    },
    {
        "titulo": "Gastronomía del mar: recetas de Níjar",
        "cuerpo": "Borrador sobre platos típicos de pescado y marisco, gurullos y ajoblanco de "
        "la cocina local. Pendiente de completar imágenes.",
        "canales": ["web", "app"],
        "etiquetas": ["gastronomia", "cultura"],
        "estado": "borrador",
        "delta_creado_dias": 1,
        "horas_a_aprobacion": None,
        "horas_aprob_a_pub": None,
    },
    {
        "titulo": "Campaña Primavera 2026 (cerrada)",
        "cuerpo": "Contenido de la campaña de primavera ya finalizada, archivado para consulta "
        "histórica y trazabilidad.",
        "canales": ["web", "app"],
        "etiquetas": ["primavera", "campana", "archivo"],
        "estado": "archivado",
        "delta_creado_dias": 110,
        "horas_a_aprobacion": 24,
        "horas_aprob_a_pub": 8,
    },
]


def generar_contenidos_seed(recursos_ids: list[str] | None = None) -> list[dict]:
    """Genera piezas de contenido del CMS en distintos estados del flujo editorial.

    Incluye ``fecha_aprobacion`` y ``fecha_publicacion`` para poder medir el KPI
    del pliego "tiempo de publicación de contenidos" (≤ 24 h desde la aprobación).
    """
    recursos_ids = recursos_ids or []
    contenidos = []
    for i, c in enumerate(_CONTENIDOS_SEED):
        creado = _NOW - timedelta(days=c["delta_creado_dias"])
        fecha_aprobacion = None
        fecha_publicacion = None
        publicar_desde = None
        if c["horas_a_aprobacion"] is not None:
            fecha_aprobacion = creado + timedelta(hours=c["horas_a_aprobacion"])
        if fecha_aprobacion is not None and c["horas_aprob_a_pub"] is not None:
            fecha_publicacion = fecha_aprobacion + timedelta(hours=c["horas_aprob_a_pub"])
            publicar_desde = fecha_publicacion
        if c["estado"] == "programado":
            # Programado a futuro
            publicar_desde = _NOW + timedelta(days=random.randint(2, 10))
        contenidos.append(
            {
                "titulo": c["titulo"],
                "cuerpo": c["cuerpo"],
                "canales": c["canales"],
                "etiquetas": c["etiquetas"],
                "estado": c["estado"],
                "recurso_id": (recursos_ids[i % len(recursos_ids)] if recursos_ids else None),
                "fecha_aprobacion": fecha_aprobacion,
                "fecha_publicacion": fecha_publicacion,
                "publicar_desde": publicar_desde,
            }
        )
    return contenidos
