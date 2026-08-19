"""Seeders de las verticales Smart City (alumbrado, agua, residuos, movilidad,
seguridad y energía).

Datos de ejemplo deterministas alineados con la maqueta de referencia:
- Alumbrado: 1.240 luminarias (967 LED · 211 VSAP · 62 solar), 18 cuadros,
  55 circuitos, 6 zonas, ~142 kW instalados.
- Agua: 14 sectores, 480 contadores (86 % telelectura), 3 fugas.
- Residuos: 684 contenedores (412 con sensor), 6 rutas.
- Movilidad: aforos de acceso, aparcamientos de playa, recarga EV y lanzadera.
- Seguridad: 24 cámaras CCTV (23 online, 1 sin comunicación).
- Energía: 61 CUPS en 34 edificios municipales.
"""

from __future__ import annotations

import random

_R = random.Random(20260703)

# --------------------------------------------------------------- ALUMBRADO
ZONAS_ALUMBRADO: list[dict] = [
    {
        "id": "nijar",
        "nombre": "Níjar casco",
        "luminarias": 348,
        "led": 320,
        "vsap": 22,
        "solar": 6,
        "latitud": 36.9656,
        "longitud": -2.2070,
        "calles": [
            "C/ Real",
            "Plaza de la Glorieta",
            "C/ Carretera",
            "C/ Parras",
            "Avda. Federico García Lorca",
            "C/ Huerta",
        ],
    },
    {
        "id": "sanjose",
        "nombre": "San José",
        "luminarias": 312,
        "led": 204,
        "vsap": 98,
        "solar": 10,
        "latitud": 36.7597,
        "longitud": -2.1064,
        "calles": [
            "Avda. de San José",
            "C/ Correo",
            "Paseo Marítimo",
            "C/ del Puerto",
            "C/ Ancla",
            "Mirador de la Calilla",
        ],
    },
    {
        "id": "campo",
        "nombre": "Campohermoso",
        "luminarias": 244,
        "led": 172,
        "vsap": 64,
        "solar": 8,
        "latitud": 36.8447,
        "longitud": -2.1503,
        "calles": [
            "Avda. de la Constitución",
            "C/ Sevilla",
            "C/ Granada",
            "Camino del Campillo",
            "C/ Almería",
            "Plaza Mayor",
        ],
    },
    {
        "id": "roda",
        "nombre": "Rodalquilar",
        "luminarias": 146,
        "led": 118,
        "vsap": 12,
        "solar": 16,
        "latitud": 36.8517,
        "longitud": -2.0416,
        "calles": [
            "C/ Los Mineros",
            "C/ del Oro",
            "Ctra. del Playazo",
            "C/ Fundición",
            "C/ Cortijo del Fraile",
        ],
    },
    {
        "id": "negras",
        "nombre": "Las Negras",
        "luminarias": 112,
        "led": 89,
        "vsap": 9,
        "solar": 14,
        "latitud": 36.8797,
        "longitud": -2.0000,
        "calles": [
            "Paseo del Mar",
            "C/ Cala San Pedro",
            "C/ La Palmera",
            "C/ Bahía",
            "C/ Cerro Negro",
        ],
    },
    {
        "id": "albar",
        "nombre": "Los Albaricoques",
        "luminarias": 78,
        "led": 64,
        "vsap": 6,
        "solar": 8,
        "latitud": 36.8720,
        "longitud": -2.0800,
        "calles": ["C/ Cine", "C/ Rodaje", "Camino de los Llanos", "C/ Era", "C/ Poniente"],
    },
]

