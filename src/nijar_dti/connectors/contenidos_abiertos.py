"""Fuentes abiertas para los contenidos del tótem (solo lectura, sin claves).

- **OpenStreetMap (Overpass API)**: restaurantes, bares y cafeterías del
  término municipal (sección Gastronomía) y alfarerías/talleres de jarapas
  (sección Cerámica y jarapas). Licencia ODbL: «© colaboradores de
  OpenStreetMap».
- **Wikipedia / Wikimedia Commons**: foto representativa de cada recurso
  turístico que no tenga imagen. Primero el artículo de Wikipedia del lugar;
  si no hay, la foto de Commons georreferenciada más cercana. Se guarda el
  crédito de autoría y licencia (CC) para mostrarlo en el tótem.

Este módulo solo habla con las APIs y normaliza; la escritura en BBDD la hace
``workers/contenidos_abiertos.py``.
"""

from __future__ import annotations

import asyncio
import html
import math
import re
from dataclasses import dataclass, field
from typing import Any

import httpx


def user_agent(contacto: str) -> str:
    """User-Agent con contacto, obligatorio por la política de las APIs de Wikimedia
    (sin él limitan el acceso con 429 casi de inmediato)."""
    return f"PlataformaDTI-Nijar/1.1 ({contacto}; Ayuntamiento de Nijar, totem turistico)"


# Espejos públicos de Overpass: si el principal da 429/504 se prueba el siguiente
OVERPASS_ESPEJOS = ("https://overpass.kumi.systems/api/interpreter",)

_REINTENTABLES = {429, 502, 503, 504}
_esperar = asyncio.sleep  # inyectable en los tests


async def _pedir(
    cli: httpx.AsyncClient, metodo: str, url: str, intentos: int = 5, **kw: Any
) -> httpx.Response:
    """Petición con reintentos ante 429/5xx, respetando ``Retry-After``."""
    for n in range(intentos):
        r = await cli.request(metodo, url, **kw)
        if r.status_code not in _REINTENTABLES or n == intentos - 1:
            r.raise_for_status()
            return r
        try:
            espera = min(float(r.headers.get("retry-after", "")), 60.0)
        except ValueError:
            espera = 2.0 * 2**n  # 2, 4, 8, 16 s
        await _esperar(espera)
    raise AssertionError("inalcanzable")


# ---------------------------------------------------------------- OSM ----

_TIPO_POR_AMENITY = {
    "restaurant": "gastronomia_restaurante",
    "cafe": "gastronomia_cafeteria",
    "ice_cream": "gastronomia_cafeteria",
    "bar": "gastronomia_bar",
    "pub": "gastronomia_bar",
}

_COCINAS = {
    "mediterranean": "mediterránea",
    "spanish": "española",
    "regional": "tradicional",
    "seafood": "pescados y mariscos",
    "fish": "pescado",
    "tapas": "tapas",
    "pizza": "pizza",
    "italian": "italiana",
    "burger": "hamburguesas",
    "vegetarian": "vegetariana",
    "vegan": "vegana",
    "international": "internacional",
    "coffee_shop": "café",
    "ice_cream": "helados",
    "breakfast": "desayunos",
}


def consulta_overpass(municipio: str = "Níjar") -> str:
    """Consulta Overpass QL: gastronomía y artesanía dentro del término municipal."""
    return f"""[out:json][timeout:120];
area["boundary"="administrative"]["admin_level"="8"]["name"="{municipio}"]->.m;
(
  nwr(area.m)["amenity"~"^(restaurant|cafe|bar|pub|ice_cream)$"]["name"];
  nwr(area.m)["craft"~"^(pottery|weaver)$"]["name"];
  nwr(area.m)["shop"~"^(pottery|craft|carpet)$"]["name"];
);
out center tags;"""


