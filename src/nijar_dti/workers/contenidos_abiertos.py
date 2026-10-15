"""Importador de contenidos abiertos para el tótem (OSM + Wikipedia/Commons).

1. **OpenStreetMap**: crea/actualiza como servicios publicados los
   restaurantes, bares y cafeterías del término municipal (Gastronomía) y
   como recursos las alfarerías y talleres de jarapas (Cerámica y jarapas).
   Es idempotente por URN (``...:osm-node-123``): al repetirlo refresca los
   datos de OSM pero respeta lo decidido en el CMS (``publicado`` e
   imágenes). Lo que desaparece de OSM se despublica, nunca se borra.
2. **Imágenes**: a cada recurso turístico publicado sin foto le busca la de
   su artículo de Wikipedia o, si no hay, la foto de Wikimedia Commons más
   cercana, y guarda el crédito (autor · licencia) en ``enlaces_externos``.
   No pisa imágenes ya puestas desde el CMS.

Uso (en producción, dentro del contenedor de la API):

    python -m nijar_dti.workers.contenidos_abiertos             # todo
    python -m nijar_dti.workers.contenidos_abiertos --solo osm
    python -m nijar_dti.workers.contenidos_abiertos --solo imagenes
    python -m nijar_dti.workers.contenidos_abiertos --dry-run   # sin escribir
    python -m nijar_dti.workers.contenidos_abiertos --solo imagenes --rehacer
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any

import httpx
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement
from sqlalchemy import cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.config import get_settings
from nijar_dti.connectors.contenidos_abiertos import (
    ElementoOsm,
    buscar_imagen,
    credito_no_representativo,
    descargar_osm,
    user_agent,
)
from nijar_dti.core.database import AsyncSessionLocal
from nijar_dti.core.logging import configure_logging, get_logger
from nijar_dti.models.recurso_turistico import RecursoTuristico
from nijar_dti.models.servicio import Servicio

logger = get_logger(__name__)

URN_SERVICIO = "urn:ngsi-ld:Servicio:nijar:"
URN_RECURSO = "urn:ngsi-ld:RecursoTuristico:nijar:"
_META_OSM = {"fuente": "OpenStreetMap", "licencia": "ODbL · © colaboradores de OpenStreetMap"}


def _punto(e: ElementoOsm) -> WKTElement:
    return WKTElement(f"POINT({e.lon} {e.lat})", srid=4326)


def _campos_comunes(e: ElementoOsm) -> dict[str, Any]:
    return {
        "nombre": e.nombre,
        "direccion": e.direccion,
        "codigo_postal": e.codigo_postal,
        "telefono": e.telefono,
        "web": e.web,
        "email": e.email,
        "etiquetas": e.etiquetas,
        "horario": {"osm": e.horario} if e.horario else None,
        "metadata_adicional": {**_META_OSM, "osm_id": e.osm_id},
    }


async def importar_osm(db: AsyncSession, elementos: list[ElementoOsm]) -> dict[str, int]:
    """Upsert de los negocios de OSM; despublica los que ya no están en OSM."""
    cuenta = {"servicios_nuevos": 0, "recursos_nuevos": 0, "actualizados": 0, "despublicados": 0}
    vistos: set[str] = set()
    for e in elementos:
        comunes = _campos_comunes(e)
        if e.clase == "servicio":
            urn = URN_SERVICIO + e.slug
            vistos.add(urn)
            s = (await db.execute(select(Servicio).where(Servicio.urn == urn))).scalar_one_or_none()
            if s is None:
                db.add(
                    Servicio(
                        urn=urn,
                        tipo=e.tipo,  # type: ignore[arg-type]
                        descripcion=e.descripcion,
                        ubicacion=_punto(e),  # type: ignore[arg-type]
                        publicado=True,
                        **comunes,
                    )
                )
                cuenta["servicios_nuevos"] += 1
            else:
                for k, v in comunes.items():
                    setattr(s, k, v)
                s.tipo = e.tipo  # type: ignore[assignment]
                s.descripcion = e.descripcion
                s.ubicacion = _punto(e)  # type: ignore[assignment]
                cuenta["actualizados"] += 1
        else:
            urn = URN_RECURSO + e.slug
            vistos.add(urn)
            r = (
                await db.execute(select(RecursoTuristico).where(RecursoTuristico.urn == urn))
            ).scalar_one_or_none()
            if r is None:
                db.add(
                    RecursoTuristico(
                        urn=urn,
                        categoria="punto_interes",  # type: ignore[arg-type]
                        descripcion_corta=e.descripcion,
                        ubicacion=_punto(e),  # type: ignore[arg-type]
                        publicado=True,
                        **comunes,
                    )
                )
                cuenta["recursos_nuevos"] += 1
            else:
                for k, v in comunes.items():
                    setattr(r, k, v)
                r.descripcion_corta = e.descripcion
                r.ubicacion = _punto(e)  # type: ignore[assignment]
                cuenta["actualizados"] += 1

    # Lo importado antes de OSM que ya no aparece: se despublica (cierre, cambio…)
    servicios = await db.execute(
        select(Servicio).where(
            Servicio.urn.like(URN_SERVICIO + "osm-%"), Servicio.publicado.is_(True)
        )
    )
    recursos = await db.execute(
        select(RecursoTuristico).where(
            RecursoTuristico.urn.like(URN_RECURSO + "osm-%"),
            RecursoTuristico.publicado.is_(True),
        )
    )
    for obj in [*servicios.scalars(), *recursos.scalars()]:
        if obj.urn not in vistos:
            obj.publicado = False
            cuenta["despublicados"] += 1
    return cuenta


_PAUSA_SEGUNDOS = 1.5  # entre recursos: las APIs de Wikimedia limitan con 429


async def retirar_imagenes_automaticas(db: AsyncSession, todas: bool = False) -> int:
    """Quita fotos puestas por este importador para volver a buscarlas.

    Siempre retira las que delatan no ser del lugar (fotos desde el espacio,
    mapas…); con ``todas=True`` retira todas las automáticas. Las fotos subidas
    desde el CMS (sin ``imagen_credito``) nunca se tocan.
    """
    recursos = (
        await db.execute(
            select(RecursoTuristico).where(
                func.cardinality(RecursoTuristico.imagenes) > 0,
                RecursoTuristico.enlaces_externos.is_not(None),
            )
        )
    ).scalars()
    retiradas = 0
    for r in recursos:
        enlaces = dict(r.enlaces_externos or {})
        credito = enlaces.get("imagen_credito")
        if not credito or not (todas or credito_no_representativo(credito)):
            continue
        enlaces.pop("imagen_credito", None)
        enlaces.pop("imagen_fuente", None)
        r.enlaces_externos = enlaces or None
        r.imagenes = None
        retiradas += 1
        logger.info("Imagen automática retirada", recurso=r.nombre, credito=credito)
    return retiradas


async def completar_imagenes(
    db: AsyncSession, cli: httpx.AsyncClient, limite: int | None = None
) -> dict[str, int]:
    """Añade foto (Wikipedia/Commons) a los recursos publicados que no la tienen."""
    geom = cast(RecursoTuristico.ubicacion, Geometry)
    filas = (
        await db.execute(
            select(RecursoTuristico, func.ST_Y(geom), func.ST_X(geom))
            .where(
                RecursoTuristico.publicado.is_(True),
                RecursoTuristico.deleted_at.is_(None),
                RecursoTuristico.ubicacion.is_not(None),
                ~RecursoTuristico.urn.like(URN_RECURSO + "osm-%"),  # negocios: sin foto ajena
                or_(
                    RecursoTuristico.imagenes.is_(None),
                    func.cardinality(RecursoTuristico.imagenes) == 0,
                ),
            )
            .order_by(RecursoTuristico.categoria, RecursoTuristico.nombre)
        )
    ).all()
    if limite:
        filas = filas[:limite]
    cuenta = {"revisados": 0, "wikipedia": 0, "commons_cercana": 0, "sin_imagen": 0}
    for r, lat, lon in filas:
        cuenta["revisados"] += 1
        radio = 2500 if r.categoria == "ruta" else 1000
        try:
            img = await buscar_imagen(cli, r.nombre, float(lat), float(lon), radio)
        except httpx.HTTPError as exc:
            logger.warning("Fallo buscando imagen", recurso=r.nombre, error=str(exc))
            img = None
        if img is None:
            cuenta["sin_imagen"] += 1
            logger.info("Sin imagen libre", recurso=r.nombre)
        else:
            r.imagenes = [img.url]
            r.enlaces_externos = {
                **(r.enlaces_externos or {}),
                "imagen_credito": img.credito,
                "imagen_fuente": img.pagina,
            }
            cuenta["wikipedia" if img.origen == "wikipedia" else "commons_cercana"] += 1
            logger.info("Imagen asignada", recurso=r.nombre, origen=img.origen, credito=img.credito)
        await asyncio.sleep(_PAUSA_SEGUNDOS)
    return cuenta


async def ejecutar(
    solo: str | None = None,
    dry_run: bool = False,
    limite: int | None = None,
    rehacer: bool = False,
) -> int:
    s = get_settings()
    async with (
        httpx.AsyncClient(
            timeout=90, headers={"User-Agent": user_agent(s.contenidos_contacto)}
        ) as cli,
        AsyncSessionLocal() as db,
    ):
        if solo in (None, "osm"):
            elementos = await descargar_osm(cli, s.overpass_url)
            n_serv = sum(1 for e in elementos if e.clase == "servicio")
            print(
                f"OSM: {n_serv} establecimientos de gastronomía · "
                f"{len(elementos) - n_serv} de artesanía"
            )
            print("   ", await importar_osm(db, elementos))
        if solo in (None, "imagenes"):
            retiradas = await retirar_imagenes_automaticas(db, todas=rehacer)
            if retiradas:
                print(f"Imágenes automáticas retiradas para rebuscar: {retiradas}")
            await db.flush()
            print("Imágenes:", await completar_imagenes(db, cli, limite))
        if dry_run:
            await db.rollback()
            print("Dry-run: no se ha guardado nada.")
        else:
            await db.commit()
            print("Guardado.")
    return 0


def main() -> None:
    configure_logging()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--solo", choices=["osm", "imagenes"], default=None)
    p.add_argument("--dry-run", action="store_true", help="consulta las fuentes sin guardar")
    p.add_argument("--limite", type=int, default=None, help="máximo de recursos para imágenes")
    p.add_argument(
        "--rehacer",
        action="store_true",
        help="vuelve a buscar todas las fotos puestas por el importador (no las del CMS)",
    )
    a = p.parse_args()
    sys.exit(asyncio.run(ejecutar(a.solo, a.dry_run, a.limite, a.rehacer)))


if __name__ == "__main__":
    main()
