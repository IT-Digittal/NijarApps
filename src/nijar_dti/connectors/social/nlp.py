"""Motor NLP ligero para Social Listening.

Funciones:

- ``detectar_idioma``: detección heurística por frecuencia de stop-words.
- ``analizar_sentimiento``: scoring por lexicón multilingüe (pos/neg) con
  manejo de negación. Devuelve etiqueta y score continuo en [-1, +1].
- ``extraer_temas``: detecta etiquetas temáticas predefinidas según
  vocabulario controlado del destino.
- ``detectar_entidades``: relaciona la mención con URNs FIWARE de los
  recursos turísticos conocidos.

Todo en memoria, sin dependencias pesadas. En el Hito 2 se sustituirá por
modelos ML pre-entrenados (HuggingFace) si se requiere mayor precisión.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# ---------------- detección de idioma ----------------
# Conjuntos pequeños de palabras muy frecuentes y exclusivas de cada idioma.

_LANG_MARKERS: dict[str, set[str]] = {
    "es": {
        "el",
        "la",
        "los",
        "las",
        "de",
        "y",
        "es",
        "un",
        "una",
        "con",
        "por",
        "en",
        "para",
        "que",
        "más",
        "muy",
        "pero",
        "cómo",
        "dónde",
        "están",
        "está",
        "aquí",
        "playa",
        "ruta",
        "fiesta",
        "gracias",
        "hola",
        "mucho",
        "mejor",
        "todo",
    },
    "en": {
        "the",
        "and",
        "is",
        "are",
        "this",
        "that",
        "with",
        "very",
        "good",
        "great",
        "best",
        "amazing",
        "beach",
        "route",
        "please",
        "thanks",
        "hello",
        "you",
        "we",
        "they",
        "incredible",
        "beautiful",
        "love",
        "worth",
    },
    "de": {
        "der",
        "die",
        "das",
        "und",
        "ist",
        "sind",
        "mit",
        "sehr",
        "gut",
        "toll",
        "schön",
        "strand",
        "wanderung",
        "danke",
        "hallo",
        "wir",
        "ihr",
        "sie",
        "wirklich",
        "wahnsinn",
        "wunderschön",
        "besten",
    },
    "fr": {
        "le",
        "la",
        "les",
        "et",
        "est",
        "sont",
        "avec",
        "très",
        "bon",
        "magnifique",
        "incroyable",
        "plage",
        "randonnée",
        "merci",
        "bonjour",
        "nous",
        "vous",
        "ils",
        "elles",
        "superbe",
        "recommande",
    },
}


def _normalizar(texto: str) -> str:
    texto = texto.lower()
    nf = unicodedata.normalize("NFD", texto)
    return "".join(c for c in nf if unicodedata.category(c) != "Mn")


_TOKEN_RE = re.compile(r"[a-záéíóúñçàèìòùâêîôûäöüß']+", re.IGNORECASE)


def _tokens(texto: str) -> list[str]:
    return _TOKEN_RE.findall(texto.lower())


def detectar_idioma(texto: str, default: str = "es") -> str:
    """Heurística simple por presencia de stop-words. Suficiente para
    redirigir el análisis al lexicón correcto."""
    if not texto.strip():
        return default
    tokens_norm = {_normalizar(t) for t in _tokens(texto)}
    if not tokens_norm:
        return default
    scores: dict[str, int] = {}
    for lang, marcas in _LANG_MARKERS.items():
        marcas_norm = {_normalizar(m) for m in marcas}
        scores[lang] = len(tokens_norm & marcas_norm)
    mejor_lang = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[mejor_lang] == 0:
        return default
    return mejor_lang


# ---------------- lexicón de sentimiento ----------------

_POS: dict[str, set[str]] = {
    "es": {
        "bueno",
        "buena",
        "buenos",
        "buenas",
        "excelente",
        "increíble",
        "maravilloso",
        "espectacular",
        "precioso",
        "preciosa",
        "fantástico",
        "genial",
        "mágico",
        "mágica",
        "amable",
        "limpio",
        "tranquilo",
        "recomiendo",
        "recomendable",
        "encanta",
        "encantado",
        "encantada",
        "perfecto",
        "perfecta",
        "único",
        "única",
        "top",
        "mejor",
        "ideal",
        "delicioso",
        "cómodo",
        "cómoda",
        "feliz",
        "disfrutar",
        "divertido",
        "divertida",
    },
    "en": {
        "good",
        "great",
        "excellent",
        "amazing",
        "wonderful",
        "awesome",
        "beautiful",
        "stunning",
        "perfect",
        "best",
        "incredible",
        "fantastic",
        "love",
        "loved",
        "lovely",
        "worth",
        "clean",
        "calm",
        "recommend",
        "unforgettable",
        "magical",
        "delicious",
        "happy",
        "enjoyed",
        "fun",
        "top",
        "unique",
    },
    "de": {
        "gut",
        "sehr",
        "toll",
        "wunderbar",
        "wahnsinn",
        "wahnsinnig",
        "schön",
        "schönste",
        "perfekt",
        "beste",
        "unglaublich",
        "fantastisch",
        "liebe",
        "empfehlen",
        "empfehlung",
        "magisch",
        "sauber",
        "ruhig",
        "glücklich",
        "genießen",
        "top",
        "einzigartig",
    },
    "fr": {
        "bon",
        "bonne",
        "excellent",
        "excellente",
        "superbe",
        "magnifique",
        "incroyable",
        "fantastique",
        "parfait",
        "parfaite",
        "meilleur",
        "meilleure",
        "adore",
        "adoré",
        "recommande",
        "unique",
        "propre",
        "tranquille",
        "heureux",
        "heureuse",
        "délicieux",
        "amusant",
        "amusante",
    },
}

_NEG: dict[str, set[str]] = {
    "es": {
        "malo",
        "mala",
        "malos",
        "malas",
        "horrible",
        "feo",
        "fea",
        "sucio",
        "sucia",
        "decepción",
        "decepcionante",
        "peor",
        "caro",
        "cara",
        "carísimo",
        "ruidoso",
        "ruidosa",
        "masificado",
        "masificada",
        "saturado",
        "saturada",
        "tarde",
        "esperar",
        "desastre",
        "estafa",
        "aburrido",
        "aburrida",
        "problema",
        "problemas",
        "triste",
        "frío",
        "frías",
    },
    "en": {
        "bad",
        "horrible",
        "terrible",
        "awful",
        "worst",
        "dirty",
        "disappointed",
        "disappointing",
        "expensive",
        "crowded",
        "overcrowded",
        "noisy",
        "disaster",
        "scam",
        "boring",
        "problem",
        "problems",
        "sad",
        "cold",
        "late",
        "waste",
        "ugly",
    },
    "de": {
        "schlecht",
        "schlimm",
        "furchtbar",
        "schrecklich",
        "dreckig",
        "schmutzig",
        "enttäuscht",
        "enttäuschend",
        "teuer",
        "überfüllt",
        "laut",
        "langweilig",
        "katastrophe",
        "problem",
        "traurig",
        "kalt",
        "spät",
        "hässlich",
    },
    "fr": {
        "mauvais",
        "mauvaise",
        "horrible",
        "terrible",
        "sale",
        "déçu",
        "décevant",
        "cher",
        "chère",
        "bondé",
        "bondée",
        "bruyant",
        "bruyante",
        "ennuyeux",
        "ennuyeuse",
        "désastre",
        "arnaque",
        "problème",
        "triste",
        "froid",
        "froide",
        "tard",
        "laid",
    },
}

# Negaciones que invierten el siguiente término detectado.
_NEGADORES: dict[str, set[str]] = {
    "es": {"no", "nunca", "jamás", "nada", "tampoco", "ningún", "ninguna"},
    "en": {"no", "not", "never", "nothing", "none", "without"},
    "de": {"nicht", "nie", "kein", "keine", "ohne"},
    "fr": {"ne", "pas", "jamais", "rien", "aucun", "aucune", "sans"},
}


@dataclass(frozen=True)
class AnalisisSentimiento:
    etiqueta: str  # positivo | neutro | negativo
    score: float  # [-1, 1]
    palabras_positivas: int
    palabras_negativas: int


def analizar_sentimiento(texto: str, idioma: str | None = None) -> AnalisisSentimiento:
    """Sentiment scoring por lexicón con manejo simple de negación.

    El score final se mapea a 3 clases con umbrales conservadores:
    - score >= 0.20  → positivo
    - score <= -0.20 → negativo
    - otro          → neutro
    """
    if not texto or not texto.strip():
        return AnalisisSentimiento("neutro", 0.0, 0, 0)

    if idioma not in {"es", "en", "de", "fr"}:
        idioma = detectar_idioma(texto)
    pos_set = {_normalizar(p) for p in _POS.get(idioma, set())}
    neg_set = {_normalizar(p) for p in _NEG.get(idioma, set())}
    negadores = {_normalizar(p) for p in _NEGADORES.get(idioma, set())}

    tokens = [_normalizar(t) for t in _tokens(texto)]
    pos = neg = 0
    invertir = False
    ventana = 0

    for tok in tokens:
        if tok in negadores:
            invertir = True
            ventana = 3
            continue
        es_pos = tok in pos_set
        es_neg = tok in neg_set
        if not (es_pos or es_neg):
            if ventana > 0:
                ventana -= 1
                if ventana == 0:
                    invertir = False
            continue
        if invertir:
            es_pos, es_neg = es_neg, es_pos
            invertir = False
            ventana = 0
        if es_pos:
            pos += 1
        if es_neg:
            neg += 1

    total = pos + neg
    if total == 0:
        return AnalisisSentimiento("neutro", 0.0, 0, 0)
    score = (pos - neg) / total
    if score >= 0.20:
        etiqueta = "positivo"
    elif score <= -0.20:
        etiqueta = "negativo"
    else:
        etiqueta = "neutro"
    return AnalisisSentimiento(
        etiqueta=etiqueta, score=round(score, 4), palabras_positivas=pos, palabras_negativas=neg
    )


# ---------------- detección de temas ----------------

# Vocabulario controlado: tema → conjunto de palabras clave (en su forma normalizada).
_TEMAS: dict[str, set[str]] = {
    "playa": {
        "playa",
        "playas",
        "beach",
        "beaches",
        "strand",
        "strände",
        "plage",
        "plages",
        "monsul",
        "genoveses",
        "playazo",
        "cala",
        "calas",
        "arena",
        "mar",
        "sea",
        "mer",
        "meer",
    },
    "parque-natural": {
        "parque",
        "cabo",
        "gata",
        "amoladeras",
        "reserva",
        "biosfera",
        "unesco",
        "ecosistema",
        "natural",
        "park",
        "biosphere",
        "reservat",
        "réserve",
        "biosphère",
    },
    "ruta": {
        "ruta",
        "rutas",
        "sendero",
        "senderismo",
        "ciclismo",
        "bici",
        "bicicleta",
        "mtb",
        "trail",
        "hike",
        "hiking",
        "wandern",
        "wanderung",
        "randonnée",
        "rodalquilar",
        "albaricoques",
        "caminata",
    },
    "alojamiento": {
        "hotel",
        "alojamiento",
        "hostal",
        "apartamento",
        "camping",
        "airbnb",
        "casa",
        "rural",
        "stay",
        "stayed",
        "accommodation",
        "unterkunft",
        "logement",
        "cortijo",
    },
    "gastronomia": {
        "comida",
        "comer",
        "tapas",
        "restaurante",
        "gastronomia",
        "gastronomía",
        "pescado",
        "marisco",
        "food",
        "eat",
        "seafood",
        "essen",
        "restaurant",
        "manger",
        "cuisine",
        "menu",
    },
    "patrimonio": {
        "patrimonio",
        "monumento",
        "mina",
        "minas",
        "castillo",
        "yacimiento",
        "museo",
        "history",
        "heritage",
        "castle",
        "mine",
        "kulturerbe",
        "schloss",
        "patrimoine",
    },
    "fotografia": {
        "foto",
        "fotos",
        "fotografia",
        "fotografía",
        "photo",
        "photography",
        "fotografieren",
        "fotografie",
        "photographie",
        "atardecer",
        "amanecer",
        "sunset",
        "sunrise",
        "sonnenuntergang",
        "coucher",
        "instagram",
        "instagrameable",
    },
    "accesibilidad": {
        "accesible",
        "accesibilidad",
        "silla",
        "ruedas",
        "accessible",
        "wheelchair",
        "barrierefrei",
        "accessibilité",
    },
    "masificacion": {
        "masificado",
        "masificación",
        "colas",
        "aforo",
        "crowded",
        "crowd",
        "overcrowded",
        "überfüllt",
        "bondé",
        "saturado",
    },
    "atardecer": {
        "atardecer",
        "atardeceres",
        "sunset",
        "sonnenuntergang",
        "coucher",
        "crepusculo",
        "crepúsculo",
    },
}


def extraer_temas(texto: str, max_temas: int = 5) -> list[str]:
    if not texto.strip():
        return []
    tokens = {_normalizar(t) for t in _tokens(texto)}
    if not tokens:
        return []
    coincidencias: list[tuple[str, int]] = []
    for tema, vocab in _TEMAS.items():
        vocab_norm = {_normalizar(v) for v in vocab}
        n = len(tokens & vocab_norm)
        if n > 0:
            coincidencias.append((tema, n))
    coincidencias.sort(key=lambda x: x[1], reverse=True)
    return [t for t, _ in coincidencias[:max_temas]]


# ---------------- detección de entidades ----------------

# Mapeo término → URN del recurso turístico (alineado con los seeds).
_ENTIDADES_URN: dict[str, str] = {
    "monsul": "urn:ngsi-ld:RecursoTuristico:nijar:playa-monsul",
    "mónsul": "urn:ngsi-ld:RecursoTuristico:nijar:playa-monsul",
    "genoveses": "urn:ngsi-ld:RecursoTuristico:nijar:playa-genoveses",
    "playazo": "urn:ngsi-ld:RecursoTuristico:nijar:playa-playazo",
    "amoladeras": "urn:ngsi-ld:RecursoTuristico:nijar:centro-amoladeras",
    "rodalquilar": "urn:ngsi-ld:RecursoTuristico:nijar:rodalquilar-mina",
    "albaricoques": "urn:ngsi-ld:RecursoTuristico:nijar:los-albaricoques",
    "isleta": "urn:ngsi-ld:RecursoTuristico:nijar:isleta-del-moro",
    "san jose": "urn:ngsi-ld:RecursoTuristico:nijar:san-jose",
    "san josé": "urn:ngsi-ld:RecursoTuristico:nijar:san-jose",
    "amatista": "urn:ngsi-ld:RecursoTuristico:nijar:mirador-amatista",
}


def detectar_entidades(texto: str) -> list[str]:
    if not texto:
        return []
    tnorm = _normalizar(texto)
    encontradas: list[str] = []
    for clave, urn in _ENTIDADES_URN.items():
        if _normalizar(clave) in tnorm and urn not in encontradas:
            encontradas.append(urn)
    return encontradas