# Distribución de los 18 cuadros por zona (según la referencia)
_CUADRO_ZONES = (
    ["nijar"] * 5 + ["sanjose"] * 4 + ["campo"] * 4 + ["roda"] * 2 + ["negras"] * 2 + ["albar"] * 1
)
_CU_NAMES = {
    "nijar": ["Casco Norte", "Casco Sur", "Glorieta", "Barrio Alto", "Polígono"],
    "sanjose": ["Puerto", "Centro urbano", "Paseo Marítimo", "Acceso playas"],
    "campo": ["Centro", "Norte", "Invernaderos", "Colegio"],
    "roda": ["Pueblo", "Valle minero"],
    "negras": ["Núcleo", "Paseo del Mar"],
    "albar": ["Núcleo"],
}
_POT_W = {"led": 45, "vsap": 100, "solar": 28}
_VIDA_H = {"led": 100000, "vsap": 24000, "solar": 60000}
_MARCA = {"led": "Salvi Basic LED", "vsap": "Carandini VSAP", "solar": "Solar autónoma IP66"}

# San José y Las Negras tienen el mar justo al este del núcleo: la dispersión
# aleatoria de activos solo puede ir hacia tierra (oeste) para no caer al agua.
# UMBRAL_LON_MAR marca la longitud a partir de la cual ya es mar en esas zonas
# (lo usa también el backfill correctivo del seed_loader).
JITTER_LON_ZONA: dict[str, tuple[float, float]] = {
    "sanjose": (-0.014, -0.001),
    "negras": (-0.014, -0.001),
}
UMBRAL_LON_MAR: dict[str, float] = {"sanjose": -2.105, "negras": -2.001}


def _jitter_lon(zid: str, amplitud: float) -> float:
    lo, hi = JITTER_LON_ZONA.get(zid, (-amplitud, amplitud))
    return _R.uniform(lo, hi)


def generar_cuadros_seed() -> list[dict]:
    zonas = {z["id"]: z for z in ZONAS_ALUMBRADO}
    idx: dict[str, int] = {}
    cuadros = []
    for i, zid in enumerate(_CUADRO_ZONES):
        z = zonas[zid]
        code = f"CM-{i + 1:03d}"
        idx[zid] = idx.get(zid, 0)
        anomalo = code == "CM-004"
        no_comms = code == "CM-013"
        if no_comms:
            estado, comms, alarmas = (
                "sin_comunicacion",
                "sin comunicación",
                ["Pérdida de comunicación GPRS"],
            )
        elif anomalo:
            estado, comms, alarmas = (
                "alerta",
                "online",
                ["Consumo anómalo nocturno", "Desequilibrio de fases"],
            )
        else:
            estado, comms, alarmas = (
                "operativo",
                "online",
                (["Puerta de cuadro abierta"] if _R.random() < 0.1 else []),
            )
        cuadros.append(
            {
                "codigo": code,
                "nombre": _CU_NAMES[zid][idx[zid] % len(_CU_NAMES[zid])],
                "zona_id": zid,
                "ubicacion": f"{_R.choice(z['calles'])}, {_R.randint(1, 40)}",
                "circuitos": _R.randint(2, 4),
                "potencia_kw": round(z["luminarias"] / len(_CU_NAMES[zid]) * 0.05, 2),
                "factor_potencia": round(_R.uniform(0.92, 0.99), 2),
                "comunicaciones": comms,
                "sla": _R.randint(88, 99),
                "estado": estado,
                "alarmas": alarmas or None,
                "latitud": round(z["latitud"] + _R.uniform(-0.01, 0.01), 6),
                "longitud": round(z["longitud"] + _jitter_lon(zid, 0.01), 6),
            }
        )
        idx[zid] += 1
    return cuadros


