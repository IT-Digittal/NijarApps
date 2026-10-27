"""Clientes HTTP de las fuentes oficiales del contexto turístico (sin credenciales).

- **INE** — API Tempus3 (``servicios.ine.es/wstempus``): serie por código con
  ``DATOS_SERIE/{codigo}?nult=N``. Si la API está caída (el INE la para a
  menudo por mantenimiento) se recurre al fichero JSON de la tabla completa
  que publica INEbase (``www.ine.es/jaxiT3/files/t/es/json/{tabla}.json``).
- **AENA** — no tiene API: publica cada mes un Excel "Estadísticas de tráfico"
  en ``aena.es/es/estadisticas/informes-mensuales.html?anio=AAAA``. Se
  descargan esos Excel y se lee la fila del aeropuerto en la hoja
  "Ranking mensual" (pasajeros, llegadas + salidas).
- **Junta de Andalucía** — API BADEA del IECA (``/rest/v1.0/consulta/{id}``).

Todas las funciones devuelven puntos mensuales ``(AAAA-MM, valor, provisional)``
y lanzan ``ContextoConnectorError`` si la fuente no responde o cambia de formato.
"""

from __future__ import annotations

import io
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

import httpx

from nijar_dti.connectors.contexto.base import ContextoConnectorError

TIMEOUT = httpx.Timeout(60.0, connect=15.0)
CABECERAS = {"User-Agent": "PlataformaDTI-Nijar/1.0 (+https://www.nijar.es)"}

INE_TEMPUS = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{codigo}?nult={n}"
INE_TABLA = "https://www.ine.es/jaxiT3/files/t/es/json/{tabla}.json"
AENA_BASE = "https://www.aena.es"
AENA_INFORMES = AENA_BASE + "/es/estadisticas/informes-mensuales.html?anio={anio}"

MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


@dataclass(frozen=True)
class PuntoMensual:
    periodo: str  # AAAA-MM
    valor: float
    provisional: bool = False


def _cliente() -> httpx.Client:
    return httpx.Client(timeout=TIMEOUT, headers=CABECERAS, follow_redirects=True)


def _sin_acentos(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    ).upper()


# ===================================================================== INE ====
def _mes_ine(dato: dict[str, Any]) -> int | None:
    """Mes de un dato INE: ``FK_Periodo`` (Tempus) o ``T3_Periodo`` "M09" (INEbase)."""
    periodo = dato.get("T3_Periodo")
    if isinstance(periodo, str) and re.fullmatch(r"M\d{2}", periodo):
        return int(periodo[1:])
    fk = dato.get("FK_Periodo")
    if isinstance(fk, int) and 1 <= fk <= 12:
        return fk
    return None


def puntos_ine(datos: Iterable[dict[str, Any]], escala: float = 1.0) -> list[PuntoMensual]:
    """Normaliza la lista ``Data`` de una serie mensual del INE."""
    salida: dict[str, PuntoMensual] = {}
    for d in datos:
        mes, anio, valor = _mes_ine(d), d.get("Anyo"), d.get("Valor")
        if mes is None or not isinstance(anio, int) or valor is None or d.get("Secreto"):
            continue
        tipo = str(d.get("T3_TipoDato") or d.get("FK_TipoDato") or "")
        provisional = tipo.lower().startswith("prov") or tipo in {"2", "3"}
        periodo = f"{anio:04d}-{mes:02d}"
        salida[periodo] = PuntoMensual(periodo, float(valor) * escala, provisional)
    return [salida[p] for p in sorted(salida)]


def serie_ine(codigo: str, tabla: int, meses: int, escala: float = 1.0) -> list[PuntoMensual]:
    """Últimos ``meses`` datos de la serie ``codigo`` (Tempus3 o, si falla, INEbase)."""
    errores: list[str] = []
    with _cliente() as http:
        try:
            r = http.get(INE_TEMPUS.format(codigo=codigo, n=meses))
            r.raise_for_status()
            puntos = puntos_ine(r.json().get("Data") or [], escala)
            if puntos:
                return puntos[-meses:]
            errores.append("Tempus3 sin datos")
        except (httpx.HTTPError, ValueError, AttributeError) as exc:
            errores.append(f"Tempus3: {exc}")
        try:
            r = http.get(INE_TABLA.format(tabla=tabla))
            r.raise_for_status()
            serie = next((s for s in r.json() if s.get("COD") == codigo), None)
            if serie is None:
                raise ContextoConnectorError(f"La tabla INE {tabla} ya no contiene {codigo}")
            puntos = puntos_ine(serie.get("Data") or [], escala)
            if puntos:
                return puntos[-meses:]
            errores.append("INEbase sin datos")
        except (httpx.HTTPError, ValueError) as exc:
            errores.append(f"INEbase: {exc}")
    raise ContextoConnectorError(f"INE {codigo} no disponible ({'; '.join(errores)})")


