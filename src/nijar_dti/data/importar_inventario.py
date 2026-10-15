"""Importa el Inventario Municipal de Bienes (Urbana) como capas del gemelo 2D.

Entrada: los GeoJSON que genera ``tools/dwg2geojson/convertir.mjs`` a partir de
los DWG del Ayuntamiento (uno por núcleo, coordenadas UTM en metros). Este
comando los transforma a WGS84 con PostGIS y los vuelca en una capa por
categoría de la leyenda del plano («Inventario · Equipamientos», «Inventario ·
Red viaria»…), dentro del grupo «Inventario de bienes».

Idempotente por núcleo: reimportar un núcleo sustituye solo sus elementos y deja
intactos los de los demás núcleos. El estilo de cada capa se puede retocar
después desde el panel («Capas del gemelo»).

Uso (dentro del contenedor de la API):

    python -m nijar_dti.data.importar_inventario /tmp/inventario_geojson/
    python -m nijar_dti.data.importar_inventario el-viso.geojson --srid 23030   # si fuera ED50
    python -m nijar_dti.data.importar_inventario /tmp/inventario_geojson/ --dry-run

Lo normal es lanzarlo con ``scripts/importar_inventario.sh inventario.zip``, que
convierte los DWG e importa todo de una vez.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.core.database import AsyncSessionLocal
from nijar_dti.core.logging import configure_logging
from nijar_dti.data.cargar_capa import geojson_a_wkt
from nijar_dti.models.geografia import (
    CapaGeografica,
    ElementoGeografico,
    GrupoCapa,
    TipoGeometria,
)

# Rectángulo que envuelve el término municipal de Níjar (WGS84), con margen
LAT_NIJAR = (36.70, 37.08)
LON_NIJAR = (-2.36, -1.85)

FUENTE = "Inventario Municipal de Bienes · Urbana (Ayuntamiento de Níjar, actualización 2025)"
SRID_POR_DEFECTO = 25830  # ETRS89 / UTM huso 30N


@dataclass(frozen=True)
class EstiloCategoria:
    nombre: str
    color: str
    color_borde: str
    orden: int
    tipo: TipoGeometria = TipoGeometria.POLIGONO
    opacidad: float = 0.55


# Colores tomados de la leyenda de los planos del inventario
CATEGORIAS: dict[str, EstiloCategoria] = {
    "red_viaria": EstiloCategoria("Red viaria", "#8E8A86", "#5A5652", 10),
    "aparcamiento": EstiloCategoria("Aparcamientos", "#B9978F", "#7A5A52", 11),
    "via_ferrea": EstiloCategoria("Vía férrea", "#4F7F45", "#2F5A27", 12),
    "via_pecuaria": EstiloCategoria(
        "Vía pecuaria", "#B5651D", "#B5651D", 13, TipoGeometria.LINEA, 0.9
    ),
    "patrimonio_suelo": EstiloCategoria("Patrimonio público del suelo", "#F1DDB8", "#B08A4E", 20),
    "residencial": EstiloCategoria("Residencial patrimonial", "#A8D8F0", "#3C88B5", 21),
    "espacio_libre": EstiloCategoria("Espacio libre público", "#DCE98F", "#8AA024", 22),
    "peatonal_ajardinado": EstiloCategoria("Peatonal ajardinado", "#A6D06A", "#5E8F22", 23),
    "equipamiento": EstiloCategoria("Equipamientos", "#8FB3E0", "#2F5E9E", 24),
    "infraestructura": EstiloCategoria("Infraestructuras", "#BDE3F6", "#4A9BC4", 25),
    "edificio": EstiloCategoria("Edificios", "#3E6FB0", "#1F3F73", 26, opacidad=0.8),
    "parcela": EstiloCategoria("Parcelas", "#DDDDDD", "#888888", 27, opacidad=0.3),
}


def codigo_capa(categoria: str) -> str:
    return f"inventario_{categoria}"


def nombre_elemento(props: dict[str, Any]) -> str:
    """«U-PB-3» (o varios códigos) o, sin código, «Red viaria · El Viso»."""
    codigos = props.get("codigos") or []
    if codigos:
        return ", ".join(codigos)[:255]
    cat = CATEGORIAS.get(props.get("categoria", ""))
    return f"{cat.nombre if cat else 'Bien'} · {props.get('nucleo', '')}"[:255]


def propiedades_ficha(props: dict[str, Any]) -> dict[str, Any]:
    """Propiedades que se muestran en la ficha del mapa (orden = orden de lectura)."""
    cat = CATEGORIAS.get(props.get("categoria", ""))
    ficha: dict[str, Any] = {
        "núcleo": props.get("nucleo"),
        "categoría": cat.nombre if cat else props.get("categoria"),
        "códigos": ", ".join(props.get("codigos") or []) or None,
        "notas": "; ".join(props.get("notas") or []) or None,
        "superficie_m2": props.get("superficie_m2"),
        "fuente": "Inventario Municipal de Bienes 2025",
        "_capa_dwg": props.get("capa_dwg"),
        "_origen": props.get("origen"),
        "_nucleo": props.get("nucleo"),  # clave estable para reimportar por núcleo
    }
    return {k: v for k, v in ficha.items() if v not in (None, "")}


def leer_colecciones(rutas: list[str]) -> list[dict[str, Any]]:
    ficheros: list[Path] = []
    for r in rutas:
        p = Path(r)
        ficheros += sorted(p.glob("*.geojson")) if p.is_dir() else [p]
    colecciones = []
    for f in ficheros:
        datos = json.loads(f.read_text(encoding="utf-8"))
        if datos.get("type") != "FeatureCollection" or not datos.get("nucleo"):
            raise ValueError(f"{f.name}: no es un GeoJSON del convertidor (falta «nucleo»)")
        colecciones.append(datos)
    if not colecciones:
        raise ValueError("No se ha encontrado ningún .geojson")
    return colecciones


async def _capa(db: AsyncSession, categoria: str) -> CapaGeografica:
    codigo = codigo_capa(categoria)
    capa = (
        await db.execute(select(CapaGeografica).where(CapaGeografica.codigo == codigo))
    ).scalar_one_or_none()
    if capa is None:
        est = CATEGORIAS[categoria]
        capa = CapaGeografica(
            codigo=codigo,
            nombre=f"Inventario · {est.nombre}",
            grupo=GrupoCapa.INVENTARIO,
            tipo_geometria=est.tipo,
            descripcion=f"{est.nombre} del Inventario Municipal de Bienes (Urbana)",
            color=est.color,
            color_borde=est.color_borde,
            opacidad=est.opacidad,
            campo_etiqueta="códigos",
            orden=100 + est.orden,
            fuente=FUENTE,
        )
        db.add(capa)
        await db.flush()
    return capa


async def importar(
    db: AsyncSession, colecciones: list[dict[str, Any]], srid: int
) -> dict[str, Any]:
    resumen: dict[str, Any] = {}
    for fc in colecciones:
        nucleo = fc["nucleo"]
        por_cat: dict[str, int] = {}
        capas_tocadas: set[str] = set()
        for i, feat in enumerate(fc.get("features") or []):
            props = feat.get("properties") or {}
            categoria = props.get("categoria")
            if categoria not in CATEGORIAS or not feat.get("geometry"):
                continue
            capa = await _capa(db, categoria)
            if capa.codigo not in capas_tocadas:
                # Reimportación: fuera los elementos previos de este núcleo en la capa
                await db.execute(
                    delete(ElementoGeografico).where(
                        ElementoGeografico.capa_id == capa.id,
                        ElementoGeografico.propiedades["_nucleo"].as_string() == nucleo,
                    )
                )
                capas_tocadas.add(capa.codigo)
            dimension = 2 if CATEGORIAS[categoria].tipo == TipoGeometria.LINEA else 3
            geom = func.ST_CollectionExtract(
                func.ST_MakeValid(
                    func.ST_Transform(
                        func.ST_SetSRID(
                            func.ST_GeomFromText(geojson_a_wkt(feat["geometry"])), srid
                        ),
                        4326,
                    )
                ),
                dimension,
            )
            db.add(
                ElementoGeografico(
                    capa_id=capa.id,
                    nombre=nombre_elemento(props),
                    geometria=geom,
                    codigo=(props.get("codigos") or [None])[0],
                    propiedades=propiedades_ficha(props),
                    orden=i,
                )
            )
            por_cat[categoria] = por_cat.get(categoria, 0) + 1
        resumen[nucleo] = por_cat
        await db.flush()
    return resumen


def _punto_utm(fc: dict[str, Any]) -> tuple[float, float] | None:
    """Centro UTM del núcleo (del convertidor) o, si falta, el primer vértice."""
    if fc.get("centro_utm"):
        x, y = fc["centro_utm"]
        return float(x), float(y)
    for feat in fc.get("features") or []:
        c = (feat.get("geometry") or {}).get("coordinates")
        while isinstance(c, list) and c and isinstance(c[0], list):
            c = c[0]
        if isinstance(c, list) and len(c) >= 2:
            return float(c[0]), float(c[1])
    return None


def dentro_de_nijar(lat: float, lon: float) -> bool:
    return LAT_NIJAR[0] <= lat <= LAT_NIJAR[1] and LON_NIJAR[0] <= lon <= LON_NIJAR[1]


async def centro_wgs84(
    db: AsyncSession, fc: dict[str, Any], srid: int
) -> tuple[float, float] | None:
    p = _punto_utm(fc)
    if p is None:
        return None
    punto = func.ST_Transform(func.ST_SetSRID(func.ST_MakePoint(p[0], p[1]), srid), 4326)
    lat, lon = (await db.execute(select(func.ST_Y(punto), func.ST_X(punto)))).one()
    return float(lat), float(lon)


async def _main(a: argparse.Namespace) -> int:
    colecciones = leer_colecciones(a.rutas)
    async with AsyncSessionLocal() as db:
        # Comprobación por núcleo: su centro debe caer en el término de Níjar
        # (detecta coordenadas locales, otro sistema de referencia o restos).
        validas = []
        for fc in colecciones:
            c = await centro_wgs84(db, fc, a.srid)
            ok = c is not None and dentro_de_nijar(*c)
            pos = f"{c[0]:.4f}, {c[1]:.4f}" if c else "sin coordenadas"
            if ok or a.incluir_fuera:
                validas.append(fc)
                print(f"  {'·' if ok else '⚠'} {fc['nucleo']}: centro {pos}")
            else:
                print(f"  ⚠ {fc['nucleo']}: centro {pos} FUERA del término de Níjar → no se importa"
                      f" (revisar el DWG; --incluir-fuera para forzar)")  # fmt: skip
        resumen = await importar(db, validas, a.srid)
        # Comprobación de que cae en Níjar (detecta un sistema de coordenadas erróneo)
        centro = (
            await db.execute(
                select(
                    func.ST_AsText(func.ST_Centroid(func.ST_Collect(ElementoGeografico.geometria)))
                )
                .join(CapaGeografica, CapaGeografica.id == ElementoGeografico.capa_id)
                .where(CapaGeografica.grupo == GrupoCapa.INVENTARIO)
            )
        ).scalar_one_or_none()
        for nucleo, por_cat in resumen.items():
            total = sum(por_cat.values())
            print(f"✔ {nucleo}: {total} elementos · " + json.dumps(por_cat, ensure_ascii=False))
        print(f"Centro del inventario cargado (WGS84): {centro}")
        if a.dry_run:
            await db.rollback()
            print("Dry-run: no se ha guardado nada.")
        else:
            await db.commit()
            print("Guardado. Recarga el Gemelo vivo 2D: grupo «Inventario de bienes».")
    return 0


def main() -> None:
    configure_logging()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument(
        "rutas", nargs="+", help="Ficheros .geojson del convertidor o carpetas con ellos"
    )
    p.add_argument(
        "--srid",
        type=int,
        default=SRID_POR_DEFECTO,
        help="EPSG de las coordenadas del DWG (25830 = ETRS89 UTM30N; 23030 = ED50)",
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--incluir-fuera",
        action="store_true",
        help="importar también los núcleos cuyo centro cae fuera del término de Níjar",
    )
    try:
        sys.exit(asyncio.run(_main(p.parse_args())))
    except (ValueError, OSError) as exc:
        print(f"✘ {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
