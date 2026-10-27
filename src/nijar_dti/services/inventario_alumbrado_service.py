"""Importación del inventario real de alumbrado exportado de la plataforma WeLight.

El Ayuntamiento recibe de WeLight (gestor del alumbrado) un Excel "Inventory
para Níjar" con una fila por punto de luz y 54 columnas: luminaria (tipo,
fabricante, coordenadas, estado), soporte, equipo auxiliar (driver), lámpara
(tecnología, potencia, temperatura de color) y cuadro de mando (nombre,
ubicación, CUPS y telegestión: dispositivo UCA de SOL-X).

Este servicio sustituye las luminarias, cuadros y zonas de demostración por
ese inventario:

- **Zona** = núcleo del municipio, tomado del nombre del cuadro
  ("SAN ISIDRO - CM 022" → San Isidro). Los cuadros sin núcleo en el nombre se
  asignan al núcleo más cercano.
- **Cuadro de mando** = cada "PANEL NAME", con sus CUPS (enlace con Datadis),
  su potencia instalada (suma de las lámparas) y la telegestión declarada.
- **Luminaria** = cada fila, con tecnología, potencia y consumo mensual
  *estimado* (potencia × horas de encendido anuales / 12).

El inventario no trae telemetría: averías, comunicaciones y regulación en
tiempo real llegarán al integrar la telegestión SOL-X. Hasta entonces los
cuadros quedan con ``comunicaciones = "sin telemetría"`` y el panel lo indica.

Uso: ``python -m nijar_dti.workers.importar_inventario_alumbrado Inventario.xlsx``
"""

from __future__ import annotations

import io
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from nijar_dti.core.logging import get_logger
from nijar_dti.models.alumbrado import SIN_TELEMETRIA, CuadroMando, Luminaria, ZonaAlumbrado
from nijar_dti.models.verticales import SuministroEnergia

logger = get_logger(__name__)

FUENTE = "welight"
HORAS_ENCENDIDO_ANIO = 4100  # alumbrado público en España: ~11,2 h/día de media
ANIO_MINIMO = 1980  # fechas anteriores (p. ej. 01/01/1970) = sin dato

# Núcleos que ya usan otras partes de la plataforma con un identificador corto.
_ZONAS_CONOCIDAS = {
    "VILLA DE NIJAR": ("nijar", "Níjar casco"),
    "SAN JOSE": ("sanjose", "San José"),
    "CAMPOHERMOSO": ("campo", "Campohermoso"),
    "RODALQUILAR": ("roda", "Rodalquilar"),
    "LAS NEGRAS": ("negras", "Las Negras"),
    "LOS ALBARICOQUES": ("albar", "Los Albaricoques"),
}
_ACENTOS = {
    "Jose": "José",
    "Fernan": "Fernán",
    "Perez": "Pérez",
    "Poligono": "Polígono",
    "Rodon": "Rodón",
    "Martinez": "Martínez",
    "Nijar": "Níjar",
}
_PARTICULAS = {"de", "del", "la", "las", "los", "el", "y"}


@dataclass
class InventarioAlumbrado:
    zonas: list[dict[str, Any]] = field(default_factory=list)
    cuadros: list[dict[str, Any]] = field(default_factory=list)
    luminarias: list[dict[str, Any]] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    def resumen(self) -> dict[str, Any]:
        tec = Counter(x["tecnologia"] for x in self.luminarias)
        cups = {c for q in self.cuadros for c in q["metadatos"]["cups"]}
        tele = Counter(q["metadatos"]["telegestion"]["fabricante"] for q in self.cuadros)
        return {
            "luminarias": len(self.luminarias),
            "cuadros": len(self.cuadros),
            "zonas": len(self.zonas),
            "cups": len(cups),
            "tecnologia": dict(tec.most_common()),
            "potencia_kw": round(sum(x["potencia_w"] for x in self.luminarias) / 1000, 1),
            "telegestion": dict(tele.most_common()),
            "avisos": self.avisos,
        }


# ------------------------------------------------------------ utilidades -----
def _norm(texto: Any) -> str:
    t = "".join(
        c for c in unicodedata.normalize("NFD", str(texto or "")) if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"\s+", " ", t).strip().upper()