# ==================================================================== AENA ====
_ENLACE_BLOB = re.compile(r'href="(/sites/Satellite\?blobcol=urldata[^"]+)"')


def enlaces_aena(html: str) -> list[str]:
    """Enlaces de descarga (Excel y PDF) de la página de informes mensuales de un año."""
    vistos: dict[str, None] = {}
    for m in _ENLACE_BLOB.finditer(html):
        vistos[AENA_BASE + m.group(1).replace("&amp;", "&")] = None
    return list(vistos)


def _hoja_mensual(libro: Any) -> Any | None:
    """Hoja del dato mensual: "Ranking mensual" (desde 2024) o "FEBRERO 2023" (antes)."""
    for hoja in libro.worksheets:
        titulo = _sin_acentos(hoja.title)
        if "MENSUAL" in titulo:
            return hoja
    for hoja in libro.worksheets:
        titulo = _sin_acentos(hoja.title)
        if "ACUM" not in titulo and any(m.upper() in titulo for m in MESES):
            return hoja
    return None


_RE_PERIODO = re.compile(r"(?<!A )\b([A-Z]+)\s+(?:DE\s+)?(\d{4})\b")


def leer_excel_aena(contenido: bytes, aeropuerto: str) -> PuntoMensual | None:
    """Pasajeros del mes de ``aeropuerto`` en un Excel mensual de AENA.

    Admite los dos formatos publicados: el de 2024 en adelante (hoja "Ranking
    mensual", texto "Mensual: Septiembre de 2026") y el anterior (una hoja por
    mes, "FEBRERO DE 2023"). Los pasajeros son el bloque más a la izquierda,
    así que se toma la aparición del aeropuerto en la columna menor.
    """
    import openpyxl  # type: ignore[import-untyped]

    libro = openpyxl.load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    try:
        hoja = _hoja_mensual(libro)
        if hoja is None:
            return None
        titulo = _sin_acentos(hoja.title)
        filas = [list(f) for f in hoja.iter_rows(values_only=True)]
    finally:
        libro.close()

    periodo: str | None = None
    provisional = True
    buscado = _sin_acentos(aeropuerto)
    mejor: tuple[int, float] | None = None  # (columna, pasajeros)
    textos = [titulo] + [_sin_acentos(c) for f in filas[:12] for c in f if isinstance(c, str)]
    for t in textos:
        if "DEFINITIVO" in t:
            provisional = False
        if periodo is None and "ACUMULADO" not in t:
            for m in _RE_PERIODO.finditer(t):
                if m.group(1).lower() in MESES:
                    periodo = f"{int(m.group(2)):04d}-{MESES[m.group(1).lower()]:02d}"
                    break
    for fila in filas:
        for i, c in enumerate(fila):
            if isinstance(c, str) and _sin_acentos(c).strip() == buscado:
                valor = next((v for v in fila[i + 1 :] if v is not None), None)
                if isinstance(valor, int | float) and (mejor is None or i < mejor[0]):
                    mejor = (i, float(valor))
                break
    if periodo is None or mejor is None:
        return None
    return PuntoMensual(periodo, mejor[1], provisional)


def serie_aena(aeropuerto: str, anios: list[int]) -> list[PuntoMensual]:
    """Pasajeros mensuales de ``aeropuerto`` desde los Excel mensuales de AENA."""
    salida: dict[str, PuntoMensual] = {}
    with _cliente() as http:
        for anio in anios:
            try:
                r = http.get(AENA_INFORMES.format(anio=anio))
                r.raise_for_status()
            except httpx.HTTPError as exc:
                raise ContextoConnectorError(f"AENA {anio}: {exc}") from exc
            for url in enlaces_aena(r.text):
                with http.stream("GET", url) as resp:
                    disp = resp.headers.get("content-disposition", "").lower()
                    if resp.status_code != 200 or ".xls" not in disp:
                        continue  # el PDF gemelo de cada mes
                    contenido = resp.read()
                try:
                    punto = leer_excel_aena(contenido, aeropuerto)
                except Exception:  # noqa: BLE001 — un Excel ilegible no invalida el resto
                    punto = None
                if punto and punto.periodo.startswith(str(anio)):
                    salida[punto.periodo] = punto
    if not salida:
        raise ContextoConnectorError(f"AENA sin datos de {aeropuerto} para {anios}")
    return [salida[p] for p in sorted(salida)]


