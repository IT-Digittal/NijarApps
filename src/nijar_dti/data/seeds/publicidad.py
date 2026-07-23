"""Seeder del módulo de publicidad: empresas anunciantes de demostración.

Datos de ejemplo (nombres ficticios) para que el apartado «Empresas» del
tótem tenga contenido desde el primer arranque; el gestor los sustituye por
los anunciantes reales desde el panel.
"""

from __future__ import annotations

EMPRESAS_SEED: list[dict] = [
    {
        "nombre": "Restaurante La Ola",
        "sector": "gastronomia",
        "descripcion": "Pescado fresco de la bahía y arroces marineros frente al puerto de San José.",
        "descripcion_i18n": {
            "es": "Pescado fresco de la bahía y arroces marineros frente al puerto de San José.",
            "en": "Fresh local fish and seafood rice dishes by San José harbour.",
            "de": "Frischer Fisch aus der Bucht und Meeresreisgerichte am Hafen von San José.",
            "fr": "Poisson frais de la baie et riz marins face au port de San José.",
        },
        "nucleo": "San José",
        "direccion": "Paseo Marítimo, 12",
        "telefono": "+34 950 000 001",
        "web": "https://ejemplo-laola.es",
        "destacado": True,
        "prioridad": 10,
        "publicado": True,
        "latitud": 36.7609,
        "longitud": -2.1062,
    },
    {
        "nombre": "Hotel Mirador del Cabo",
        "sector": "alojamiento",
        "descripcion": "Hotel boutique con vistas al valle minero de Rodalquilar y al parque natural.",
        "descripcion_i18n": {
            "es": "Hotel boutique con vistas al valle minero de Rodalquilar y al parque natural.",
            "en": "Boutique hotel overlooking the Rodalquilar mining valley and the natural park.",
            "de": "Boutique-Hotel mit Blick auf das Minental von Rodalquilar und den Naturpark.",
            "fr": "Hôtel boutique avec vue sur la vallée minière de Rodalquilar et le parc naturel.",
        },
        "nucleo": "Rodalquilar",
        "direccion": "C/ Los Mineros, 4",
        "telefono": "+34 950 000 002",
        "web": "https://ejemplo-miradordelcabo.es",
        "destacado": False,
        "prioridad": 5,
        "publicado": True,
        "latitud": 36.8515,
        "longitud": -2.0420,
    },
    {
        "nombre": "Kayak Cabo Activo",
        "sector": "ocio_activo",
        "descripcion": "Rutas guiadas en kayak y snorkel por los acantilados y calas del parque.",
        "descripcion_i18n": {
            "es": "Rutas guiadas en kayak y snorkel por los acantilados y calas del parque.",
            "en": "Guided kayak and snorkel tours along the park's cliffs and coves.",
            "de": "Geführte Kajak- und Schnorcheltouren entlang der Klippen und Buchten.",
            "fr": "Sorties guidées en kayak et snorkel le long des falaises et criques du parc.",
        },
        "nucleo": "Las Negras",
        "direccion": "Paseo del Mar, 8",
        "telefono": "+34 950 000 003",
        "web": "https://ejemplo-caboactivo.es",
        "destacado": False,
        "prioridad": 4,
        "publicado": True,
        "latitud": 36.8795,
        "longitud": -2.0042,
    },
    {
        "nombre": "Alfarería El Oficio",
        "sector": "comercio",
        "descripcion": "Cerámica y jarapas artesanas de Níjar, elaboradas en taller propio desde 1952.",
        "descripcion_i18n": {
            "es": "Cerámica y jarapas artesanas de Níjar, elaboradas en taller propio desde 1952.",
            "en": "Handmade Níjar pottery and jarapa rugs, crafted in our own workshop since 1952.",
            "de": "Handgemachte Keramik und Jarapa-Teppiche aus Níjar, seit 1952 aus eigener Werkstatt.",
            "fr": "Céramique et jarapas artisanales de Níjar, fabriquées dans notre atelier depuis 1952.",
        },
        "nucleo": "Níjar",
        "direccion": "C/ Real, 22",
        "telefono": "+34 950 000 004",
        "web": None,
        "destacado": False,
        "prioridad": 3,
        "publicado": True,
        "latitud": 36.9653,
        "longitud": -2.2068,
    },
]