def _texto(valor: Any) -> str | None:
    """Texto limpio; ``DESCONOCIDO`` y vacíos son ``None``."""
    if valor is None:
        return None
    t = re.sub(r"\s+", " ", str(valor)).strip()
    return None if not t or _norm(t) in {"DESCONOCIDO", "DESCONOCIDA", "-", "0"} else t


def _num(valor: Any) -> float | None:
    if isinstance(valor, int | float) and not (isinstance(valor, float) and math.isnan(valor)):
        return float(valor)
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None


def nombre_zona(nucleo: str) -> str:
    """ "LA ISLETA DEL MORO" → "La Isleta del Moro" (con tildes conocidas)."""
    palabras = []
    for i, p in enumerate(nucleo.lower().split()):
        p = p if i and p in _PARTICULAS else p.capitalize()
        palabras.append(_ACENTOS.get(p, p))
    return " ".join(palabras)


def slug_zona(nucleo: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _norm(nucleo).lower()).strip("-")[:40]


def zona_de_cuadro(nombre_cuadro: str) -> tuple[str, str] | None:
    """Zona (id, nombre) a partir del nombre del cuadro: "SAN JOSE - CM 004"."""
    if " - " not in nombre_cuadro:
        return None
    nucleo = _norm(nombre_cuadro.split(" - ")[0])
    if not nucleo:
        return None
    return _ZONAS_CONOCIDAS.get(nucleo, (slug_zona(nucleo), nombre_zona(nucleo)))


def tecnologia_de(tipo_lampara: Any) -> str:
    t = _norm(tipo_lampara)
    if t == "LED":
        return "led"
    if t in {"VSAP", "VAPOR DE SODIO A ALTA PRESION"} or "SODIO" in t:
        return "vsap"
    if t in {"HM", "HALOGENURO METALICO"} or "HALOGENURO" in t:
        return "hm"
    if "SOLAR" in t:
        return "solar"
    return "desconocida"


def anio_de(epoch: Any) -> int | None:
    """Fecha de WeLight (segundos Unix) → año; 1970 y similares = sin dato."""
    n = _num(epoch)
    if not n:
        return None
    anio = datetime.fromtimestamp(n, UTC).year
    return anio if anio >= ANIO_MINIMO else None


def consumo_mes_estimado(potencia_w: float) -> float:
    return round(potencia_w * HORAS_ENCENDIDO_ANIO / 12 / 1000, 2)


def _distancia2(a: tuple[float, float], b: tuple[float, float]) -> float:
    return (a[0] - b[0]) ** 2 + ((a[1] - b[1]) * math.cos(math.radians(a[0]))) ** 2


