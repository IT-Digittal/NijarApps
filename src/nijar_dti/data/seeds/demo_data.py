"""Datos de demostración para poblar los dashboards.

Genera observaciones IoT, opiniones de social listening,
interacciones de tótems y sesiones de chatbot para que el
dashboard muestre datos realistas sin necesidad de workers activos.
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone

# ---------- Observaciones IoT (últimas 48h, cada 15 min) ----------

_NOW = datetime.now(timezone.utc)
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
            observaciones.append({
                "sensor_id": sensor_id,
                "observado_en": ts,
                "valor": round(valor_actual, 2),
                "unidades": unidades,
                "valido": True,
            })
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
]

_NUM_OPINIONES = 60


def generar_opiniones_seed() -> list[dict]:
    opiniones = []
    for i in range(_NUM_OPINIONES):
        tmpl = _OPINION_TEMPLATES[i % len(_OPINION_TEMPLATES)]
        dias_atras = random.randint(0, 30)
        horas_atras = random.randint(0, 23)
        ts = _NOW - timedelta(days=dias_atras, hours=horas_atras)
        opiniones.append({
            "fuente": tmpl["fuente"],
            "fuente_id_externo": f"demo-{i:04d}",
            "texto_original": tmpl["texto"],
            "publicado_en": ts,
            "idioma": tmpl["idioma"],
            "sentimiento": tmpl["sentimiento"],
            "score_sentimiento": tmpl["score"] + random.uniform(-0.05, 0.05),
            "temas": tmpl["temas"],
            "autor_handle": f"@demo_user_{i % 20}",
            "capturado_en": ts + timedelta(minutes=random.randint(1, 30)),
        })
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
        visitas.append({
            "tipo": "interaccion_totem",
            "ocurrido_en": ts,
            "visitante_hash": hashlib.sha256(f"visitor-{i % 40}".encode()).hexdigest(),
            "idioma": random.choice(["es", "en", "de", "fr"]),
            "canal": random.choice(["totem_rodalquilar", "totem_albaricoques"]),
            "atributos": {
                "seccion": random.choice(_SECCIONES_TOTEM),
                "duracion_seg": random.randint(15, 180),
            },
        })
    return visitas


# ---------- Interacciones de chatbot (últimos 14 días) ----------

_CHATBOT_SAMPLES = [
    ("playas_destacadas", "es", "¿Cuáles son las mejores playas?", "Las playas más conocidas son: Mónsul, Genoveses, Playazo y Cala de Enmedio.", "alta", 0.92),
    ("acceso_playa_monsul", "es", "¿Cómo llego a Mónsul en verano?", "Durante la temporada alta el acceso está regulado por aforo.", "alta", 0.88),
    ("ruta_rodalquilar_albaricoques", "en", "Tell me about the cycling route", "An 8.5 km route of low-medium difficulty connecting Rodalquilar with Los Albaricoques.", "alta", 0.85),
    ("donde_comer", "es", "¿Dónde puedo comer bien?", "La gastronomía local se basa en pescado fresco, gurullos y ajoblanco.", "alta", 0.90),
    ("emergencias", "de", "Notrufnummer?", "Die Notrufnummer in Spanien ist 112.", "alta", 0.95),
    ("mejor_epoca_visita", "fr", "Meilleure période pour visiter?", "Le printemps et l'automne sont idéaux.", "alta", 0.87),
    ("saludo", "es", "Hola, buenos días", "¡Hola! Soy el asistente turístico de Níjar.", "alta", 0.99),
    ("artesania_jarapas", "en", "What are jarapas?", "The jarapa is a traditional handcrafted textile from Níjar.", "alta", 0.83),
    ("horario_amoladeras", "es", "¿Horario del centro de visitantes?", "El Centro de Visitantes Las Amoladeras abre de 10:00 a 14:00.", "media", 0.72),
    ("normativa_parque", "es", "¿Qué está prohibido en el parque?", "Está prohibido hacer fuego, acampar fuera de zonas habilitadas...", "alta", 0.91),
]

_NUM_INTERACCIONES_CHATBOT = 45


# ---------- Eventos turísticos (próximas 2 semanas) ----------

_EVENTOS_SEED = [
    {
        "urn": "urn:ngsi-ld:EventoTuristico:nijar:concierto-salinas",
        "nombre": "Concierto Noche de las Salinas",
        "tipo": "musical",
        "descripcion": "Concierto de flamenco fusión al aire libre en el entorno de las antiguas salinas de Cabo de Gata. Entrada gratuita.",
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
        "direccion": "Playa de Las Negras",
        "organizador": "Ayuntamiento de Níjar",
        "precio": "Gratuito",
        "etiquetas": ["fiesta", "playa", "nocturno", "tradicion"],
        "delta_dias": 10,
        "hora_inicio": 22,
        "duracion_h": 4,
    },
]


def generar_eventos_seed() -> list[dict]:
    eventos = []
    for ev in _EVENTOS_SEED:
        inicio = _NOW + timedelta(days=ev["delta_dias"])
        inicio = inicio.replace(hour=ev["hora_inicio"], minute=0, second=0, microsecond=0)
        fin = inicio + timedelta(hours=ev["duracion_h"])
        eventos.append({
            "urn": ev["urn"],
            "nombre": ev["nombre"],
            "tipo": ev["tipo"],
            "descripcion": ev.get("descripcion"),
            "direccion": ev.get("direccion"),
            "organizador": ev.get("organizador"),
            "precio": ev.get("precio"),
            "capacidad_aforo": ev.get("capacidad_aforo"),
            "etiquetas": ev.get("etiquetas"),
            "fecha_inicio": inicio,
            "fecha_fin": fin,
            "publicado": True,
            "activo": True,
        })
    return eventos


def generar_interacciones_chatbot_seed() -> list[dict]:
    interacciones = []
    for i in range(_NUM_INTERACCIONES_CHATBOT):
        sample = _CHATBOT_SAMPLES[i % len(_CHATBOT_SAMPLES)]
        intent, idioma, pregunta, respuesta, nivel, score = sample
        dias_atras = random.randint(0, 14)
        ts = _NOW - timedelta(days=dias_atras, hours=random.randint(0, 23))
        interacciones.append({
            "sesion_id": f"demo-session-{i % 25:03d}",
            "canal": random.choice(["web", "totem"]),
            "idioma": idioma,
            "pregunta": pregunta,
            "respuesta": respuesta,
            "intent_detectado": intent,
            "nivel_confianza": nivel,
            "score_confianza": score + random.uniform(-0.03, 0.03),
            "util": random.choice([True, True, True, None]),  # 75% positivo
            "latencia_ms": random.randint(50, 400),
        })
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
            "severidad": "critica", "titulo": "Caída temporal de la API de la plataforma",
            "componente": "plataforma", "origen": "monitorizacion",
            "descripcion": "Errores 5xx por saturación de conexiones a BBDD durante un pico.",
            "detectada_en": en(6, 11), "respondida_en": en(6, 11) + timedelta(minutes=25),
            "resuelta_en": en(6, 11) + timedelta(hours=3, minutes=40),
            "estado": "resuelta", "afecta_disponibilidad": True, "incidente_confirmado": False,
        },
        # Alta resuelta en ANS
        {
            "severidad": "alta", "titulo": "Tótem de Rodalquilar sin conexión",
            "componente": "totem_1", "origen": "monitorizacion",
            "descripcion": "Pérdida de enlace 4G; conmutación a modo local degradado.",
            "detectada_en": en(12, 8), "respondida_en": en(12, 8) + timedelta(hours=1),
            "resuelta_en": en(12, 8) + timedelta(hours=6),
            "estado": "resuelta", "afecta_disponibilidad": True,
        },
        # Alta que INCUMPLE resolución (para mostrar cumplimiento <100 %)
        {
            "severidad": "alta", "titulo": "Retraso en sincronización del CMS al tótem",
            "componente": "totem_2", "origen": "usuario",
            "descripcion": "Contenido publicado tardó en propagarse por incidencia en caché.",
            "detectada_en": en(18, 17), "respondida_en": en(18, 17) + timedelta(hours=2),
            "resuelta_en": en(18, 17) + timedelta(hours=20),
            "estado": "resuelta", "afecta_disponibilidad": True,
        },
        # Media resuelta
        {
            "severidad": "media", "titulo": "Sensor de ruido con lecturas erráticas",
            "componente": "smart_office", "origen": "monitorizacion",
            "descripcion": "Calibración desviada; sustituido y recalibrado.",
            "detectada_en": en(9, 10), "respondida_en": en(9, 12),
            "resuelta_en": en(10, 10), "estado": "resuelta", "afecta_disponibilidad": False,
        },
        # Baja resuelta
        {
            "severidad": "baja", "titulo": "Ajuste de copy en una FAQ del chatbot",
            "componente": "chatbot", "origen": "ticketing",
            "descripcion": "Corrección menor de redacción en respuesta de horarios.",
            "detectada_en": en(22, 9), "respondida_en": en(22, 15),
            "resuelta_en": en(23, 12), "estado": "resuelta", "afecta_disponibilidad": False,
        },
        # Evento de seguridad contenido (WAF), confirmado, sin impacto
        {
            "severidad": "alta", "titulo": "Intento de inyección bloqueado por WAF",
            "componente": "plataforma", "origen": "monitorizacion",
            "descripcion": "Patrón SQLi bloqueado por el WAF; sin acceso a datos.",
            "detectada_en": en(15, 3), "respondida_en": en(15, 3) + timedelta(minutes=20),
            "resuelta_en": en(15, 3) + timedelta(hours=2),
            "estado": "resuelta", "afecta_disponibilidad": False,
            "es_evento_seguridad": True, "incidente_confirmado": True,
        },
        # Acciones preventivas ejecutadas
        {
            "severidad": "baja", "titulo": "Patching mensual en ventana nocturna",
            "componente": "plataforma", "origen": "preventivo",
            "descripcion": "Actualización de dependencias con verificación de regresión.",
            "detectada_en": en(2, 2), "respondida_en": en(2, 2),
            "resuelta_en": en(2, 4), "estado": "resuelta",
            "afecta_disponibilidad": False, "es_preventiva": True,
        },
        {
            "severidad": "baja", "titulo": "Inspección de tótems (protocolo costero)",
            "componente": "totem_1", "origen": "preventivo",
            "descripcion": "Revisión de juntas IP65, filtros y brillo; sin incidencias.",
            "detectada_en": en(20, 9), "respondida_en": en(20, 9),
            "resuelta_en": en(20, 13), "estado": "resuelta",
            "afecta_disponibilidad": False, "es_preventiva": True,
        },
    ]
    return incidencias
