"""Ortofotos históricas del territorio (PNOA histórico del IGN).

El Gemelo vivo 2D permite elegir un año/periodo y ver cómo era el territorio
de Níjar (vuelo americano de 1956, vuelos nacionales de los 70-80, OLISTAT,
SIGPAC y las ortofotos PNOA anuales), y compararlo con otro mediante una
cortina deslizante.

El catálogo de vuelos no se fija a mano: se lee del propio servicio WMS del
IGN (``GetCapabilities``) y, para cada capa, se comprueba con una petición
``GetMap`` mínima sobre Níjar que de verdad tiene imagen en el municipio (los
vuelos PNOA anuales solo cubren algunas comunidades cada año). El resultado se
cachea en memoria 24 h.
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass

import httpx

from nijar_dti.config import get_settings
from nijar_dti.core.logging import get_logger

logger = get_logger(__name__)

# Zona de muestreo para comprobar cobertura: interior de Níjar (tierra firme,
# junto al casco). lon/lat en EPSG:4326 (orden de WMS 1.1.1).
_BBOX_MUESTRA = (-2.225, 36.955, -2.19, 36.98)
# Una JPEG de 128 px de un área sin imagen (color plano) ocupa ~1 KB; una
# ortofoto real de esa zona pasa holgadamente de este umbral.
_UMBRAL_BYTES_IMAGEN = 2500
_TTL_SEGUNDOS = 24 * 3600
_CONCURRENCIA = 6

_RE_CAPA = re.compile(
    r"<Layer[^>]*>\s*<Name>([^<]+)</Name>\s*<Title>([^<]*)</Title>", re.IGNORECASE
)
_RE_ANIO = re.compile(r"(19|20)\d{2}")


@dataclass(frozen=True)
class OrtofotoHistorica:
    nombre: str  # nombre de la capa WMS
    titulo: str
    anio: int  # primer año del vuelo (orden cronológico)
    etiqueta: str  # texto corto para el selector («1956-57», «2010»…)


_cache: tuple[float, list[OrtofotoHistorica], bool] | None = None


def _etiqueta(nombre: str, titulo: str) -> tuple[int, str] | None:
    """Año inicial y etiqueta corta de un vuelo a partir de su nombre/título."""
    texto = f"{nombre} {titulo}"
    anios = sorted({int(m.group(0)) for m in _RE_ANIO.finditer(texto)})
    if not anios:
        return None
    ini, fin = anios[0], anios[-1]
    if fin == ini:
        return ini, str(ini)
    return ini, f"{ini}-{str(fin)[2:] if fin // 100 == ini // 100 else fin}"


def parsear_capacidades(xml: str) -> list[OrtofotoHistorica]:
    """Extrae los vuelos (capas con nombre y año) de un GetCapabilities WMS."""
    vistos: set[str] = set()
    out: list[OrtofotoHistorica] = []
    for nombre, titulo in _RE_CAPA.findall(xml):
        nombre, titulo = nombre.strip(), titulo.strip()
        if nombre in vistos:
            continue
        et = _etiqueta(nombre, titulo)
        if et is None:
            continue  # capas agrupadoras o sin fecha
        vistos.add(nombre)
        out.append(
            OrtofotoHistorica(nombre=nombre, titulo=titulo or nombre, anio=et[0], etiqueta=et[1])
        )
    out.sort(key=lambda o: (o.anio, o.etiqueta))
    return out


async def _tiene_imagen(cli: httpx.AsyncClient, url: str, capa: str) -> bool:
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "LAYERS": capa,
        "STYLES": "",
        "SRS": "EPSG:4326",
        "BBOX": ",".join(str(v) for v in _BBOX_MUESTRA),
        "WIDTH": "128",
        "HEIGHT": "128",
        "FORMAT": "image/jpeg",
    }
    try:
        r = await cli.get(url, params=params)
    except httpx.HTTPError:
        return False
    es_imagen = r.headers.get("content-type", "").startswith("image/")
    return r.status_code == 200 and es_imagen and len(r.content) > _UMBRAL_BYTES_IMAGEN


async def listar_ortofotos() -> tuple[str, list[OrtofotoHistorica], bool]:
    """Devuelve (url_wms, vuelos con imagen en Níjar, cobertura_verificada).

    Si la comprobación de cobertura descartara todos los vuelos (cambio de
    formato del servicio, umbral inadecuado…), se devuelven todos sin filtrar
    y ``cobertura_verificada=False`` para no dejar el selector vacío.
    """
    global _cache
    url = get_settings().ortofoto_historica_wms_url
    if _cache and time.monotonic() - _cache[0] < _TTL_SEGUNDOS:
        return url, _cache[1], _cache[2]

    async with httpx.AsyncClient(timeout=20) as cli:
        r = await cli.get(url, params={"SERVICE": "WMS", "REQUEST": "GetCapabilities"})
        r.raise_for_status()
        capas = parsear_capacidades(r.text)

        sem = asyncio.Semaphore(_CONCURRENCIA)

        async def comprobar(o: OrtofotoHistorica) -> bool:
            async with sem:
                return await _tiene_imagen(cli, url, o.nombre)

        cubre = await asyncio.gather(*(comprobar(o) for o in capas))

    con_imagen = [o for o, ok in zip(capas, cubre, strict=True) if ok]
    verificada = bool(con_imagen)
    resultado = con_imagen if verificada else capas
    logger.info(
        "Ortofotos históricas cargadas",
        vuelos=len(capas),
        con_imagen_en_nijar=len(con_imagen),
        cobertura_verificada=verificada,
    )
    _cache = (time.monotonic(), resultado, verificada)
    return url, resultado, verificada


# =====================================================================
# Ortofotos históricas de la Junta de Andalucía (REDIAM e IECA)
# =====================================================================
# La Junta publica cada vuelo como un servicio WMS propio (no hay un servicio
# multianual como el del IGN). Los nombres de capa no son homogéneos y el IECA
# renombró su serie en 2023 (``/wms/ortofotoAAAA`` → ``/wms/ortofoto_AAAA``),
# así que cada entrada lleva URLs alternativas y nombres de capa candidatos; al
# cargar el catálogo se lee el GetCapabilities de cada servicio, se elige la
# capa y se comprueba con un GetMap en EPSG:3857 (lo que pide el mapa) que hay
# imagen sobre Níjar. Solo aparecen en el selector los vuelos que responden.

_IECA = "https://www.ideandalucia.es/wms/"
_REDIAM = "https://www.juntadeandalucia.es/medioambiente/mapwms/"


@dataclass(frozen=True)
class ServicioJunta:
    etiqueta: str
    anio: int
    titulo: str
    organismo: str  # «REDIAM» | «IECA»
    urls: tuple[str, ...]
    candidatas: tuple[str, ...] = ()


SERVICIOS_JUNTA: tuple[ServicioJunta, ...] = (
    ServicioJunta(
        "1956-57",
        1956,
        "Vuelo americano 1956-57 (B/N)",
        "REDIAM",
        (f"{_REDIAM}REDIAM_Ortofoto_Andalucia_1956", f"{_IECA}ortofoto_1956-1957"),
        ("ortofoto_1956", "ortofotografia_1956-1957_pancromatico"),
    ),
    ServicioJunta(
        "1977-83",
        1977,
        "Vuelo interministerial 1977-83 (B/N)",
        "REDIAM",
        (f"{_REDIAM}REDIAM_Ortofoto_BN_1977_83",),
        ("orto_BN_77_83",),
    ),
    ServicioJunta(
        "1984-85",
        1984,
        "Vuelo nacional 1984-85 (B/N)",
        "REDIAM",
        (f"{_REDIAM}REDIAM_Ortofoto_PAN_Andalucia_84_85",),
        ("orto_1984_85",),
    ),
    ServicioJunta(
        "1998-99",
        1998,
        "Ortofoto de Andalucía 1998-99",
        "IECA",
        (f"{_IECA}ortofoto_1998", f"{_IECA}ortofoto1998"),
    ),
    ServicioJunta(
        "2001-02",
        2001,
        "Ortofoto de Andalucía 2001-02",
        "IECA",
        (f"{_IECA}ortofoto2001", f"{_REDIAM}REDIAM_Ortofoto_coloreada_Andalucia_2001"),
        ("ORTO_2001",),
    ),
    ServicioJunta(
        "2004",
        2004,
        "Ortofoto de Andalucía 2004",
        "IECA",
        (f"{_IECA}ortofoto_2004", f"{_IECA}ortofoto2004"),
    ),
    ServicioJunta(
        "2006-07",
        2006,
        "Ortofoto de Andalucía 2006-07 (color)",
        "REDIAM",
        (f"{_REDIAM}REDIAM_Ortofoto_Andalucia_RGB_2006_2007",),
    ),
    ServicioJunta(
        "2007",
        2007,
        "Ortofoto de Andalucía 2007",
        "IECA",
        (f"{_IECA}ortofoto2007",),
        ("oca10_2007",),
    ),
    ServicioJunta(
        "2008-09",
        2008,
        "Ortofoto de Andalucía 2008-09",
        "IECA",
        (f"{_IECA}ortofoto_2008-2009", f"{_IECA}ortofoto2009"),
        ("oca10_2008-09",),
    ),
    ServicioJunta(
        "2010-11",
        2010,
        "Ortofoto de Andalucía 2010-11",
        "IECA",
        (f"{_IECA}ortofoto2010",),
        ("orto_2010-11",),
    ),
    ServicioJunta(
        "2013",
        2013,
        "Ortofoto de Andalucía 2013",
        "IECA",
        (f"{_IECA}ortofoto2013",),
        ("oca10_2013",),
    ),
    ServicioJunta(
        "2016",
        2016,
        "Ortofoto de Andalucía 2016",
        "IECA",
        (f"{_IECA}ortofoto_2016", f"{_IECA}ortofoto2016"),
        ("ortofotografia_2016_rgb",),
    ),
    ServicioJunta(
        "2019",
        2019,
        "Ortofoto de Andalucía 2019",
        "IECA",
        (f"{_IECA}ortofoto_2019",),
        ("ortofotografia_2019_rgb",),
    ),
    ServicioJunta(
        "2022",
        2022,
        "Ortofoto de Andalucía 2022",
        "IECA",
        (f"{_IECA}ortofoto_2022",),
        ("ortofotografia_2022_rgb",),
    ),
)

# Capas auxiliares que algunos servicios publican junto a la ortofoto
_RE_CAPA_AUXILIAR = re.compile(
    r"distrib|hoja|malla|cuadr|limite|l[ií]mite|indice|[ií]ndice|grid|fecha|vuelo_|marco",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class OrtofotoJunta:
    id: str
    url: str
    capa: str
    formato: str
    etiqueta: str
    anio: int
    titulo: str
    organismo: str


@dataclass
class DiagnosticoJunta:
    """Resultado de la comprobación de un servicio (para el verificador)."""

    etiqueta: str
    url: str | None = None
    capa: str | None = None
    capas_disponibles: list[str] | None = None
    con_imagen: bool = False
    error: str | None = None


# <Layer …> / </Layer> (grupos 1-2) y <Name>/<Title> con su texto (grupos 3-4)
_RE_ETIQUETA = re.compile(r"<(/?)(Layer)\b[^>]*>|<(Name|Title)>([^<]*)</(?:Name|Title)>")

_cache_junta: tuple[float, list[OrtofotoJunta], list[DiagnosticoJunta]] | None = None


def elegir_capa(xml: str, candidatas: tuple[str, ...]) -> tuple[str | None, list[str], str]:
    """De un GetCapabilities WMS: (capa elegida, capas con nombre, formato de imagen).

    Prioridad: un nombre candidato; si no, una capa hoja que no sea auxiliar
    (rejillas de hojas, fechas de vuelo…), mejor en color; si no, la raíz.
    """
    # Lectura por etiquetas (sin parser XML: el documento viene de fuera)
    capas: list[tuple[str, str, bool]] = []  # (nombre, título, es_hoja)
    pila: list[dict[str, object]] = []
    for m in _RE_ETIQUETA.finditer(xml):
        cierre, tag, texto = m.group(1), m.group(2) or m.group(3), m.group(4)
        if tag == "Layer" and not cierre:
            if pila:
                pila[-1]["hijas"] = True
            pila.append({"nombre": None, "titulo": "", "hijas": False})
        elif tag == "Layer" and cierre and pila:
            capa = pila.pop()
            if capa["nombre"]:
                capas.append((str(capa["nombre"]), str(capa["titulo"]), not capa["hijas"]))
        elif tag in ("Name", "Title") and pila and texto is not None:
            clave = "nombre" if tag == "Name" else "titulo"
            if not pila[-1][clave]:
                pila[-1][clave] = texto.strip()
    bloque_getmap = re.search(r"<GetMap>(.*?)</GetMap>", xml, re.DOTALL)
    formatos = re.findall(
        r"<Format>\s*([^<]+?)\s*</Format>", bloque_getmap.group(1) if bloque_getmap else ""
    )

    nombres = [n for n, _, _ in capas]
    if not formatos or "image/jpeg" in formatos:
        formato = "image/jpeg"
    else:
        formato = "image/png" if "image/png" in formatos else formatos[0]
    for c in candidatas:
        if c in nombres:
            return c, nombres, formato
    utiles = [(n, t) for n, t, hoja in capas if hoja and not _RE_CAPA_AUXILIAR.search(f"{n} {t}")]
    if utiles:
        color = [n for n, t in utiles if re.search(r"rgb|color", f"{n} {t}", re.IGNORECASE)]
        return (color or [utiles[0][0]])[0], nombres, formato
    return (nombres[0] if nombres else None), nombres, formato


def _bbox_3857(lon0: float, lat0: float, lon1: float, lat1: float) -> tuple[float, ...]:
    import math

    r = 6378137.0

    def x(lon: float) -> float:
        return math.radians(lon) * r

    def y(lat: float) -> float:
        return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * r

    return (x(lon0), y(lat0), x(lon1), y(lat1))


async def _imagen_3857(cli: httpx.AsyncClient, url: str, capa: str, formato: str) -> bool:
    params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetMap",
        "LAYERS": capa,
        "STYLES": "",
        "SRS": "EPSG:3857",
        "BBOX": ",".join(f"{v:.2f}" for v in _bbox_3857(*_BBOX_MUESTRA)),
        "WIDTH": "128",
        "HEIGHT": "128",
        "FORMAT": formato,
    }
    try:
        r = await cli.get(url, params=params)
    except httpx.HTTPError:
        return False
    es_imagen = r.headers.get("content-type", "").startswith("image/")
    return r.status_code == 200 and es_imagen and len(r.content) > _UMBRAL_BYTES_IMAGEN


async def _comprobar_servicio(
    cli: httpx.AsyncClient, s: ServicioJunta
) -> tuple[OrtofotoJunta | None, DiagnosticoJunta]:
    diag = DiagnosticoJunta(etiqueta=s.etiqueta)
    for url in s.urls:
        diag.url = url
        try:
            r = await cli.get(
                url, params={"SERVICE": "WMS", "REQUEST": "GetCapabilities", "VERSION": "1.1.1"}
            )
            r.raise_for_status()
            capa, nombres, formato = elegir_capa(r.text, s.candidatas)
        except Exception as exc:  # noqa: BLE001 - un servicio caído no debe tumbar el resto
            diag.error = f"{type(exc).__name__}: {exc}"[:200]
            continue
        diag.capas_disponibles, diag.capa, diag.error = nombres, capa, None
        if capa and await _imagen_3857(cli, url, capa, formato):
            diag.con_imagen = True
            slug = re.sub(r"[^0-9a-z]+", "-", s.etiqueta.lower())
            return (
                OrtofotoJunta(
                    id=f"junta:{slug}",
                    url=url,
                    capa=capa,
                    formato=formato,
                    etiqueta=s.etiqueta,
                    anio=s.anio,
                    titulo=s.titulo,
                    organismo=s.organismo,
                ),
                diag,
            )
        diag.error = "sin imagen sobre Níjar en EPSG:3857" if capa else "sin capas con nombre"
    return None, diag


async def listar_ortofotos_junta(
    forzar: bool = False,
) -> tuple[list[OrtofotoJunta], list[DiagnosticoJunta]]:
    """Vuelos de la Junta con imagen sobre Níjar (y el diagnóstico de cada servicio).

    Nunca lanza: si la Junta no responde, el selector sigue con los del IGN.
    """
    global _cache_junta
    if not get_settings().ortofotos_junta_activas:
        return [], []
    if _cache_junta and not forzar:
        caducidad = _TTL_SEGUNDOS if _cache_junta[1] else 3600  # si falló todo, reintento en 1 h
        if time.monotonic() - _cache_junta[0] < caducidad:
            return _cache_junta[1], _cache_junta[2]
    sem = asyncio.Semaphore(_CONCURRENCIA)
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as cli:

        async def uno(s: ServicioJunta) -> tuple[OrtofotoJunta | None, DiagnosticoJunta]:
            async with sem:
                return await _comprobar_servicio(cli, s)

        resultados = await asyncio.gather(*(uno(s) for s in SERVICIOS_JUNTA))
    vuelos = sorted((o for o, _ in resultados if o), key=lambda o: o.anio)
    diags = [d for _, d in resultados]
    logger.info(
        "Ortofotos históricas de la Junta cargadas",
        servicios=len(SERVICIOS_JUNTA),
        con_imagen_en_nijar=len(vuelos),
    )
    _cache_junta = (time.monotonic(), vuelos, diags)
    return vuelos, diags