# ------------------------------------------------------------ lectura --------
def leer_inventario_welight(contenido: bytes) -> InventarioAlumbrado:
    """Convierte el Excel de WeLight en zonas, cuadros y luminarias de la plataforma."""
    import openpyxl  # type: ignore[import-untyped]

    libro = openpyxl.load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    try:
        hoja = libro.worksheets[0]
        filas = hoja.iter_rows(values_only=True)
        cabecera = [_norm(h).split(" (")[0].split(" [")[0] for h in next(filas)]
        datos = [list(f) for f in filas if any(v is not None for v in f)]
    finally:
        libro.close()

    col = {h: i for i, h in enumerate(cabecera) if h}
    obligatorias = ["LUMINARY IDENTIFIER", "LAMP TYPE", "LAMP POWER", "PANEL NAME"]
    faltan = [c for c in obligatorias if c not in col]
    if faltan:
        raise ValueError(f"No es un inventario de WeLight: faltan las columnas {faltan}")

    def v(fila: list[Any], nombre: str) -> Any:
        i = col.get(nombre)
        return fila[i] if i is not None and i < len(fila) else None

    inv = InventarioAlumbrado()
    cuadros: dict[str, dict[str, Any]] = {}
    sin_nucleo: list[str] = []
    vistos: set[str] = set()
    for fila in datos:
        ident = _texto(v(fila, "LUMINARY IDENTIFIER"))
        nombre_cm = _texto(v(fila, "PANEL NAME")) or "SIN CUADRO"
        if not ident:
            inv.avisos.append("Fila sin identificador de luminaria: omitida")
            continue
        codigo = f"WL-{ident}"[:20]
        if codigo in vistos:
            inv.avisos.append(f"Identificador repetido {ident}: omitida la segunda fila")
            continue
        vistos.add(codigo)

        cm = cuadros.get(nombre_cm)
        if cm is None:
            zona = zona_de_cuadro(nombre_cm)
            if zona is None:
                sin_nucleo.append(nombre_cm)
            cm = cuadros[nombre_cm] = {
                "nombre": nombre_cm[:120],
                "zona": zona,
                "ubicacion": _texto(v(fila, "PANEL ADDRESS")),
                "latitud": _num(v(fila, "PANEL LATITUDE")),
                "longitud": _num(v(fila, "PANEL LONGITUDE")),
                "cups": set(),
                "potencia_w": 0.0,
                "luminarias": 0,
                "telegestion": Counter(),
                "tipo": _texto(v(fila, "PANEL TYPE")),
                "fabricante": _texto(v(fila, "PANEL MANUFACTURER")),
                "anio_instalacion": anio_de(v(fila, "PANEL INSTALLATION DATE")),
            }
        cups = _texto(v(fila, "PANEL CUPS"))
        if cups:
            cm["cups"].add(cups.replace(" ", "").upper())
        cm["telegestion"][
            (
                _texto(v(fila, "PANEL TELEMANAGEMENT DEVICE")),
                _texto(v(fila, "PANEL TELEMANAGEMENT MANUFACTURER")),
            )
        ] += 1
        potencia = _num(v(fila, "LAMP POWER")) or 0.0
        cm["potencia_w"] += potencia
        cm["luminarias"] += 1

        marca = " ".join(
            x
            for x in (
                _texto(v(fila, "LUMINARY MANUFACTURER")),
                _texto(v(fila, "LUMINARY TYPE")),
                _texto(v(fila, "LUMINARY MODEL")),
            )
            if x
        )
        inv.luminarias.append(
            {
                "codigo": codigo,
                "cuadro": nombre_cm,
                "tecnologia": tecnologia_de(v(fila, "LAMP TYPE")),
                "direccion": (_texto(v(fila, "LUMINARY ADDRESS")) or "")[:255] or None,
                "potencia_w": int(round(potencia)),
                "marca_modelo": marca[:120] or None,
                "anio_instalacion": anio_de(v(fila, "LUMINARY INSTALLATION DATE")),
                "consumo_mes_kwh": consumo_mes_estimado(potencia),
                "latitud": _num(v(fila, "LUMINARY LATITUDE")),
                "longitud": _num(v(fila, "LUMINARY LONGITUDE")),
                "metadatos": {
                    "fuente": FUENTE,
                    "identificador": ident,
                    "soporte": _texto(v(fila, "SUPPORT TYPE")),
                    "altura_m": _num(v(fila, "SUPPORT HEIGHT")),
                    "driver": " ".join(
                        x
                        for x in (
                            _texto(v(fila, "DEVICE MANUFACTURER")),
                            _texto(v(fila, "DEVICE TYPE")),
                        )
                        if x
                    )
                    or None,
                    "temperatura_color_k": _num(v(fila, "LAMP COLOR TEMPERATURE")) or None,
                    "estado_inventario": _texto(v(fila, "LUMINARY STATE")),
                    "grupo": _texto(v(fila, "LUMINARY GROUP")),
                },
            }
        )

    # Zonas: núcleos de los nombres de cuadro; los cuadros sin núcleo, al más cercano.
    puntos: dict[str, list[tuple[float, float]]] = defaultdict(list)
    nombres_zona: dict[str, str] = {}
    for cm in cuadros.values():
        if cm["zona"]:
            zid, znombre = cm["zona"]
            nombres_zona[zid] = znombre
            if cm["latitud"] and cm["longitud"]:
                puntos[zid].append((cm["latitud"], cm["longitud"]))
    centros = {
        z: (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps))
        for z, ps in puntos.items()
    }
    for nombre_cm in sin_nucleo:
        cm = cuadros[nombre_cm]
        if centros and cm["latitud"] and cm["longitud"]:
            punto = (float(cm["latitud"]), float(cm["longitud"]))
            zid = min(centros, key=lambda z: _distancia2(centros[z], punto))
            cm["zona"] = (zid, nombres_zona[zid])
            inv.avisos.append(
                f"Cuadro '{nombre_cm}' sin núcleo en el nombre: asignado a {nombres_zona[zid]}"
            )
        else:
            cm["zona"] = ("sin-zona", "Sin zona")
            nombres_zona["sin-zona"] = "Sin zona"

    # Códigos CM-001… por orden alfabético del nombre del cuadro.
    codigos = {n: f"CM-{i + 1:03d}" for i, n in enumerate(sorted(cuadros))}
    for nombre_cm, cm in sorted(cuadros.items()):
        dispositivo, fabricante = cm["telegestion"].most_common(1)[0][0]
        inv.cuadros.append(
            {
                "codigo": codigos[nombre_cm],
                "nombre": cm["nombre"],
                "zona_id": cm["zona"][0],
                "ubicacion": (cm["ubicacion"] or "")[:255] or None,
                "potencia_kw": round(cm["potencia_w"] / 1000, 2),
                "comunicaciones": SIN_TELEMETRIA,
                "latitud": cm["latitud"],
                "longitud": cm["longitud"],
                "metadatos": {
                    "fuente": FUENTE,
                    "nombre_welight": nombre_cm,
                    "cups": sorted(cm["cups"]),
                    "luminarias": cm["luminarias"],
                    "telegestion": {"dispositivo": dispositivo, "fabricante": fabricante},
                    "tipo": cm["tipo"],
                    "fabricante": cm["fabricante"],
                    "anio_instalacion": cm["anio_instalacion"],
                },
            }
        )
    zona_cuadro = {n: cm["zona"][0] for n, cm in cuadros.items()}
    for x in inv.luminarias:
        nombre_cm = x.pop("cuadro")
        x["cuadro_codigo"] = codigos[nombre_cm]
        x["zona_id"] = zona_cuadro[nombre_cm]

    por_zona: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for x in inv.luminarias:
        por_zona[x["zona_id"]].append(x)
    for zid, lums in sorted(por_zona.items(), key=lambda kv: -len(kv[1])):
        tec = Counter(x["tecnologia"] for x in lums)
        coords = [(x["latitud"], x["longitud"]) for x in lums if x["latitud"] and x["longitud"]]
        inv.zonas.append(
            {
                "id": zid,
                "nombre": nombres_zona[zid],
                "luminarias": len(lums),
                "led": tec["led"],
                "vsap": tec["vsap"],
                "solar": tec["solar"],
                "latitud": round(sum(c[0] for c in coords) / len(coords), 6) if coords else None,
                "longitud": round(sum(c[1] for c in coords) / len(coords), 6) if coords else None,
            }
        )
    return inv