def trimestres(puntos: list[PuntoMensual]) -> list[tuple[str, float, bool]]:
    """Agrega meses en trimestres ``AAAA-Qn`` (solo trimestres completos)."""
    grupos: dict[str, list[PuntoMensual]] = {}
    for p in puntos:
        anio, mes = int(p.periodo[:4]), int(p.periodo[5:7])
        grupos.setdefault(f"{anio}-Q{(mes - 1) // 3 + 1}", []).append(p)
    return [
        (q, round(sum(p.valor for p in g), 2), any(p.provisional for p in g))
        for q, g in sorted(grupos.items())
        if len(g) == 3
    ]


# ================================================================== IECA ====
IECA_BASE = (
    "https://www.juntadeandalucia.es/institutodeestadisticaycartografia/intranet/admin/rest/v1.0"
)
IECA_EOH_PROVINCIAS = 8035  # Viajeros, pernoctaciones y estancia media por provincias (EOH)
IECA_JERARQUIA_MES = 5  # jerarquía temporal mensual (año → mes)
IECA_ALMERIA = 2352  # miembro "Almería" (código 04) de D_TERRITORIO_0
_POSORD = "f[D_TEMPORAL_0],f[D_TERRITORIO_0],f[D_RESITUR_0],c[D_CAT_HOTELES_0],c[Measures]"


def _get_ieca(http: httpx.Client, url: str, params: dict[str, Any] | None = None) -> Any:
    """GET con reintentos: el servidor de la Junta corta conexiones a menudo."""
    ultimo: Exception | None = None
    for _ in range(4):
        try:
            r = http.get(url, params=params)
            r.raise_for_status()
            return r.json()
        except (httpx.TransportError, httpx.HTTPStatusError, ValueError) as exc:
            ultimo = exc
    raise ContextoConnectorError(f"IECA no disponible: {ultimo}")


def meses_ieca(arbol: dict[str, Any], desde: str, hasta: str) -> dict[str, int]:
    """``{AAAAMM: id}`` de los meses del árbol temporal entre ``desde`` y ``hasta``."""
    salida: dict[str, int] = {}
    pila = [arbol]
    while pila:
        nodo = pila.pop()
        cod = str(nodo.get("cod") or "")
        if re.fullmatch(r"\d{6}", cod) and desde <= cod <= hasta:
            salida[cod] = int(nodo["id"])
        pila.extend(nodo.get("children") or [])
    return salida


def puntos_ieca(filas: list[list[dict[str, Any]]], medida: int = 0) -> list[PuntoMensual]:
    """Total (todas las residencias y categorías) de una medida por mes.

    Cada fila: ``[mes, territorio, residencia, categoría, viajeros, pernoctaciones, estancia]``.
    """
    salida: dict[str, PuntoMensual] = {}
    for fila in filas:
        if len(fila) < 5 + medida:
            continue
        cod_mes = str((fila[0].get("cod") or [""])[-1])
        if fila[2].get("cod") != ["00"] or fila[3].get("cod") != ["00"]:
            continue
        if not re.fullmatch(r"\d{6}", cod_mes):
            continue
        valor = _num_ieca(fila[4 + medida].get("val"))
        if valor is None:
            continue
        periodo = f"{cod_mes[:4]}-{cod_mes[4:]}"
        salida[periodo] = PuntoMensual(periodo, round(valor), False)
    return [salida[p] for p in sorted(salida)]


def _num_ieca(valor: Any) -> float | None:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def serie_ieca_viajeros(
    desde: str, hasta: str, territorio: int = IECA_ALMERIA
) -> list[PuntoMensual]:
    """Viajeros alojados en hoteles por mes (IECA, explotación de la EOH)."""
    with _cliente() as http:
        arbol = _get_ieca(
            http,
            f"{IECA_BASE}/jerarquia/{IECA_JERARQUIA_MES}",
            {"consultaId": IECA_EOH_PROVINCIAS, "alias": "D_TEMPORAL_0"},
        )
        meses = meses_ieca(arbol.get("data") or {}, desde, hasta)
        if not meses:
            raise ContextoConnectorError("IECA: sin meses en el rango pedido")
        datos = _get_ieca(
            http,
            f"{IECA_BASE}/consulta/{IECA_EOH_PROVINCIAS}",
            {
                "D_TERRITORIO_0": territorio,
                "D_TEMPORAL_0": ",".join(str(i) for i in meses.values()),
                "posord": _POSORD,
            },
        )
    puntos = puntos_ieca(datos.get("data") or [])
    if not puntos:
        raise ContextoConnectorError(f"IECA sin datos: {datos.get('messages')}")
    return puntos