def generar_luminarias_seed() -> list[dict]:
    """Genera las 1.240 luminarias con el reparto exacto por zona y tecnología."""
    cuadros_por_zona: dict[str, list[str]] = {}
    for i, zid in enumerate(_CUADRO_ZONES):
        cuadros_por_zona.setdefault(zid, []).append(f"CM-{i + 1:03d}")

    luminarias = []
    n = 0
    # nº de averías / sin comunicación repartidas (1213 operativas, 17 avería, 10 sin com.)
    total = sum(z["luminarias"] for z in ZONAS_ALUMBRADO)
    idx_averia = set(_R.sample(range(total), 17))
    idx_sincom = set(_R.sample([i for i in range(total) if i not in idx_averia], 10))

    for z in ZONAS_ALUMBRADO:
        cuadros = cuadros_por_zona[z["id"]]
        tech_pool = ["led"] * z["led"] + ["vsap"] * z["vsap"] + ["solar"] * z["solar"]
        _R.shuffle(tech_pool)
        for j, tech in enumerate(tech_pool):
            code = f"L-{n + 1:04d}"
            cuadro = cuadros[j % len(cuadros)]
            circuito = f"{cuadro}-C{(j % 3) + 1}"
            pot = _POT_W[tech]
            anio = _R.randint(2016, 2024)
            horas = (2024 - anio) * 4100 + _R.randint(0, 900)
            if n in idx_averia:
                estado, ultima = "averia", _R.randint(60, 400)
            elif n in idx_sincom:
                estado, ultima = "sin_comunicacion", _R.randint(180, 4320)
            else:
                estado, ultima = "operativo", _R.randint(1, 15)
            luminarias.append(
                {
                    "codigo": code,
                    "zona_id": z["id"],
                    "cuadro_codigo": cuadro,
                    "circuito": circuito,
                    "direccion": f"{_R.choice(z['calles'])}, {_R.randint(1, 120)}",
                    "tecnologia": tech,
                    "potencia_w": pot,
                    "marca_modelo": _MARCA[tech],
                    "anio_instalacion": anio,
                    "vida_util_h": _VIDA_H[tech],
                    "estado": estado,
                    "nivel_regulacion": 100 if 6 <= 20 else 50,
                    "horas_funcionamiento": horas,
                    "consumo_mes_kwh": round(pot * 0.30 * 30 / 1000 * _R.uniform(0.9, 1.1), 2),
                    "ultima_comunicacion_min": ultima,
                    "tiene_documentacion": _R.random() > 0.018,  # ~23 sin documentación
                    "latitud": round(z["latitud"] + _R.uniform(-0.012, 0.012), 6),
                    "longitud": round(z["longitud"] + _R.uniform(-0.012, 0.012), 6),
                }
            )
            n += 1
    return luminarias


# -------------------------------------------------------------------- AGUA
_SECTORES_AGUA = [
    ("SEC-01", "Níjar casco"),
    ("SEC-02", "San José puerto"),
    ("SEC-03", "San José playas"),
    ("SEC-04", "Campohermoso norte"),
    ("SEC-05", "Campohermoso sur"),
    ("SEC-06", "San Isidro"),
    ("SEC-07", "Rodalquilar"),
    ("SEC-08", "Las Negras"),
    ("SEC-09", "La Isleta"),
    ("SEC-10", "Los Albaricoques"),
    ("SEC-11", "Presillas Bajas"),
    ("SEC-12", "Fernán Pérez"),
    ("SEC-13", "El Barranquete"),
    ("SEC-14", "Agua Amarga"),
]


def generar_sectores_agua_seed() -> list[dict]:
    # 480 contadores, 86 % telelectura, 3 fugas repartidas, rendimiento medio ~84 %
    pesos = [_R.uniform(0.6, 1.6) for _ in _SECTORES_AGUA]
    total_w = sum(pesos)
    fugas_en = set(_R.sample(range(len(_SECTORES_AGUA)), 3))
    sectores = []
    contadores_rep = 0
    for i, (code, nombre) in enumerate(_SECTORES_AGUA):
        cont = round(480 * pesos[i] / total_w)
        if i == len(_SECTORES_AGUA) - 1:
            cont = 480 - contadores_rep
        contadores_rep += cont
        tele = round(cont * _R.uniform(0.80, 0.92))
        caudal = round(42 * pesos[i] / total_w, 2)
        tiene_fuga = i in fugas_en
        sectores.append(
            {
                "codigo": code,
                "nombre": nombre,
                "contadores": cont,
                "contadores_telelectura": tele,
                "caudal_entrada_ls": caudal,
                "caudal_nocturno_ls": round(
                    caudal * _R.uniform(0.35, 0.55) * (1.6 if tiene_fuga else 1.0), 2
                ),
                "presion_bar": round(_R.uniform(2.4, 3.2), 2),
                "rendimiento_pct": round(_R.uniform(74, 92) - (12 if tiene_fuga else 0), 2),
                "fugas_detectadas": 1 if tiene_fuga else 0,
                "estado": "alerta" if tiene_fuga else "operativo",
            }
        )
    return sectores