@dataclass
class ElementoOsm:
    """Negocio de OSM normalizado al modelo de la plataforma."""

    osm_id: str  # «node/123», «way/456»
    nombre: str
    lat: float
    lon: float
    clase: str  # "servicio" (gastronomía) o "recurso" (artesanía)
    tipo: str | None = None  # tipo de Servicio si clase == "servicio"
    etiquetas: list[str] = field(default_factory=list)
    descripcion: str | None = None
    direccion: str | None = None
    codigo_postal: str | None = None
    telefono: str | None = None
    web: str | None = None
    email: str | None = None
    horario: str | None = None

    @property
    def slug(self) -> str:
        return "osm-" + self.osm_id.replace("/", "-")


_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.IGNORECASE)
_RE_CP = re.compile(r"^\d{5}$")


def _web(valor: str | None) -> str | None:
    """URL válida para el esquema (HttpUrl) o None: el listado no puede romperse."""
    if not valor:
        return None
    v = valor.strip().split(";")[0].strip()
    if not v or " " in v:
        return None
    if not v.lower().startswith(("http://", "https://")):
        v = "https://" + v
    return v if re.match(r"^https?://[\w.-]+\.[a-z]{2,}(/\S*)?$", v, re.IGNORECASE) else None


def _etiquetas_artesania(tags: dict[str, str]) -> list[str]:
    nombre = tags.get("name", "").lower()
    craft, shop = tags.get("craft"), tags.get("shop")
    et = ["artesania"]
    if craft == "pottery" or shop == "pottery" or re.search(r"alfar|cer[aá]mica|barro", nombre):
        et.append("ceramica")
    if craft == "weaver" or shop == "carpet" or "jarapa" in nombre or "telar" in nombre:
        et.append("jarapas")
    return et


def parsear_overpass(datos: dict[str, Any]) -> list[ElementoOsm]:
    """Normaliza la respuesta JSON de Overpass (``out center tags``)."""
    out: list[ElementoOsm] = []
    for el in datos.get("elements") or []:
        tags: dict[str, str] = el.get("tags") or {}
        nombre = (tags.get("name") or "").strip()
        lat = el.get("lat", (el.get("center") or {}).get("lat"))
        lon = el.get("lon", (el.get("center") or {}).get("lon"))
        if not nombre or lat is None or lon is None:
            continue
        amenity = tags.get("amenity")
        if amenity in _TIPO_POR_AMENITY:
            clase, tipo = "servicio", _TIPO_POR_AMENITY[amenity]
            cocinas = [
                _COCINAS.get(c.strip(), c.strip().replace("_", " "))
                for c in (tags.get("cuisine") or "").split(";")
                if c.strip()
            ]
            etiquetas = ["gastronomia", *cocinas]
            descripcion = ("Cocina " + ", ".join(cocinas) + ".") if cocinas else None
        else:
            clase, tipo = "recurso", None
            etiquetas = _etiquetas_artesania(tags)
            if "jarapas" in etiquetas and "ceramica" not in etiquetas:
                descripcion = "Taller y tienda de jarapas tejidas a mano."
            elif "ceramica" in etiquetas:
                descripcion = "Alfarería y tienda de cerámica artesana de Níjar."
            else:
                descripcion = "Tienda de artesanía local."
        calle = tags.get("addr:street")
        num = tags.get("addr:housenumber")
        lugar = tags.get("addr:place") or tags.get("addr:city")
        direccion = ", ".join(p for p in [" ".join(x for x in [calle, num] if x), lugar] if p)
        cp = tags.get("addr:postcode")
        email = tags.get("email") or tags.get("contact:email")
        out.append(
            ElementoOsm(
                osm_id=f"{el.get('type')}/{el.get('id')}",
                nombre=nombre[:255],
                lat=float(lat),
                lon=float(lon),
                clase=clase,
                tipo=tipo,
                etiquetas=etiquetas,
                descripcion=descripcion,
                direccion=direccion or None,
                codigo_postal=cp if cp and _RE_CP.match(cp) else None,
                telefono=(tags.get("phone") or tags.get("contact:phone") or "").split(";")[0]
                or None,
                web=_web(tags.get("website") or tags.get("contact:website")),
                email=email if email and _RE_EMAIL.match(email) else None,
                horario=tags.get("opening_hours"),
            )
        )
    return out


