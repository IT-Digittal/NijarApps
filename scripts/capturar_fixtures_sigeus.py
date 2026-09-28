#!/usr/bin/env python3
"""Captura respuestas reales de siGEUS (Distromel) para fijar tests.

Inicia sesión con el usuario técnico configurado (``SIGEUS_USUARIO`` /
``SIGEUS_PASSWORD``, más ``SIGEUS_CUSTOMER_CODE`` / ``SIGEUS_SITE_CODE``) y
llama a los endpoints de resumen (``api/Das/Summary/*``) e inventario
(``api/cnt``, ``api/bns``, ``Api/Cmn``, ``api/rsu``) del panel, todos de solo
lectura. Para cada llamada:

- guarda la respuesta en ``tests/fixtures/sigeus/<nombre>.json`` **recortando
  las listas a como mucho 5 elementos** y sustituyendo posibles datos
  personales (nombres, matrículas, teléfonos, emails) por valores ficticios;
- anota en ``tests/fixtures/sigeus/README.md`` una fila con el código HTTP o el
  error, si la respuesta es lista u objeto, el número total de elementos antes
  del recorte y las claves de primer nivel.

No se captura ``api/session/user/current`` (perfil del usuario técnico).

Uso:
    python -m scripts.capturar_fixtures_sigeus
    python scripts/capturar_fixtures_sigeus.py
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from nijar_dti.connectors.sigeus import SigeusError, SigeusRequiere2FAError
from nijar_dti.services import sigeus_service as svc

DIRECTORIO = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sigeus"
MAX_ELEMENTOS = 5

# --------------------------------------------------------------------------
# Ventana temporal que usa el panel: día completo en UTC (ayer 00:00 → hoy
# 23:59:59), en ISO 8601.
# --------------------------------------------------------------------------


def _ventana() -> tuple[str, str]:
    ahora = datetime.now(UTC)
    ayer = (ahora - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    hoy = ahora.replace(hour=23, minute=59, second=59, microsecond=0)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return ayer.strftime(fmt), hoy.strftime(fmt)


# --------------------------------------------------------------------------
# Endpoints a capturar. Cada entrada: (nombre_fichero, ruta, params).
# ``params`` puede referirse a "dateFrom"/"dateTo" que se rellenan con la
# ventana; las rutas de inventario no llevan fecha.
# --------------------------------------------------------------------------


def _endpoints(date_from: str, date_to: str) -> list[tuple[str, str, dict[str, Any]]]:
    df, dt = {"dateFrom": date_from, "dateTo": date_to}, {}
    # Filtro de inventario de contenedores: active=true y el resto vacío
    # (ver la URL completa en docs/integraciones/runbook-sigeus-distromel.md §4).
    filtro_contenedores = {
        "containerTypeId": "",
        "garbageId": "",
        "active": "true",
        "code": "",
        "tag": "",
        "containerData1Id": "",
        "containerData2Id": "",
        "containerData3Id": "",
        "areaId": "",
        "provinceId": "",
        "municipalityId": "",
        "addressId": "",
        "volumetricFilter": "",
        "startDate": "",
        "endDate": "",
        "isDoor2Door": "",
        "isVolumetric": "",
        "isLock": "",
        "containerProperty": "",
        "containerPropertyValue": "",
    }
    filtro_puntos = {
        "code": "",
        "reference": "",
        "active": "true",
        "areaId": "",
        "provinceId": "",
        "municipalityId": "",
        "addressId": "",
        "typeId": "",
        "startDate": "",
        "endDate": "",
        "isDoor2Door": "",
        "property": "",
        "propertyValue": "",
    }
    filtro_papeleras = {
        "reference": "",
        "binTypeId": "",
        "tag": "",
        "active": "true",
        "areaId": "",
        "provinceId": "",
        "municipalityId": "",
        "addressId": "",
        "fromDate": "",
        "toDate": "",
        "startDate": "",
        "endDate": "",
        "binProperty": "",
        "binPropertyValue": "",
    }
    return [
        # --- Resumen del estado del servicio (api/Das/Summary/*) ---
        ("summary_containers", "api/Das/Summary/ContainersAsync", df),
        ("summary_collection_points", "api/Das/Summary/CollectionPointsAsync", df),
        ("summary_collections", "api/Das/Summary/CollectionsAsync", df),
        ("summary_events", "api/Das/Summary/EventsAsync", df),
        ("summary_unloads", "api/Das/Summary/UnloadsAsync", df),
        ("summary_bins", "api/Das/Summary/BinsAsync", {"dateTo": date_to}),
        ("summary_incidences", "api/Das/Summary/IncidencesAsync", df),
        ("summary_rsu_work_orders", "api/Das/Summary/RsuWorkOrdersAsync", df),
        ("summary_lv_work_orders", "api/Das/Summary/LvWorkOrdersAsync", df),
        ("summary_resources", "api/Das/Summary/ResourcesAsync", df),
        ("summary_gps", "api/Das/Summary/GpsAsync", df),
        ("summary_alarms", "api/Das/Summary/AlarmsAsync", df),
        (
            "summary_family_resources_by_module",
            "api/Das/Summary/FamilyResourcesByModuleAsync",
            {"module": "Rsu"},
        ),
        # --- Inventario (api/cnt, api/bns, Api/Cmn, api/rsu) ---
        ("cnt_containers", "api/cnt/containers/GetListFilteredAsync", filtro_contenedores),
        ("cnt_col_points", "api/cnt/colPoints/GetListFilteredAsync", filtro_puntos),
        ("bns_bins", "api/bns/bins/GetFilteredAsync", filtro_papeleras),
        ("cnt_container_types", "api/cnt/containers/types/getListAsync", dt),
        ("cmn_garbages", "Api/Cmn/Garbages/GetListAsync", dt),
        ("cmn_areas_thin", "Api/Cmn/areas/GetListThinAsync", dt),
        ("cmn_landfills_thin", "Api/Cmn/Landfills/GetListThinAsync", dt),
        ("rsu_work_orders_today", "api/rsu/workOrders/today/GetListAsync", dt),
    ]


# --------------------------------------------------------------------------
# Anonimización básica: sustituye posibles datos personales por ficticios.
# --------------------------------------------------------------------------

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_TELEFONO = re.compile(r"(?<!\d)(?:\+?\d[\s\-]?){9,15}(?!\d)")
# Matrícula española: 4 dígitos + 3 letras (formato actual) o provincia antigua.
_MATRICULA = re.compile(r"\b\d{4}[\s\-]?[BCDFGHJKLMNPRSTVWXYZ]{3}\b", re.IGNORECASE)

_CLAVES_NOMBRE = ("name", "nombre", "driver", "conductor", "operator", "operario", "worker")
_CLAVES_MATRICULA = ("plate", "matricula", "matrícula", "licenseplate", "registration")
_CLAVES_TELEFONO = ("phone", "telefono", "teléfono", "mobile", "movil", "móvil")
_CLAVES_EMAIL = ("email", "mail", "correo")


def _es_clave(clave: str, marcadores: tuple[str, ...]) -> bool:
    c = clave.lower()
    return any(m in c for m in marcadores)


def _anonimizar(valor: Any, clave: str = "") -> Any:
    """Recorre la estructura y reemplaza datos personales por ficticios."""
    if isinstance(valor, dict):
        return {k: _anonimizar(v, k) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_anonimizar(v, clave) for v in valor]
    if isinstance(valor, str):
        if _es_clave(clave, _CLAVES_EMAIL) or _EMAIL.fullmatch(valor.strip()):
            return "ejemplo@ejemplo.test"
        if _es_clave(clave, _CLAVES_MATRICULA) or _MATRICULA.fullmatch(valor.strip()):
            return "0000XXX"
        if _es_clave(clave, _CLAVES_TELEFONO):
            return "600000000"
        if _es_clave(clave, _CLAVES_NOMBRE):
            return "Nombre Apellido"
        # Sustituciones dentro de texto libre.
        texto = _EMAIL.sub("ejemplo@ejemplo.test", valor)
        texto = _MATRICULA.sub("0000XXX", texto)
        return texto
    return valor


def _recortar(valor: Any) -> Any:
    """Recorta listas a MAX_ELEMENTOS (recursivamente en objetos)."""
    if isinstance(valor, list):
        return [_recortar(v) for v in valor[:MAX_ELEMENTOS]]
    if isinstance(valor, dict):
        return {k: _recortar(v) for k, v in valor.items()}
    return valor


def _claves_nivel1(datos: Any) -> list[str]:
    if isinstance(datos, dict):
        return sorted(datos.keys())
    if isinstance(datos, list) and datos and isinstance(datos[0], dict):
        return sorted(datos[0].keys())
    return []


def _tipo(datos: Any) -> str:
    if isinstance(datos, list):
        return "lista"
    if isinstance(datos, dict):
        return "objeto"
    return type(datos).__name__


def _total(datos: Any) -> int | str:
    return len(datos) if isinstance(datos, list) else "-"


async def _run() -> int:
    print("\n== Captura de fixtures de siGEUS (Distromel · RSU y limpieza viaria) ==\n")
    DIRECTORIO.mkdir(parents=True, exist_ok=True)

    if not svc.sigeus_configurado():
        _escribir_readme_bloqueado(
            "Sin configurar: faltan SIGEUS_USUARIO / SIGEUS_PASSWORD en el entorno."
        )
        print("siGEUS sin configurar; no se captura nada.")
        return 1

    cliente = svc._obtener_cliente()

    # Comprobar acceso antes de recorrer los endpoints.
    try:
        await cliente.comprobar_sesion()
    except SigeusRequiere2FAError as e:
        _escribir_readme_bloqueado(f"Login bloqueado por segundo factor (OTP): {e}")
        print(f"BLOQUEADO: {e}")
        print("Pedir a Distromel un usuario técnico sin 2FA para poder capturar.")
        return 2
    except SigeusError as e:
        _escribir_readme_bloqueado(f"No se puede iniciar sesión: {e}")
        print(f"BLOQUEADO: {e}")
        return 2

    date_from, date_to = _ventana()
    print(f"Ventana: dateFrom={date_from} · dateTo={date_to}\n")

    filas: list[dict[str, Any]] = []
    for nombre, ruta, params in _endpoints(date_from, date_to):
        estado, datos = await _capturar(cliente, ruta, params)
        # module=Rsu puede fallar; el runbook sugiere probar module=1.
        if datos is None and "FamilyResourcesByModuleAsync" in ruta:
            estado_alt, datos_alt = await _capturar(cliente, ruta, {"module": "1"})
            if datos_alt is not None:
                estado, datos, params = (
                    f"{estado} (module=Rsu) → OK con module=1",
                    datos_alt,
                    {"module": "1"},
                )

        fila = {
            "endpoint": f"{ruta}" + (f"?{_qs(params)}" if params else ""),
            "fichero": f"{nombre}.json",
            "estado": estado,
            "tipo": _tipo(datos) if datos is not None else "-",
            "total": _total(datos) if datos is not None else "-",
            "claves": ", ".join(_claves_nivel1(datos)) if datos is not None else "-",
        }
        filas.append(fila)
        print(f"  {estado:>12}  {ruta}")

        if datos is not None:
            limpio = _recortar(_anonimizar(datos))
            (DIRECTORIO / f"{nombre}.json").write_text(
                json.dumps(limpio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

    _escribir_readme(date_from, date_to, filas)
    print(f"\nFixtures y README en {DIRECTORIO}")
    return 0


def _qs(params: dict[str, Any]) -> str:
    return "&".join(f"{k}={v}" for k, v in params.items())


async def _capturar(cliente: Any, ruta: str, params: dict[str, Any]) -> tuple[str, Any]:
    """Llama al endpoint; devuelve (estado, datos) o (error, None)."""
    try:
        datos = await cliente.get(ruta, params=params or None)
        return "200", datos
    except SigeusError as e:
        return f"ERROR: {e}", None


def _escribir_readme(date_from: str, date_to: str, filas: list[dict[str, Any]]) -> None:
    lineas = [
        "# Fixtures de siGEUS (Distromel · RSU y limpieza viaria)",
        "",
        "Respuestas reales capturadas con `scripts/capturar_fixtures_sigeus.py`.",
        "Las listas se recortan a 5 elementos y se anonimizan posibles datos",
        "personales (nombres, matrículas, teléfonos, emails).",
        "",
        f"- Ventana: `dateFrom={date_from}` · `dateTo={date_to}`",
        "",
        "| Endpoint | Fichero | HTTP/error | Tipo | Total | Claves de primer nivel |",
        "|---|---|---|---|---|---|",
    ]
    for f in filas:
        estado = f["estado"].replace("|", "\\|")
        claves = f["claves"].replace("|", "\\|")
        lineas.append(
            f"| `{f['endpoint']}` | `{f['fichero']}` | {estado} | {f['tipo']} | "
            f"{f['total']} | {claves} |"
        )
    lineas.append("")
    (DIRECTORIO / "README.md").write_text("\n".join(lineas), encoding="utf-8")


def _escribir_readme_bloqueado(motivo: str) -> None:
    DIRECTORIO.mkdir(parents=True, exist_ok=True)
    contenido = (
        "# Fixtures de siGEUS (Distromel · RSU y limpieza viaria)\n"
        "\n"
        "Todavía **no se han podido capturar** respuestas reales.\n"
        "\n"
        f"- Motivo: {motivo}\n"
        "\n"
        "El usuario técnico facilitado por Distromel tiene el segundo factor\n"
        "(OTP) activado, y `POST api/session/login` responde HTTP 200 con\n"
        '`{"token": null, "twoFactorAuthentication": true}`, sin emitir token.\n'
        "El login automatizado no es posible en ese caso.\n"
        "\n"
        "Siguiente paso: solicitar a Distromel un usuario técnico **sin 2FA**\n"
        "(solo lectura) y volver a ejecutar `python -m scripts.capturar_fixtures_sigeus`.\n"
    )
    (DIRECTORIO / "README.md").write_text(contenido, encoding="utf-8")


def main() -> int:
    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