# ---------------------------------------------------------------- RESIDUOS
_FRACCIONES = ["organica", "envases", "papel", "vidrio", "resto"]
_RES_ZONAS = ["nijar", "sanjose", "campo", "roda", "negras", "albar"]
_RUTAS = ["R1", "R2", "R3", "R4", "R5", "R6"]


def generar_contenedores_seed() -> list[dict]:
    # 684 contenedores, 412 con sensor de llenado, dispersos alrededor de su zona
    zonas = {z["id"]: z for z in ZONAS_ALUMBRADO}
    idx_sensor = set(_R.sample(range(684), 412))
    contenedores = []
    for i in range(684):
        zid = _R.choices(_RES_ZONAS, weights=[30, 26, 20, 10, 8, 6])[0]
        z = zonas[zid]
        fraccion = _R.choice(_FRACCIONES)
        sensor = i in idx_sensor
        llenado = _R.randint(5, 100) if sensor else None
        estado = "operativo"
        if sensor and llenado is not None and llenado >= 85:
            estado = "alerta"
        contenedores.append(
            {
                "codigo": f"RSU-{i + 1:04d}",
                "zona_id": zid,
                "fraccion": fraccion,
                "tiene_sensor": sensor,
                "llenado_pct": llenado,
                "ruta": _R.choice(_RUTAS),
                "estado": estado,
                "latitud": round(z["latitud"] + _R.uniform(-0.012, 0.012), 6),
                "longitud": round(z["longitud"] + _jitter_lon(zid, 0.012), 6),
            }
        )
    return contenedores


# --------------------------------------------------------------- MOVILIDAD
# Coordenadas reales aproximadas de cada punto (WGS84). Se usan también en el
# backfill del seed_loader para bases sembradas por versiones sin coordenadas.
COORDS_MOVILIDAD: dict[str, tuple[float, float]] = {
    "MOV-01": (36.7755, -2.1295),  # Ctra. AL-3108, acceso al parque por San José
    "MOV-02": (36.8508, -2.0330),  # Ctra. del Playazo, Rodalquilar
    "MOV-03": (36.8785, -2.0062),  # AL-5106, Las Negras
    "MOV-04": (36.7440, -2.1230),  # Parking Genoveses
    "MOV-05": (36.7307, -2.1447),  # Parking Mónsul
    "MOV-06": (36.7618, -2.1067),  # Parking San José centro
    "MOV-07": (36.7712, -2.1108),  # Parking disuasorio, acceso San José
    "MOV-08": (36.9656, -2.2067),  # Recarga EV Ayuntamiento (Níjar)
    "MOV-09": (36.7603, -2.1055),  # Recarga EV Puerto de San José
    "MOV-10": (36.8494, -2.0402),  # Recarga EV Rodalquilar
    "MOV-11": (36.7560, -2.1150),  # Lanzadera San José ↔ playas
}