async def descargar_osm(
    cli: httpx.AsyncClient, url_overpass: str, municipio: str = "Níjar"
) -> list[ElementoOsm]:
    """Descarga de Overpass con reintentos; si el servidor sigue caído, prueba un espejo."""
    error: httpx.HTTPError | None = None
    for url in (url_overpass, *[u for u in OVERPASS_ESPEJOS if u != url_overpass]):
        try:
            r = await _pedir(
                cli, "POST", url, intentos=3, data={"data": consulta_overpass(municipio)}
            )
            return parsear_overpass(r.json())
        except httpx.HTTPError as exc:
            error = exc
    assert error is not None
    raise error


# ---------------------------------------------------- Wikipedia/Commons ----

_WIKI_ES = "https://es.wikipedia.org/w/api.php"
_COMMONS = "https://commons.wikimedia.org/w/api.php"
_ANCHO = 1280
_ANCHO_MIN_ORIGINAL = 800
_PALABRAS_VACIAS = {
    "de", "del", "la", "las", "el", "los", "y", "en", "a", "sendero", "ruta", "playa",
    "cala", "s01", "s02", "s03", "s04", "s05", "s06", "s07", "s08", "s09", "s10", "s11",
    "s12", "s13", "s14", "s15", "s16", "camino", "níjar", "nijar",
}  # fmt: skip


@dataclass
class ImagenEncontrada:
    url: str  # miniatura de ~1280 px servida por upload.wikimedia.org
    credito: str  # «Autor · Licencia · Wikimedia Commons»
    pagina: str  # página de la imagen (descripción y licencia completa)
    origen: str  # "wikipedia" o "commons-geo"


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = math.radians
    a = (
        math.sin(r(lat2 - lat1) / 2) ** 2
        + math.cos(r(lat1)) * math.cos(r(lat2)) * math.sin(r(lon2 - lon1) / 2) ** 2
    )
    return 6371 * 2 * math.asin(math.sqrt(a))


def _palabras(texto: str) -> set[str]:
    return {p for p in re.findall(r"[a-záéíóúüñ]+", texto.lower()) if len(p) > 2} - _PALABRAS_VACIAS


def _limpiar_html(valor: str | None) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", valor or "")).strip()


async def _info_fichero(cli: httpx.AsyncClient, titulos: list[str]) -> list[dict[str, Any]]:
    """imageinfo (url escalada, tamaño, MIME, autor y licencia) de ficheros de Commons."""
    if not titulos:
        return []
    r = await _pedir(
        cli,
        "GET",
        _COMMONS,
        params={
            "action": "query",
            "format": "json",
            "titles": "|".join(titulos[:20]),
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": str(_ANCHO),
        },
    )
    r.raise_for_status()
    paginas = (r.json().get("query") or {}).get("pages") or {}
    por_titulo = {p.get("title"): p for p in paginas.values()}
    out = []
    for t in titulos:
        p = por_titulo.get(t)
        if p and p.get("imageinfo"):
            out.append({"titulo": t, **p["imageinfo"][0]})
    return out


# Fotos que no representan el lugar: fotos desde el espacio (la ISS también se
# geoetiqueta), mapas, planos, escudos, banderas, diagramas…
_RE_NO_REPRESENTATIVA = re.compile(
    r"\bISS\d|\bSTS-|NASA|Space Center|astronaut|Landsat|Sentinel|sat[eé]lit|"
    r"\bmap\b|\bmapa|\bplano\b|locator|location map|escudo|coat of arms|\bflag\b|"
    r"bandera|diagram|esquema|\blogo\b",
    re.IGNORECASE,
)


