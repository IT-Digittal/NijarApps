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