def generar_movilidad_seed() -> list[dict]:
    puntos = [
        {
            "codigo": "MOV-01",
            "nombre": "Aforo acceso Parque · San José",
            "tipo": "aforo",
            "ubicacion": "Ctra. AL-3108",
            "valor_actual": _R.randint(180, 420),
            "capacidad": None,
            "unidad": "veh/h",
            "estado": "operativo",
        },
        {
            "codigo": "MOV-02",
            "nombre": "Aforo acceso Rodalquilar",
            "tipo": "aforo",
            "ubicacion": "Ctra. del Playazo",
            "valor_actual": _R.randint(60, 180),
            "capacidad": None,
            "unidad": "veh/h",
            "estado": "operativo",
        },
        {
            "codigo": "MOV-03",
            "nombre": "Aforo acceso Las Negras",
            "tipo": "aforo",
            "ubicacion": "AL-5106",
            "valor_actual": _R.randint(40, 140),
            "capacidad": None,
            "unidad": "veh/h",
            "estado": "operativo",
        },
        {
            "codigo": "MOV-04",
            "nombre": "Parking Playa de los Genoveses",
            "tipo": "parking",
            "ubicacion": "Genoveses",
            "valor_actual": 289,
            "capacidad": 300,
            "unidad": "plazas",
            "estado": "alerta",
        },
        {
            "codigo": "MOV-05",
            "nombre": "Parking Playa de Mónsul",
            "tipo": "parking",
            "ubicacion": "Mónsul",
            "valor_actual": 176,
            "capacidad": 225,
            "unidad": "plazas",
            "estado": "operativo",
        },
        {
            "codigo": "MOV-06",
            "nombre": "Parking San José centro",
            "tipo": "parking",
            "ubicacion": "San José",
            "valor_actual": 141,
            "capacidad": 190,
            "unidad": "plazas",
            "estado": "operativo",
        },
        {
            "codigo": "MOV-07",
            "nombre": "Parking disuasorio (desvío estival)",
            "tipo": "parking",
            "ubicacion": "Acceso San José",
            "valor_actual": 351,
            "capacidad": 400,
            "unidad": "plazas",
            "estado": "operativo",
        },
        {
            "codigo": "MOV-08",
            "nombre": "Recarga EV · Ayuntamiento",
            "tipo": "recarga_ev",
            "ubicacion": "Plaza de la Glorieta",
            "valor_actual": 1,
            "capacidad": 2,
            "unidad": "tomas",
            "estado": "operativo",
        },
        {
            "codigo": "MOV-09",
            "nombre": "Recarga EV · San José",
            "tipo": "recarga_ev",
            "ubicacion": "Puerto",
            "valor_actual": 2,
            "capacidad": 2,
            "unidad": "tomas",
            "estado": "operativo",
        },
        {
            "codigo": "MOV-10",
            "nombre": "Recarga EV · Rodalquilar",
            "tipo": "recarga_ev",
            "ubicacion": "C/ del Oro",
            "valor_actual": 0,
            "capacidad": 2,
            "unidad": "tomas",
            "estado": "operativo",
        },
        {
            "codigo": "MOV-11",
            "nombre": "Lanzadera estival playas",
            "tipo": "lanzadera",
            "ubicacion": "San José ↔ Genoveses/Mónsul",
            "valor_actual": _R.randint(12, 46),
            "capacidad": 55,
            "unidad": "ocupación",
            "estado": "operativo",
        },
    ]
    for p in puntos:
        lat, lon = COORDS_MOVILIDAD[p["codigo"]]
        p["latitud"], p["longitud"] = lat, lon
    return puntos


# --------------------------------------------------------------- SEGURIDAD
_SEG_ZONAS = ["nijar", "sanjose", "campo", "roda", "negras", "albar"]

# Coordenadas reales aproximadas por emplazamiento (WGS84); también las usa el
# backfill del seed_loader para bases sembradas por versiones sin coordenadas.
COORDS_CAMARAS: dict[str, tuple[float, float]] = {
    "Playa de Mónsul": (36.7305, -2.1442),
    "Playa de los Genoveses": (36.7443, -2.1207),
    "Acceso San José": (36.7708, -2.1082),
    "Puerto de San José": (36.7605, -2.1058),
    "Plaza de la Glorieta": (36.9659, -2.2066),
    "Avda. García Lorca": (36.9648, -2.2079),
    "Acceso Rodalquilar": (36.8479, -2.0452),
    "Mirador de la Amatista": (36.8363, -2.0113),
    "Paseo del Mar (Las Negras)": (36.8793, -2.0034),
    "Acceso Los Albaricoques": (36.8721, -2.0803),
    "Centro de salud": (36.9644, -2.2074),
    "Ayuntamiento": (36.9656, -2.2070),
    "Recinto ferial": (36.9632, -2.2088),
    "Colegio Campohermoso": (36.8452, -2.1494),
    "Depósito de agua San José": (36.7641, -2.1093),
    "Nave de servicios": (36.8432, -2.1521),
    "Cala de Enmedio (sendero)": (36.9441, -1.9603),
    "Playa del Playazo": (36.8560, -2.0048),
    "Rotonda AL-3108": (36.8002, -2.1401),
    "Aparcamiento Genoveses": (36.7468, -2.1252),
    "Isleta del Moro": (36.8128, -2.0431),
    "Agua Amarga": (36.9393, -1.9363),
    "Fernán Pérez": (36.8763, -2.0532),
    "San Isidro": (36.8791, -2.1562),
}


