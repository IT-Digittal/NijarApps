"""Cliente REST de Datadis (plataforma oficial de las distribuidoras eléctricas).

Dos interfaces, ambas de solo lectura:

**Datos públicos agregados** (``/api-public/api-search``): energía consumida y
número de contratos por día, municipio, sector económico y tensión, lo mismo
que muestra https://datadis.es/queries. Se intenta sin credenciales; si
Datadis exige identificarse (401/403) y hay usuario configurado, se repite con
token.

**API privada** (``/api-private/api/*-v2``): los suministros (CUPS) del
Ayuntamiento o de un NIF que le haya autorizado, su contrato y su curva de
consumo horaria. Requiere usuario (NIF) y contraseña de Datadis.

Notas de la API (contempladas aquí):
- Login: ``POST /nikola-auth/tokens/login`` con formulario ``username`` y
  ``password``; la respuesta es el token JWT en texto plano (válido ~24 h).
- Consumo: fechas ``AAAA/MM``; ``measurementType`` 0 = horario.
- Datadis rechaza repetir la misma consulta privada durante 24 h: la carga
  se hace una vez al día.
- El formato exacto de la respuesta pública no está documentado con detalle:
  el parseo acepta varios nombres de campo y el verificador
  (``scripts/verificar_datadis.py``) muestra la respuesta real.
"""

from __future__ import annotations

import asyncio
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import httpx

BASE_URL = "https://datadis.es"
URL_LOGIN = "/nikola-auth/tokens/login"
URL_PUBLICA = "/api-public/api-search"
URL_PRIVADA = "/api-private/api"

_REINTENTABLES = {429, 502, 503, 504}
_esperar = asyncio.sleep  # inyectable en los tests


class DatadisError(Exception):
    """Error de comunicación o de datos con Datadis."""


class DatadisAutenticacionError(DatadisError):
    """Credenciales ausentes o rechazadas."""


def normalizar(texto: str | None) -> str:
    """Mayúsculas sin tildes ni espacios sobrantes (para comparar municipios)."""
    t = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return " ".join(t.upper().split())


