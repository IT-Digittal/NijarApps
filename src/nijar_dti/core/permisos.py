"""Matriz de permisos por rol (curada en código).

Fuente única de verdad sobre qué módulos/acciones ve cada rol RBAC. Se
mantiene aquí, en un único lugar, para no dispersar la lógica de visibilidad
por el frontend ni por los routers. La autorización real de cada endpoint
sigue haciéndose con `require_roles(...)`; este módulo permite además:

- construir tuplas de roles a partir de un permiso (`roles_con`), de modo que
  las guardas de los routers puedan derivarse de la matriz en vez de listar
  strings a mano;
- exponer la matriz al panel de administración (endpoint
  `GET /api/v1/usuarios/matriz-permisos`) para mostrarla de forma visual.

Decisión de diseño: NO se persisten permisos en base de datos ni se sustituye
el sistema de roles existente. La matriz es estática y editable solo en código.
"""

from __future__ import annotations

from nijar_dti.models.usuario import RolUsuario

# ---------------------------------------------------------------------------
# Catálogo de módulos/permisos
# ---------------------------------------------------------------------------

# Cada módulo tiene un id estable (permiso), un nombre legible y un grupo para
# agruparlos visualmente en la matriz.
MODULOS: list[dict[str, str]] = [
    {"id": "ver_resumen_municipal", "nombre": "Resumen municipal", "grupo": "Dirección"},
    {"id": "ver_recomendaciones_ia", "nombre": "Recomendaciones IA", "grupo": "Dirección"},
    {"id": "ver_dti", "nombre": "DTI / Turismo", "grupo": "Verticales"},
    {"id": "ver_alumbrado", "nombre": "Alumbrado público", "grupo": "Verticales"},
    {"id": "ver_agua", "nombre": "Ciclo del agua", "grupo": "Verticales"},
    {"id": "ver_residuos", "nombre": "Residuos", "grupo": "Verticales"},
    {"id": "ver_movilidad", "nombre": "Movilidad", "grupo": "Verticales"},
    {"id": "ver_seguridad", "nombre": "Seguridad", "grupo": "Verticales"},
    {"id": "ver_energia", "nombre": "Energía municipal", "grupo": "Verticales"},
    {"id": "ver_detalle_tecnico", "nombre": "Detalle técnico", "grupo": "Operación"},
    {"id": "gestionar_incidencias", "nombre": "Gestionar incidencias", "grupo": "Operación"},
    {"id": "generar_informes", "nombre": "Generar informes", "grupo": "Gestión"},
    {"id": "exportar_datos", "nombre": "Exportar datos", "grupo": "Gestión"},
    {"id": "administrar_usuarios", "nombre": "Administrar usuarios", "grupo": "Administración"},
    {"id": "administrar_roles", "nombre": "Administrar roles", "grupo": "Administración"},
    {
        "id": "configurar_integraciones",
        "nombre": "Configurar integraciones",
        "grupo": "Administración",
    },
]

_TODOS: set[str] = {m["id"] for m in MODULOS}

_VERTICALES: set[str] = {
    "ver_dti",
    "ver_alumbrado",
    "ver_agua",
    "ver_residuos",
    "ver_movilidad",
    "ver_seguridad",
    "ver_energia",
}

# ---------------------------------------------------------------------------
# Nombres legibles de cada rol (para la UI)
# ---------------------------------------------------------------------------

DISPLAY_ROLES: dict[str, str] = {
    RolUsuario.ADMINISTRADOR_TIC.value: "Superadministrador",
    RolUsuario.GESTOR_CONTENIDOS.value: "Administrador municipal / Contenidos",
    RolUsuario.ANALISTA_DATOS.value: "Analista de datos",
    RolUsuario.OPERADOR_SMART_OFFICE.value: "Operaciones",
    RolUsuario.AUDITOR.value: "Consulta / Visor",
    RolUsuario.DIRECCION_GOBIERNO.value: "Dirección / Gobierno",
}

# ---------------------------------------------------------------------------
# Permisos por rol (la matriz)
# ---------------------------------------------------------------------------

PERMISOS_POR_ROL: dict[str, set[str]] = {
    # Superadministrador: control total.
    RolUsuario.ADMINISTRADOR_TIC.value: set(_TODOS),
    # Administrador municipal / Contenidos: resúmenes, turismo, informes y
    # exportación; sin detalle técnico ni administración de la plataforma.
    RolUsuario.GESTOR_CONTENIDOS.value: {
        "ver_resumen_municipal",
        "ver_recomendaciones_ia",
        *_VERTICALES,
        "generar_informes",
        "exportar_datos",
    },
    # Analista de datos: lectura completa + detalle técnico + informes; sin
    # administración de usuarios/roles/integraciones.
    RolUsuario.ANALISTA_DATOS.value: {
        "ver_resumen_municipal",
        "ver_recomendaciones_ia",
        *_VERTICALES,
        "ver_detalle_tecnico",
        "generar_informes",
        "exportar_datos",
    },
    # Operaciones: verticales, detalle técnico e incidencias; enfoque operativo.
    RolUsuario.OPERADOR_SMART_OFFICE.value: {
        *_VERTICALES,
        "ver_detalle_tecnico",
        "gestionar_incidencias",
        "generar_informes",
    },
    # Consulta / Visor: solo lectura de resúmenes e informes.
    RolUsuario.AUDITOR.value: {
        "ver_resumen_municipal",
        *_VERTICALES,
        "generar_informes",
    },
    # Dirección / Gobierno: visión ejecutiva — resúmenes, recomendaciones,
    # informes y exportación. SIN detalle técnico, incidencias ni administración.
    RolUsuario.DIRECCION_GOBIERNO.value: {
        "ver_resumen_municipal",
        "ver_recomendaciones_ia",
        *_VERTICALES,
        "generar_informes",
        "exportar_datos",
    },
}


def permisos_de(rol: str) -> set[str]:
    """Devuelve el conjunto de permisos (ids de módulo) de un rol."""
    return set(PERMISOS_POR_ROL.get(rol, set()))


def tiene_permiso(rol: str, permiso: str) -> bool:
    """Indica si un rol tiene concedido un permiso concreto."""
    return permiso in PERMISOS_POR_ROL.get(rol, set())


def roles_con(permiso: str) -> tuple[str, ...]:
    """Roles que tienen concedido el permiso indicado.

    Pensado para usarse en las guardas de los routers:
    `require_roles(*roles_con("ver_resumen_municipal"))`.
    """
    return tuple(rol for rol, permisos in PERMISOS_POR_ROL.items() if permiso in permisos)


def matriz() -> dict[str, object]:
    """Estructura serializable de la matriz para el panel de administración."""
    return {
        "modulos": MODULOS,
        "roles": [
            {
                "rol": rol,
                "display": DISPLAY_ROLES.get(rol, rol),
                "permisos": sorted(PERMISOS_POR_ROL.get(rol, set())),
            }
            for rol in DISPLAY_ROLES
        ],
    }