def generar_camaras_seed() -> list[dict]:
    # 24 cámaras: 23 online, 1 sin comunicación
    ubic = list(COORDS_CAMARAS)
    camaras = []
    sin_com = _R.randrange(24)
    for i in range(24):
        zid = _R.choice(_SEG_ZONAS)
        lat, lon = COORDS_CAMARAS[ubic[i]]
        camaras.append(
            {
                "codigo": f"CCTV-{i + 1:02d}",
                "nombre": ubic[i],
                "zona_id": zid,
                "tipo": _R.choice(["fija", "domo", "domo", "lpr"]),
                "con_analitica": _R.random() < 0.55,
                "retencion_dias": 30,
                "estado": "sin_comunicacion" if i == sin_com else "operativo",
                "latitud": lat,
                "longitud": lon,
            }
        )
    return camaras


# ----------------------------------------------------------------- ENERGÍA
_EDIFICIOS = [
    "Ayuntamiento",
    "Casa Consistorial (anexo)",
    "Biblioteca municipal",
    "Centro de salud",
    "Colegio Ntra. Sra. del Rosario",
    "Colegio Campohermoso",
    "IES Río Aguas",
    "Polideportivo municipal",
    "Piscina municipal",
    "Recinto ferial",
    "Nave de servicios operativos",
    "Oficina de Turismo",
    "Centro de Visitantes Las Amoladeras",
    "Depósito de agua Níjar",
    "Depósito de agua San José",
    "Bombeo Campohermoso",
    "Centro social San José",
    "Centro social Rodalquilar",
    "Cementerio municipal",
    "Mercado municipal",
    "Guardería municipal",
    "Museo del Agua",
    "Tanatorio",
    "EDAR Níjar",
    "EDAR San José",
    "Alumbrado ornamental casco",
    "Fuentes ornamentales",
    "Parque de bomberos",
    "Almacén municipal",
    "Oficinas técnicas",
    "Centro de mayores",
    "Sala de exposiciones",
    "Punto limpio",
    "Vivero municipal",
]


def generar_suministros_energia_seed() -> list[dict]:
    # 61 CUPS en 34 edificios · 0,165 €/kWh medio · fotovoltaica en algunos
    n_por_edificio = [1] * len(_EDIFICIOS)  # 34 CUPS base (uno por edificio)
    for _ in range(61 - len(_EDIFICIOS)):  # +27 CUPS extra repartidos
        n_por_edificio[_R.randrange(len(_EDIFICIOS))] += 1
    suministros = []
    n = 0
    for ed, n_cups in zip(_EDIFICIOS, n_por_edificio, strict=False):
        for k in range(n_cups):
            consumo = round(_R.uniform(800, 14000), 2)
            fv = _R.random() < 0.28
            auto = round(consumo * _R.uniform(0.15, 0.4), 2) if fv else 0.0
            suministros.append(
                {
                    "cups": f"ES0031{_R.randint(10**11, 10**12 - 1)}{chr(65 + n % 26)}",
                    "edificio": ed if k == 0 else f"{ed} (CUPS {k + 1})",
                    "tipo": _R.choice(
                        ["dependencia municipal", "alumbrado", "bombeo", "climatización"]
                    ),
                    "potencia_contratada_kw": round(_R.uniform(6.9, 100), 2),
                    "consumo_mes_kwh": consumo,
                    "autoconsumo_mes_kwh": auto,
                    "coste_mes_eur": round((consumo - auto) * 0.165, 2),
                    "tiene_fotovoltaica": fv,
                    "estado": "operativo",
                }
            )
            n += 1
    return suministros