# ------------------------------------------------------------ escritura ------
async def importar(db: AsyncSession, inv: InventarioAlumbrado) -> dict[str, Any]:
    """Sustituye el inventario de alumbrado (zonas, cuadros, luminarias) por el de WeLight.

    También marca como ``tipo="alumbrado"`` los suministros eléctricos ya cargados
    de Datadis cuyo CUPS aparece en un cuadro, para que su consumo se cuente en
    la vertical de alumbrado y no en la de edificios.
    """
    if not inv.luminarias:
        raise ValueError("El inventario no contiene luminarias")
    await db.execute(delete(Luminaria))
    await db.execute(delete(CuadroMando))
    await db.execute(delete(ZonaAlumbrado))
    for z in inv.zonas:
        db.add(ZonaAlumbrado(**z))
    for c in inv.cuadros:
        db.add(CuadroMando(**c))
    for x in inv.luminarias:
        db.add(Luminaria(**x))
    await db.flush()

    cups = {c[:20] for q in inv.cuadros for c in q["metadatos"]["cups"]}
    marcados = 0
    if cups:
        res = await db.execute(
            update(SuministroEnergia)
            .where(func.substr(SuministroEnergia.cups, 1, 20).in_(cups))
            .where(func.coalesce(SuministroEnergia.tipo, "") != "alumbrado")
            .values(tipo="alumbrado")
        )
        marcados = int(getattr(res, "rowcount", 0) or 0)
    resumen = inv.resumen() | {"suministros_marcados_alumbrado": marcados}
    logger.info(
        "Inventario de alumbrado importado", **{k: v for k, v in resumen.items() if k != "avisos"}
    )
    return resumen


async def fuente_inventario(db: AsyncSession) -> str | None:
    """``"welight"`` si el inventario cargado es el real de WeLight; None si es el de demo."""
    fila = (
        await db.execute(
            select(CuadroMando.metadatos).where(CuadroMando.metadatos.is_not(None)).limit(1)
        )
    ).scalar_one_or_none()
    return FUENTE if isinstance(fila, dict) and fila.get("fuente") == FUENTE else None