def credito_no_representativo(texto: str) -> bool:
    """True si el crédito/título delata una foto que no sirve como imagen del lugar."""
    return bool(_RE_NO_REPRESENTATIVA.search(texto or ""))


def _a_imagen(info: dict[str, Any], origen: str) -> ImagenEncontrada | None:
    if info.get("mime") != "image/jpeg":  # las PNG suelen ser mapas o diagramas
        return None
    if int(info.get("width") or 0) < _ANCHO_MIN_ORIGINAL:
        return None
    meta = info.get("extmetadata") or {}
    autor = _limpiar_html((meta.get("Artist") or {}).get("value")) or "Autor desconocido"
    licencia = _limpiar_html((meta.get("LicenseShortName") or {}).get("value")) or "ver licencia"
    descripcion = _limpiar_html((meta.get("ImageDescription") or {}).get("value"))
    if credito_no_representativo(f"{info.get('titulo', '')} {autor} {descripcion[:300]}"):
        return None
    url = info.get("thumburl") or info.get("url")
    if not url:
        return None
    return ImagenEncontrada(
        url=url,
        credito=f"{autor[:120]} · {licencia} · Wikimedia Commons",
        pagina=info.get("descriptionurl") or url,
        origen=origen,
    )


async def imagen_wikipedia(
    cli: httpx.AsyncClient, nombre: str, lat: float, lon: float
) -> ImagenEncontrada | None:
    """Foto principal del artículo de Wikipedia (es) que corresponde al lugar.

    El artículo se acepta si está georreferenciado a menos de 5 km del recurso
    o, sin coordenadas, si comparte alguna palabra significativa con el nombre.
    """
    r = await _pedir(
        cli,
        "GET",
        _WIKI_ES,
        params={
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"{nombre} Níjar",
            "gsrlimit": "5",
            "prop": "pageimages|coordinates",
            "piprop": "name",
        },
    )
    r.raise_for_status()
    paginas = sorted(
        ((r.json().get("query") or {}).get("pages") or {}).values(),
        key=lambda p: p.get("index", 99),
    )
    claves = _palabras(nombre)
    for p in paginas:
        fichero = p.get("pageimage")
        if not fichero:
            continue
        coords = (p.get("coordinates") or [None])[0]
        if coords:
            if _km(lat, lon, coords["lat"], coords["lon"]) > 5:
                continue
        elif not (claves & _palabras(p.get("title", ""))):
            continue
        infos = await _info_fichero(cli, [f"File:{fichero}"])
        if infos and (img := _a_imagen(infos[0], "wikipedia")):
            return img
    return None


async def imagen_commons_cercana(
    cli: httpx.AsyncClient, lat: float, lon: float, radio_m: int = 1000
) -> ImagenEncontrada | None:
    """La foto de Commons georreferenciada más cercana al punto (radio en metros)."""
    r = await _pedir(
        cli,
        "GET",
        _COMMONS,
        params={
            "action": "query",
            "format": "json",
            "list": "geosearch",
            "gscoord": f"{lat}|{lon}",
            "gsradius": str(min(radio_m, 10_000)),
            "gsnamespace": "6",
            "gslimit": "15",
        },
    )
    r.raise_for_status()
    titulos = [g["title"] for g in (r.json().get("query") or {}).get("geosearch") or []]
    for info in await _info_fichero(cli, titulos):  # ya vienen ordenadas por distancia
        if img := _a_imagen(info, "commons-geo"):
            return img
    return None


async def buscar_imagen(
    cli: httpx.AsyncClient, nombre: str, lat: float, lon: float, radio_m: int = 1000
) -> ImagenEncontrada | None:
    return await imagen_wikipedia(cli, nombre, lat, lon) or await imagen_commons_cercana(
        cli, lat, lon, radio_m
    )
