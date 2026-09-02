"""Carga o reemplaza una capa geográfica del gemelo 2D desde un fichero GeoJSON.

Es la vía de entrada de la cartografía real (planeamiento, catastro…) que
aporte el Ayuntamiento: cada ``FeatureCollection`` se vuelca como una capa del
geoportal (`CapaGeografica` + sus `ElementoGeografico`), sin tocar el esquema.

Uso (dentro del contenedor de la API o con el entorno activado):

    python -m nijar_dti.data.cargar_capa fichero.geojson --codigo clasificacion_suelo \
        --nombre "Clasificación del suelo" --grupo clasificacion --fuente "PGOU vigente"

    # Sustituir la geometría de una capa existente (p. ej. la demo) por la real:
    python -m nijar_dti.data.cargar_capa pgou.geojson --codigo clasificacion_suelo --reemplazar

El estilo y la visibilidad de las capas ya cargadas se gestionan desde el
panel («Capas del gemelo»); este comando gestiona la geometría y el alta.
Si el fichero está en otro formato (Shapefile, DXF…), conviértase antes a
GeoJSON (p. ej. con ``ogr2ogr -f GeoJSON salida.geojson entrada.shp``).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from geoalchemy2 import WKTElement
from sqlalchemy import delete, func, select

from nijar_dti.core.database import AsyncSessionLocal
from nijar_dti.core.logging import configure_logging, get_logger
from nijar_dti.models.geografia import (
    CapaGeografica,
    ElementoGeografico,
    GrupoCapa,
    TipoGeometria,
)

log = get_logger(__name__)

# GeoJSON → tipo predominante de la capa
_TIPO_POR_GEOMETRIA = {
    "Point": TipoGeometria.PUNTO,
    "MultiPoint": TipoGeometria.PUNTO,
    "LineString": TipoGeometria.LINEA,
    "MultiLineString": TipoGeometria.LINEA,
    "Polygon": TipoGeometria.POLIGONO,
    "MultiPolygon": TipoGeometria.POLIGONO,
}


def _coords_wkt(coords: list[Any]) -> str:
    """``[lon, lat]`` (o anidados) → texto de coordenadas WKT."""
    if coords and isinstance(coords[0], (int, float)):
        lon, lat = float(coords[0]), float(coords[1])
        return f"{lon} {lat}"
    return ", ".join(_coords_wkt(c) for c in coords)


def geojson_a_wkt(geometry: dict[str, Any]) -> str:
    """Convierte una geometría GeoJSON (RFC 7946) a WKT.

    Cobertura: Point, MultiPoint, LineString, MultiLineString, Polygon y
    MultiPolygon — los tipos que produce cualquier exportación de cartografía
    municipal. GeoJSON usa orden ``[lon, lat]``, igual que WKT.
    """
    tipo = geometry.get("type")
    coords = geometry.get("coordinates")
    if not tipo or coords is None:
        raise ValueError("Geometría GeoJSON sin 'type' o 'coordinates'")
    if tipo == "Point":
        return f"POINT({_coords_wkt(coords)})"
    if tipo == "MultiPoint":
        return "MULTIPOINT(" + ", ".join(f"({_coords_wkt(c)})" for c in coords) + ")"
    if tipo == "LineString":
        return f"LINESTRING({_coords_wkt(coords)})"
    if tipo == "MultiLineString":
        return "MULTILINESTRING(" + ", ".join(f"({_coords_wkt(c)})" for c in coords) + ")"
    if tipo == "Polygon":
        return "POLYGON(" + ", ".join(f"({_coords_wkt(anillo)})" for anillo in coords) + ")"
    if tipo == "MultiPolygon":
        poligonos = [
            "(" + ", ".join(f"({_coords_wkt(anillo)})" for anillo in poly) + ")" for poly in coords
        ]
        return "MULTIPOLYGON(" + ", ".join(poligonos) + ")"
    raise ValueError(f"Tipo de geometría no soportado: {tipo}")


def leer_features(ruta: Path) -> list[dict[str, Any]]:
    """Lee el fichero y devuelve la lista de features con geometría."""
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if datos.get("type") == "FeatureCollection":
        features = datos.get("features") or []
    elif datos.get("type") == "Feature":
        features = [datos]
    else:
        raise ValueError("El fichero no es un GeoJSON Feature/FeatureCollection")
    con_geometria = [f for f in features if f.get("geometry")]
    if not con_geometria:
        raise ValueError("El GeoJSON no contiene ninguna feature con geometría")
    return con_geometria


def _nombre_elemento(props: dict[str, Any], campo_nombre: str, indice: int) -> str:
    for clave in (campo_nombre, "nombre", "name", "NOMBRE", "rotulo", "label"):
        valor = props.get(clave)
        if valor:
            return str(valor)[:255]
    return f"Elemento {indice + 1}"


async def cargar(args: argparse.Namespace) -> None:
    features = leer_features(Path(args.fichero))
    tipo_geo = _TIPO_POR_GEOMETRIA.get(features[0]["geometry"].get("type"))
    if tipo_geo is None:
        raise ValueError(f"Geometría no soportada: {features[0]['geometry'].get('type')}")

    async with AsyncSessionLocal() as db:
        capa = (
            await db.execute(select(CapaGeografica).where(CapaGeografica.codigo == args.codigo))
        ).scalar_one_or_none()

        if capa is None:
            capa = CapaGeografica(
                codigo=args.codigo,
                nombre=args.nombre or args.codigo.replace("_", " ").capitalize(),
                grupo=GrupoCapa(args.grupo),
                tipo_geometria=tipo_geo,
                descripcion=args.descripcion,
                fuente=args.fuente,
            )
            db.add(capa)
            await db.flush()
            log.info("Capa '%s' creada", args.codigo)
        else:
            n_existentes = int(
                (
                    await db.execute(
                        select(func.count())
                        .select_from(ElementoGeografico)
                        .where(ElementoGeografico.capa_id == capa.id)
                    )
                ).scalar_one()
                or 0
            )
            if n_existentes and not args.reemplazar:
                raise SystemExit(
                    f"La capa '{args.codigo}' ya tiene {n_existentes} elementos. "
                    "Añade --reemplazar para sustituirlos por los del fichero."
                )
            if n_existentes:
                await db.execute(
                    delete(ElementoGeografico).where(ElementoGeografico.capa_id == capa.id)
                )
                log.info("Eliminados %d elementos previos de '%s'", n_existentes, args.codigo)
            # La carga de datos reales sustituye a la demo: refleja metadatos
            if args.nombre:
                capa.nombre = args.nombre
            if args.descripcion:
                capa.descripcion = args.descripcion
            if args.fuente:
                capa.fuente = args.fuente
            capa.tipo_geometria = tipo_geo

        for i, feature in enumerate(features):
            props = dict(feature.get("properties") or {})
            refcat = props.get(args.campo_refcat) or props.get("referencia_catastral")
            db.add(
                ElementoGeografico(
                    capa_id=capa.id,
                    nombre=_nombre_elemento(props, args.campo_nombre, i),
                    geometria=WKTElement(geojson_a_wkt(feature["geometry"]), srid=4326),
                    codigo=str(props[args.campo_codigo])[:120]
                    if props.get(args.campo_codigo)
                    else None,
                    referencia_catastral=str(refcat)[:20] if refcat else None,
                    propiedades=props or None,
                    orden=i,
                )
            )
        await db.commit()
        log.info("Capa '%s': %d elementos cargados", args.codigo, len(features))


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(
        description="Carga una capa geográfica del gemelo 2D desde un GeoJSON"
    )
    parser.add_argument("fichero", help="Ruta del fichero GeoJSON (FeatureCollection)")
    parser.add_argument("--codigo", required=True, help="Código estable de la capa (p. ej. pgou)")
    parser.add_argument("--nombre", help="Nombre visible de la capa")
    parser.add_argument(
        "--grupo",
        default=GrupoCapa.OTRAS.value,
        choices=[g.value for g in GrupoCapa],
        help="Grupo temático (solo al crear la capa)",
    )
    parser.add_argument("--descripcion", help="Descripción de la capa")
    parser.add_argument("--fuente", help="Procedencia del dato (organismo, expediente…)")
    parser.add_argument(
        "--campo-nombre",
        default="nombre",
        help="Propiedad del GeoJSON usada como nombre de cada elemento",
    )
    parser.add_argument(
        "--campo-codigo",
        default="codigo",
        help="Propiedad usada como código de cada elemento",
    )
    parser.add_argument(
        "--campo-refcat",
        default="referencia_catastral",
        help="Propiedad con la referencia catastral (si existe)",
    )
    parser.add_argument(
        "--reemplazar",
        action="store_true",
        help="Sustituir los elementos existentes de la capa por los del fichero",
    )
    try:
        asyncio.run(cargar(parser.parse_args()))
    except (ValueError, OSError) as exc:
        log.error("No se pudo cargar la capa: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