def _num(valor: Any) -> float | None:
    """Número de la API: admite 1234.5, "1234.5", "1.234,5" y "14.597" (miles)."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    s = str(valor).strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):  # «14.597»: punto de miles
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def _primero(d: dict[str, Any], *claves: str) -> Any:
    for c in claves:
        if c in d and d[c] not in (None, ""):
            return d[c]
    # sin distinguir mayúsculas
    bajas = {k.lower(): v for k, v in d.items()}
    for c in claves:
        v = bajas.get(c.lower())
        if v not in (None, ""):
            return v
    return None


def _fecha(valor: Any) -> date | None:
    if not valor:
        return None
    s = str(valor).strip()[:10]
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# ------------------------------------------------------------ públicos ----


@dataclass(frozen=True)
class RegistroPublico:
    """Una fila de «Consumos y contratos» (agregado diario)."""

    fecha: date
    comunidad: str | None
    provincia: str | None
    municipio: str | None
    sector: str
    tension: str
    contratos: int
    energia_kwh: float


def filas_de_respuesta(datos: Any) -> list[dict[str, Any]]:
    """Extrae la lista de filas de la respuesta, venga como lista o envuelta."""
    if isinstance(datos, list):
        return [x for x in datos if isinstance(x, dict)]
    if isinstance(datos, dict):
        for clave in ("data", "content", "result", "results", "items", "list", "rows"):
            v = datos.get(clave)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
            if isinstance(v, dict):
                return filas_de_respuesta(v)
    return []


def parsear_registro_publico(fila: dict[str, Any]) -> RegistroPublico | None:
    f = _fecha(_primero(fila, "date", "fecha", "day", "dia", "measureDate"))
    energia = _num(
        _primero(fila, "sumEnergy", "energy", "energia", "sumConsumption", "consumption",
                 "consumptionKWh", "energySum", "totalEnergy")
    )  # fmt: skip
    contratos = _num(
        _primero(fila, "sumContracts", "contracts", "contratos", "numContracts",
                 "contractsSum", "totalContracts")
    )  # fmt: skip
    if f is None or (energia is None and contratos is None):
        return None
    return RegistroPublico(
        fecha=f,
        comunidad=_primero(fila, "community", "comunidad", "communityName"),
        provincia=_primero(fila, "province", "provincia", "provinceName"),
        municipio=_primero(fila, "municipality", "municipio", "municipalityName"),
        sector=str(
            _primero(fila, "economicSector", "sector", "economicSectorName") or "NO ESPECIFICADO"
        ).strip()[:60],
        tension=str(_primero(fila, "tension", "tensionName", "fare", "tarifa") or "—").strip()[:60],
        contratos=int(contratos or 0),
        energia_kwh=float(energia or 0),
    )


# ------------------------------------------------------------ privados ----


@dataclass(frozen=True)
class Suministro:
    cups: str
    direccion: str
    codigo_postal: str | None
    municipio: str | None
    distribuidora: str | None
    codigo_distribuidora: str
    tipo_punto: int | None
    valido_desde: str | None
    valido_hasta: str | None
    provincia: str | None = None


@dataclass(frozen=True)
class LecturaHoraria:
    cups: str
    fecha: date
    hora: int  # 1..24 (hora de FIN del periodo, como la publica Datadis)
    consumo_kwh: float
    excedente_kwh: float | None
    autoconsumo_kwh: float | None
    metodo: str | None  # «Real» / «Estimada»


def parsear_suministros(datos: Any) -> list[Suministro]:
    """Suministros de la respuesta, sin repetir CUPS.

    Si la autorización de tercero está duplicada en Datadis (p. ej. 318 «CUPS
    autorizados» para 159 suministros), cada CUPS llega dos veces: se toma una
    sola para no descargar su curva dos veces.
    """
    filas = datos.get("supplies") if isinstance(datos, dict) else datos
    out = []
    vistos: set[str] = set()
    for s in filas or []:
        if not isinstance(s, dict) or not s.get("cups"):
            continue
        cups = str(s["cups"]).strip().upper()
        if cups in vistos:
            continue
        vistos.add(cups)
        tipo = s.get("pointType")
        out.append(
            Suministro(
                cups=cups,
                direccion=str(s.get("address") or s["cups"]).strip(),
                codigo_postal=s.get("postalCode"),
                municipio=s.get("municipality"),
                distribuidora=s.get("distributor"),
                codigo_distribuidora=str(s.get("distributorCode") or ""),
                tipo_punto=int(str(tipo)) if str(tipo or "").isdigit() else None,
                valido_desde=s.get("validDateFrom"),
                valido_hasta=s.get("validDateTo"),
                provincia=s.get("province"),
            )
        )
    return out


def parsear_curva(datos: Any) -> list[LecturaHoraria]:
    filas = datos.get("timeCurve") if isinstance(datos, dict) else datos
    out = []
    for r in filas or []:
        if not isinstance(r, dict):
            continue
        f = _fecha(r.get("date"))
        hora_txt = str(r.get("time") or "").split(":")[0]
        consumo = _num(r.get("consumptionKWh"))
        if f is None or not hora_txt.isdigit() or consumo is None:
            continue
        out.append(
            LecturaHoraria(
                cups=str(r.get("cups") or "").strip().upper(),
                fecha=f,
                hora=int(hora_txt),
                consumo_kwh=consumo,
                excedente_kwh=_num(r.get("surplusEnergyKWh")),
                autoconsumo_kwh=_num(r.get("selfConsumptionEnergyKWh")),
                metodo=r.get("obtainMethod"),
            )
        )
    return out


def detalle_contrato(datos: Any) -> dict[str, Any]:
    """Datos del contrato vigente (detalle V2): peaje, tensión y potencias P1…P6.

    Es lo que piden los pliegos de suministro eléctrico (Anexo I). Si hay varios
    contratos se toma el último por fecha de inicio.
    """
    contratos = datos.get("contract") if isinstance(datos, dict) else datos
    validos = [c for c in contratos or [] if isinstance(c, dict)]
    if not validos:
        return {}
    c = max(validos, key=lambda x: str(x.get("startDate") or ""))
    potencias = [
        round(float(p), 3) if isinstance(p, int | float) else None
        for p in (c.get("contractedPowerkW") or [])
    ]
    return {
        "tarifa_acceso": (str(c.get("accessFare") or "").strip() or None),
        "codigo_tarifa": (str(c.get("codeFare") or "").strip() or None),
        "tension": (str(c.get("tension") or "").strip() or None),
        "potencias_kw": potencias[:6],
        "distribuidora": c.get("distributor"),
        "comercializadora": c.get("marketer"),
        "provincia": c.get("province"),
        "municipio": c.get("municipality"),
        "codigo_postal": c.get("postalCode"),
        "discriminacion_horaria": c.get("timeDiscrimination"),
        "fecha_inicio": c.get("startDate"),
        "fecha_fin": c.get("endDate"),
        "autoconsumo": c.get("selfConsumptionTypeDesc"),
    }


def potencia_contratada(datos: Any) -> float | None:
    """Mayor potencia contratada (kW) del detalle de contrato V2."""
    contratos = datos.get("contract") if isinstance(datos, dict) else datos
    potencias = [
        p
        for c in contratos or []
        if isinstance(c, dict)
        for p in (c.get("contractedPowerkW") or [])
        if isinstance(p, (int, float))
    ]
    return max(potencias) if potencias else None


# --------------------------------------------------------------- cliente ----


def _consulta_repetida(r: httpx.Response) -> bool:
    """429 por el límite diario de Datadis («Consulta ya realizada en las últimas 24 horas»).

    Reintentar no sirve: la misma consulta no se admite hasta el día siguiente.
    """
    return r.status_code == 429 and "ya realizada" in r.text.lower()


class ClienteDatadis:
    """Cliente asíncrono con token perezoso y reintentos ante 429/5xx."""

    def __init__(
        self,
        usuario: str = "",
        password: str = "",
        nif_autorizado: str = "",
        base_url: str = BASE_URL,
        timeout_seconds: int = 90,
        cliente_http: httpx.AsyncClient | None = None,
    ) -> None:
        self._usuario = usuario
        self._password = password
        self._nif_autorizado = nif_autorizado or None
        self._base = base_url.rstrip("/")
        self._cli = cliente_http or httpx.AsyncClient(timeout=timeout_seconds)
        self._propio = cliente_http is None
        self._token: str | None = None

    @property
    def tiene_credenciales(self) -> bool:
        return bool(self._usuario and self._password)

    async def cerrar(self) -> None:
        if self._propio:
            await self._cli.aclose()

    async def __aenter__(self) -> ClienteDatadis:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.cerrar()

    async def _pedir(self, metodo: str, ruta: str, **kw: Any) -> httpx.Response:
        for n in range(4):
            try:
                r = await self._cli.request(metodo, self._base + ruta, **kw)
            except httpx.HTTPError as exc:
                if n == 3:
                    raise DatadisError(f"Sin conexión con Datadis: {exc}") from exc
                await _esperar(2.0 * 2**n)
                continue
            if r.status_code not in _REINTENTABLES or n == 3 or _consulta_repetida(r):
                return r
            try:
                espera = min(float(r.headers.get("retry-after", "")), 60.0)
            except ValueError:
                espera = 2.0 * 2**n
            await _esperar(espera)
        raise AssertionError("inalcanzable")

    async def login(self) -> str:
        if not self.tiene_credenciales:
            raise DatadisAutenticacionError("DATADIS_USUARIO / DATADIS_PASSWORD sin configurar")
        r = await self._pedir(
            "POST", URL_LOGIN, data={"username": self._usuario, "password": self._password}
        )
        token = r.text.strip().strip('"')
        if r.status_code != 200 or not token or token.startswith("{"):
            raise DatadisAutenticacionError(f"Login rechazado por Datadis ({r.status_code})")
        self._token = token
        return token

    def _cabeceras(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"} if self._token else {}

    async def _get_json(self, ruta: str, params: dict[str, Any], requiere_token: bool) -> Any:
        if requiere_token and not self._token:
            await self.login()
        r = await self._pedir("GET", ruta, params=params, headers=self._cabeceras())
        if r.status_code in (401, 403):
            if self.tiene_credenciales:
                await self.login()  # token caducado o la API pública lo exige
                r = await self._pedir("GET", ruta, params=params, headers=self._cabeceras())
            if r.status_code in (401, 403):
                raise DatadisAutenticacionError(
                    f"Datadis exige autenticación para {ruta} ({r.status_code})"
                )
        if r.status_code != 200:
            raise DatadisError(f"Datadis respondió {r.status_code} en {ruta}: {r.text[:200]}")
        try:
            return r.json()
        except ValueError as exc:
            raise DatadisError(f"Respuesta no JSON en {ruta}: {r.text[:200]}") from exc

    # ---------- públicos ----------
    async def buscar_publico(
        self,
        desde: date,
        hasta: date,
        filtros: dict[str, str],
        page_size: int = 2000,
        max_paginas: int = 50,
    ) -> tuple[list[dict[str, Any]], Any]:
        """Filas crudas de ``api-search`` paginando. Devuelve (filas, primera respuesta)."""
        filas: list[dict[str, Any]] = []
        primera: Any = None
        for page in range(max_paginas):
            params = {
                "startDate": desde.strftime("%Y/%m/%d"),
                "endDate": hasta.strftime("%Y/%m/%d"),
                "page": page,
                "pageSize": page_size,
                **{k: v for k, v in filtros.items() if v},
            }
            datos = await self._get_json(URL_PUBLICA, params, requiere_token=False)
            if primera is None:
                primera = datos
            lote = filas_de_respuesta(datos)
            filas.extend(lote)
            if len(lote) < page_size:
                break
        return filas, primera

    # ---------- privados ----------
    def _con_nif(self, params: dict[str, Any]) -> dict[str, Any]:
        if self._nif_autorizado:
            params["authorizedNif"] = self._nif_autorizado
        return params

    async def suministros(self) -> list[Suministro]:
        datos = await self._get_json(
            URL_PRIVADA + "/get-supplies-v2", self._con_nif({}), requiere_token=True
        )
        return parsear_suministros(datos)

    async def contrato(self, s: Suministro) -> Any:
        """Respuesta cruda del detalle de contrato V2 de un suministro."""
        return await self._get_json(
            URL_PRIVADA + "/get-contract-detail-v2",
            self._con_nif({"cups": s.cups, "distributorCode": s.codigo_distribuidora}),
            requiere_token=True,
        )

    async def potencia_contratada(self, s: Suministro) -> float | None:
        return potencia_contratada(await self.contrato(s))

    async def curva_horaria(
        self, s: Suministro, mes_desde: str, mes_hasta: str
    ) -> list[LecturaHoraria]:
        """Consumo horario entre dos meses (``AAAA/MM``, ambos incluidos)."""
        params: dict[str, Any] = {
            "cups": s.cups,
            "distributorCode": s.codigo_distribuidora,
            "startDate": mes_desde,
            "endDate": mes_hasta,
            "measurementType": "0",
        }
        if s.tipo_punto is not None:
            params["pointType"] = str(s.tipo_punto)
        datos = await self._get_json(
            URL_PRIVADA + "/get-consumption-data-v2", self._con_nif(params), requiere_token=True
        )
        return parsear_curva(datos)
