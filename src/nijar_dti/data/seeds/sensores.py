"""Sensores ejemplo del Smart Office y de los puntos turísticos.

Coordenadas reales del Ayuntamiento de Níjar (lon: -2.207, lat: 36.965)
y de los dos tótems en la ruta Rodalquilar–Albaricoques.
"""

from __future__ import annotations


# Smart Office: 4 sensores ambientales (CO₂, temperatura, humedad, ruido).
# Tótems: meteo + aforo en cada uno de los 2 emplazamientos.
# Plaza La Glorieta: 1 punto WiFi público para conteo de dispositivos únicos.
# Total: 9 sensores.

SENSORES_SEED: list[dict] = [
    # ---------- Smart Office ----------
    {
        "urn": "urn:ngsi-ld:Device:nijar:co2:smartoffice-01",
        "nombre": "CO₂ - Smart Office (sala principal)",
        "tipo": "ambiental_co2",
        "fabricante": "Sensirion",
        "modelo": "SCD41",
        "lon": -2.207, "lat": 36.965,
        "descripcion_ubicacion": "Sala principal del Smart Office (Ayuntamiento)",
        "unidades_medida": "ppm",
        "rango_minimo": 400.0,
        "rango_maximo": 5000.0,
        "umbrales_alerta": {"warning_max": 1000, "critical_max": 2000},
        "frecuencia_muestreo_seg": 60,
        "estado": "operativo",
        "topic_mqtt": "nijar/sensors/smartoffice-01/co2",
        "etiquetas": ["smart-office", "ambiental", "salud"],
    },
    {
        "urn": "urn:ngsi-ld:Device:nijar:temp:smartoffice-01",
        "nombre": "Temperatura - Smart Office (sala principal)",
        "tipo": "ambiental_temperatura",
        "fabricante": "Sensirion",
        "modelo": "SHT4x",
        "lon": -2.207, "lat": 36.965,
        "descripcion_ubicacion": "Sala principal del Smart Office (Ayuntamiento)",
        "unidades_medida": "°C",
        "rango_minimo": -10.0,
        "rango_maximo": 50.0,
        "umbrales_alerta": {"warning_min": 18, "warning_max": 28, "critical_max": 35},
        "frecuencia_muestreo_seg": 60,
        "estado": "operativo",
        "topic_mqtt": "nijar/sensors/smartoffice-01/temp",
        "etiquetas": ["smart-office", "ambiental", "confort"],
    },
    {
        "urn": "urn:ngsi-ld:Device:nijar:hum:smartoffice-01",
        "nombre": "Humedad - Smart Office (sala principal)",
        "tipo": "ambiental_humedad",
        "fabricante": "Sensirion",
        "modelo": "SHT4x",
        "lon": -2.207, "lat": 36.965,
        "descripcion_ubicacion": "Sala principal del Smart Office (Ayuntamiento)",
        "unidades_medida": "%",
        "rango_minimo": 0.0,
        "rango_maximo": 100.0,
        "umbrales_alerta": {"warning_min": 30, "warning_max": 70},
        "frecuencia_muestreo_seg": 60,
        "estado": "operativo",
        "topic_mqtt": "nijar/sensors/smartoffice-01/hum",
        "etiquetas": ["smart-office", "ambiental", "confort"],
    },
    {
        "urn": "urn:ngsi-ld:Device:nijar:noise:smartoffice-01",
        "nombre": "Ruido - Smart Office (sala principal)",
        "tipo": "ambiental_ruido",
        "fabricante": "GENERIC",
        "modelo": "MEMS-MIC-01",
        "lon": -2.207, "lat": 36.965,
        "descripcion_ubicacion": "Sala principal del Smart Office (Ayuntamiento)",
        "unidades_medida": "dB",
        "rango_minimo": 30.0,
        "rango_maximo": 130.0,
        "umbrales_alerta": {"warning_max": 65, "critical_max": 85},
        "frecuencia_muestreo_seg": 60,
        "estado": "operativo",
        "topic_mqtt": "nijar/sensors/smartoffice-01/noise",
        "etiquetas": ["smart-office", "ambiental", "salud"],
    },

    # ---------- Tótem Rodalquilar ----------
    {
        "urn": "urn:ngsi-ld:Device:nijar:meteo:totem-rodalquilar",
        "nombre": "Estación meteo - Tótem Rodalquilar",
        "tipo": "meteo",
        "fabricante": "Davis Instruments",
        "modelo": "Vantage Pro2",
        "lon": -2.043, "lat": 36.853,
        "descripcion_ubicacion": "Tótem digital interactivo en Rodalquilar",
        "unidades_medida": "varios",
        "frecuencia_muestreo_seg": 300,
        "estado": "operativo",
        "topic_mqtt": "nijar/sensors/totem-rodalquilar/meteo",
        "etiquetas": ["totem", "meteo", "ruta"],
    },
    {
        "urn": "urn:ngsi-ld:Device:nijar:aforo:totem-rodalquilar",
        "nombre": "Conteo de personas - Tótem Rodalquilar",
        "tipo": "aforo",
        "fabricante": "GENERIC",
        "modelo": "PIR-Counter-01",
        "lon": -2.043, "lat": 36.853,
        "descripcion_ubicacion": "Tótem digital interactivo en Rodalquilar",
        "unidades_medida": "personas",
        "frecuencia_muestreo_seg": 60,
        "estado": "operativo",
        "topic_mqtt": "nijar/sensors/totem-rodalquilar/aforo",
        "etiquetas": ["totem", "aforo", "turismo"],
    },

    # ---------- Tótem Albaricoques ----------
    {
        "urn": "urn:ngsi-ld:Device:nijar:meteo:totem-albaricoques",
        "nombre": "Estación meteo - Tótem Albaricoques",
        "tipo": "meteo",
        "fabricante": "Davis Instruments",
        "modelo": "Vantage Pro2",
        "lon": -2.080, "lat": 36.872,
        "descripcion_ubicacion": "Tótem digital interactivo en Los Albaricoques",
        "unidades_medida": "varios",
        "frecuencia_muestreo_seg": 300,
        "estado": "operativo",
        "topic_mqtt": "nijar/sensors/totem-albaricoques/meteo",
        "etiquetas": ["totem", "meteo", "ruta"],
    },
    {
        "urn": "urn:ngsi-ld:Device:nijar:aforo:totem-albaricoques",
        "nombre": "Conteo de personas - Tótem Albaricoques",
        "tipo": "aforo",
        "fabricante": "GENERIC",
        "modelo": "PIR-Counter-01",
        "lon": -2.080, "lat": 36.872,
        "descripcion_ubicacion": "Tótem digital interactivo en Los Albaricoques",
        "unidades_medida": "personas",
        "frecuencia_muestreo_seg": 60,
        "estado": "operativo",
        "topic_mqtt": "nijar/sensors/totem-albaricoques/aforo",
        "etiquetas": ["totem", "aforo", "turismo"],
    },

    # ---------- WiFi público Plaza La Glorieta ----------
    {
        "urn": "urn:ngsi-ld:Device:nijar:wifi:plaza-glorieta",
        "nombre": "WiFi público - Plaza La Glorieta",
        "tipo": "wifi_publico",
        "fabricante": "Cambium Networks",
        "modelo": "cnPilot E410",
        "lon": -2.207, "lat": 36.966,
        "descripcion_ubicacion": "Plaza La Glorieta (centro histórico de Níjar)",
        "unidades_medida": "dispositivos_unicos",
        "rango_minimo": 0.0,
        "rango_maximo": 500.0,
        "umbrales_alerta": {"warning_max": 300},
        "frecuencia_muestreo_seg": 300,
        "estado": "operativo",
        "topic_mqtt": "nijar/sensors/plaza-glorieta/wifi",
        "etiquetas": ["wifi", "afluencia", "centro-historico"],
    },
]
