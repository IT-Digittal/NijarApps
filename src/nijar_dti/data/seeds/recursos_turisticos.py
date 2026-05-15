"""Catálogo inicial de recursos turísticos de Níjar.

Coordenadas reales de los principales POIs del Parque Natural Cabo de Gata-Níjar
y del término municipal. Todos publicables tras revisión por el Ayuntamiento.
"""

from __future__ import annotations


RECURSOS_SEED: list[dict] = [
    # ----------- Playas -----------
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:playa-monsul",
        "nombre": "Playa de Mónsul",
        "categoria": "playa",
        "descripcion_corta": "Una de las playas más icónicas de Cabo de Gata, con su característica duna y la Peineta.",
        "nombre_i18n": {
            "es": "Playa de Mónsul",
            "en": "Mónsul Beach",
            "de": "Strand von Mónsul",
            "fr": "Plage de Mónsul",
        },
        "descripcion_i18n": {
            "es": "Playa de arena dorada y formaciones rocosas volcánicas únicas. Acceso restringido en verano por aforo.",
            "en": "Golden sand beach with unique volcanic rock formations. Access restricted in summer due to capacity.",
            "de": "Goldener Sandstrand mit einzigartigen vulkanischen Felsformationen. Im Sommer Zugangsbeschränkung.",
            "fr": "Plage de sable doré et formations rocheuses volcaniques uniques. Accès restreint en été.",
        },
        "lon": -2.155,
        "lat": 36.741,
        "etiquetas": ["playa", "parque-natural", "fotografia", "iconico"],
        "publicado": True,
    },
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:playa-genoveses",
        "nombre": "Playa de los Genoveses",
        "categoria": "playa",
        "descripcion_corta": "Playa virgen de gran extensión rodeada de campos de pitas, sin construcciones.",
        "nombre_i18n": {
            "es": "Playa de los Genoveses",
            "en": "Genoveses Beach",
            "de": "Genoveses-Strand",
            "fr": "Plage des Génois",
        },
        "lon": -2.131,
        "lat": 36.749,
        "etiquetas": ["playa", "parque-natural", "virgen"],
        "publicado": True,
    },
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:playa-playazo",
        "nombre": "Playa del Playazo",
        "categoria": "playa",
        "descripcion_corta": "Playa amplia con el Castillo de San Ramón al fondo, junto a Rodalquilar.",
        "lon": -2.024,
        "lat": 36.864,
        "etiquetas": ["playa", "patrimonio"],
        "publicado": True,
    },
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:cala-enmedio",
        "nombre": "Cala de Enmedio",
        "categoria": "playa",
        "descripcion_corta": "Pequeña cala virgen accesible únicamente a pie, con rocas erosionadas espectaculares.",
        "lon": -1.986,
        "lat": 36.901,
        "etiquetas": ["playa", "cala", "parque-natural", "senderismo"],
        "publicado": True,
    },

    # ----------- Centros y oficinas -----------
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:centro-amoladeras",
        "nombre": "Centro de Visitantes Las Amoladeras",
        "categoria": "centro_visitantes",
        "descripcion_corta": "Centro principal de información del Parque Natural Cabo de Gata-Níjar.",
        "nombre_i18n": {
            "es": "Centro de Visitantes Las Amoladeras",
            "en": "Las Amoladeras Visitor Center",
            "de": "Besucherzentrum Las Amoladeras",
            "fr": "Centre des Visiteurs Las Amoladeras",
        },
        "lon": -2.195,
        "lat": 36.794,
        "horario": {
            "verano": "10:00-14:00",
            "invierno": "10:00-15:00, fines de semana 10:00-14:00",
        },
        "telefono": "+34 950 16 04 35",
        "etiquetas": ["centro", "informacion", "parque-natural"],
        "publicado": True,
    },
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:oficina-turismo-nijar",
        "nombre": "Oficina de Turismo de Níjar",
        "categoria": "oficina_turismo",
        "descripcion_corta": "Oficina municipal de turismo en el casco histórico de Níjar.",
        "lon": -2.207,
        "lat": 36.965,
        "etiquetas": ["oficina", "informacion"],
        "publicado": True,
    },

    # ----------- Rutas -----------
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:ruta-rodalquilar-albaricoques",
        "nombre": "Ruta cicloturista Rodalquilar–Albaricoques",
        "categoria": "ruta",
        "descripcion_corta": "Ruta cicloturista de 8,5 km que conecta Rodalquilar con Los Albaricoques atravesando paisajes mineros y la rambla.",
        "nombre_i18n": {
            "es": "Ruta cicloturista Rodalquilar–Albaricoques",
            "en": "Rodalquilar–Albaricoques cycling route",
            "de": "Radroute Rodalquilar–Albaricoques",
            "fr": "Itinéraire cyclable Rodalquilar–Albaricoques",
        },
        "lon": -2.041,
        "lat": 36.857,
        "etiquetas": ["ruta", "ciclismo", "senderismo", "parque-natural", "cine"],
        "servicios_disponibles": ["totem_digital_inicio", "totem_digital_fin"],
        "publicado": True,
    },
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:ruta-vela-blanca",
        "nombre": "Sendero del Faro de Cabo de Gata a Vela Blanca",
        "categoria": "ruta",
        "descripcion_corta": "Espectacular sendero costero con vistas a los acantilados volcánicos.",
        "lon": -2.193,
        "lat": 36.730,
        "etiquetas": ["ruta", "senderismo", "panoramica"],
        "publicado": True,
    },

    # ----------- Patrimonio -----------
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:rodalquilar-mina",
        "nombre": "Antigua mina de oro de Rodalquilar",
        "categoria": "yacimiento",
        "descripcion_corta": "Patrimonio industrial minero del siglo XX, hoy convertido en escenario singular.",
        "lon": -2.043,
        "lat": 36.853,
        "etiquetas": ["patrimonio", "mineria", "fotografia"],
        "publicado": True,
    },
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:los-albaricoques",
        "nombre": "Los Albaricoques",
        "categoria": "punto_interes",
        "descripcion_corta": "Núcleo rural conocido por ser escenario de las películas del oeste de Sergio Leone.",
        "lon": -2.080,
        "lat": 36.872,
        "etiquetas": ["pueblo", "cine", "ruta"],
        "publicado": True,
    },
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:isleta-del-moro",
        "nombre": "La Isleta del Moro",
        "categoria": "punto_interes",
        "descripcion_corta": "Pintoresco pueblo pesquero con casas blancas y barcas tradicionales.",
        "lon": -2.000,
        "lat": 36.815,
        "etiquetas": ["pueblo", "pesca", "gastronomia"],
        "publicado": True,
    },
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:san-jose",
        "nombre": "San José",
        "categoria": "punto_interes",
        "descripcion_corta": "Principal núcleo turístico del Parque Natural, base ideal para visitar las playas.",
        "lon": -2.108,
        "lat": 36.764,
        "etiquetas": ["pueblo", "turismo", "playa"],
        "publicado": True,
    },
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:nijar-pueblo",
        "nombre": "Casco histórico de Níjar",
        "categoria": "monumento",
        "descripcion_corta": "Casco histórico declarado conjunto histórico-artístico, famoso por su artesanía y jarapas.",
        "lon": -2.207,
        "lat": 36.965,
        "etiquetas": ["pueblo", "patrimonio", "artesania"],
        "publicado": True,
    },

    # ----------- Miradores -----------
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:mirador-amatista",
        "nombre": "Mirador de la Amatista",
        "categoria": "mirador",
        "descripcion_corta": "Mirador con vistas espectaculares de la costa y el Arrecife de las Sirenas.",
        "lon": -1.989,
        "lat": 36.819,
        "etiquetas": ["mirador", "panoramica", "fotografia"],
        "publicado": True,
    },
]
