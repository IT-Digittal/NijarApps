"""Catálogo inicial de recursos turísticos de Níjar.

Coordenadas reales de los principales POIs del Parque Natural Cabo de Gata-Níjar
y del término municipal. Todos publicables tras revisión por el Ayuntamiento.

Todos los recursos incluyen `nombre_i18n` y `descripcion_i18n` en los cuatro
idiomas atendidos por los tótems (es, en, de, fr) para garantizar experiencia
multilingüe consistente al turista.
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
        "lon": -2.1445,
        "lat": 36.7307,
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
        "descripcion_i18n": {
            "es": "Playa virgen de gran extensión rodeada de campos de pitas, sin construcciones.",
            "en": "Large unspoiled beach surrounded by agave fields, with no buildings.",
            "de": "Weitläufiger unberührter Strand, umgeben von Agavenfeldern, ohne Bebauung.",
            "fr": "Vaste plage sauvage entourée de champs d'agaves, sans constructions.",
        },
        "lon": -2.1225,
        "lat": 36.7442,
        "etiquetas": ["playa", "parque-natural", "virgen"],
        "publicado": True,
    },
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:playa-playazo",
        "nombre": "Playa del Playazo",
        "categoria": "playa",
        "descripcion_corta": "Playa amplia con el Castillo de San Ramón al fondo, junto a Rodalquilar.",
        "nombre_i18n": {
            "es": "Playa del Playazo",
            "en": "Playazo Beach",
            "de": "Playazo-Strand",
            "fr": "Plage du Playazo",
        },
        "descripcion_i18n": {
            "es": "Playa amplia con el Castillo de San Ramón al fondo, junto a Rodalquilar.",
            "en": "Wide beach with the San Ramón Castle in the background, next to Rodalquilar.",
            "de": "Breiter Strand mit der Burg San Ramón im Hintergrund, nahe Rodalquilar.",
            "fr": "Vaste plage avec le château de San Ramón en arrière-plan, près de Rodalquilar.",
        },
        "lon": -2.0060,
        "lat": 36.8567,
        "etiquetas": ["playa", "patrimonio"],
        "publicado": True,
    },
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:cala-enmedio",
        "nombre": "Cala de Enmedio",
        "categoria": "playa",
        "descripcion_corta": "Pequeña cala virgen accesible únicamente a pie, con rocas erosionadas espectaculares.",
        "nombre_i18n": {
            "es": "Cala de Enmedio",
            "en": "Enmedio Cove",
            "de": "Enmedio-Bucht",
            "fr": "Crique d'Enmedio",
        },
        "descripcion_i18n": {
            "es": "Pequeña cala virgen accesible únicamente a pie, con rocas erosionadas espectaculares.",
            "en": "Small unspoiled cove accessible only on foot, with spectacular eroded rocks.",
            "de": "Kleine unberührte Bucht, nur zu Fuß erreichbar, mit spektakulären erodierten Felsen.",
            "fr": "Petite crique vierge accessible uniquement à pied, avec des rochers érodés spectaculaires.",
        },
        "lon": -1.9563,
        "lat": 36.9468,
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
        "descripcion_i18n": {
            "es": "Centro principal de información del Parque Natural Cabo de Gata-Níjar.",
            "en": "Main information centre for the Cabo de Gata-Níjar Natural Park.",
            "de": "Hauptinformationszentrum des Naturparks Cabo de Gata-Níjar.",
            "fr": "Centre principal d'information du Parc Naturel de Cabo de Gata-Níjar.",
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
        "nombre_i18n": {
            "es": "Oficina de Turismo de Níjar",
            "en": "Níjar Tourist Office",
            "de": "Touristeninformation Níjar",
            "fr": "Office de Tourisme de Níjar",
        },
        "descripcion_i18n": {
            "es": "Oficina municipal de turismo en el casco histórico de Níjar.",
            "en": "Municipal tourist office in the historic centre of Níjar.",
            "de": "Städtische Touristeninformation in der Altstadt von Níjar.",
            "fr": "Office de tourisme municipal dans le centre historique de Níjar.",
        },
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
        "descripcion_i18n": {
            "es": "Ruta cicloturista de 8,5 km que conecta Rodalquilar con Los Albaricoques atravesando paisajes mineros y la rambla.",
            "en": "8.5 km cycling route connecting Rodalquilar with Los Albaricoques through mining landscapes and the ravine.",
            "de": "8,5 km lange Radroute, die Rodalquilar mit Los Albaricoques durch Bergbaulandschaften und die Rambla verbindet.",
            "fr": "Itinéraire cyclable de 8,5 km reliant Rodalquilar à Los Albaricoques à travers les paysages miniers et la rambla.",
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
        "nombre_i18n": {
            "es": "Sendero del Faro de Cabo de Gata a Vela Blanca",
            "en": "Cabo de Gata Lighthouse to Vela Blanca trail",
            "de": "Wanderweg vom Leuchtturm Cabo de Gata nach Vela Blanca",
            "fr": "Sentier du Phare de Cabo de Gata à Vela Blanca",
        },
        "descripcion_i18n": {
            "es": "Espectacular sendero costero con vistas a los acantilados volcánicos.",
            "en": "Spectacular coastal path with views of the volcanic cliffs.",
            "de": "Spektakulärer Küstenweg mit Blick auf die vulkanischen Klippen.",
            "fr": "Spectaculaire sentier côtier avec vue sur les falaises volcaniques.",
        },
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
        "nombre_i18n": {
            "es": "Antigua mina de oro de Rodalquilar",
            "en": "Former Rodalquilar gold mine",
            "de": "Ehemalige Goldmine von Rodalquilar",
            "fr": "Ancienne mine d'or de Rodalquilar",
        },
        "descripcion_i18n": {
            "es": "Patrimonio industrial minero del siglo XX, hoy convertido en escenario singular.",
            "en": "20th-century industrial mining heritage, today a unique open-air setting.",
            "de": "Industrieerbe des Bergbaus aus dem 20. Jahrhundert, heute eine einzigartige Kulisse.",
            "fr": "Patrimoine industriel minier du XXe siècle, devenu aujourd'hui un décor unique.",
        },
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
        "nombre_i18n": {
            "es": "Los Albaricoques",
            "en": "Los Albaricoques",
            "de": "Los Albaricoques",
            "fr": "Los Albaricoques",
        },
        "descripcion_i18n": {
            "es": "Núcleo rural conocido por ser escenario de las películas del oeste de Sergio Leone.",
            "en": "Rural village famous as a filming location for Sergio Leone's spaghetti westerns.",
            "de": "Ländlicher Ort, bekannt als Drehort der Italowestern von Sergio Leone.",
            "fr": "Village rural célèbre comme lieu de tournage des westerns de Sergio Leone.",
        },
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
        "nombre_i18n": {
            "es": "La Isleta del Moro",
            "en": "La Isleta del Moro",
            "de": "La Isleta del Moro",
            "fr": "La Isleta del Moro",
        },
        "descripcion_i18n": {
            "es": "Pintoresco pueblo pesquero con casas blancas y barcas tradicionales.",
            "en": "Picturesque fishing village with whitewashed houses and traditional boats.",
            "de": "Malerisches Fischerdorf mit weiß getünchten Häusern und traditionellen Booten.",
            "fr": "Village de pêcheurs pittoresque aux maisons blanches et barques traditionnelles.",
        },
        "lon": -2.0430,
        "lat": 36.8129,
        "etiquetas": ["pueblo", "pesca", "gastronomia"],
        "publicado": True,
    },
    {
        "urn": "urn:ngsi-ld:RecursoTuristico:nijar:san-jose",
        "nombre": "San José",
        "categoria": "punto_interes",
        "descripcion_corta": "Principal núcleo turístico del Parque Natural, base ideal para visitar las playas.",
        "nombre_i18n": {
            "es": "San José",
            "en": "San José",
            "de": "San José",
            "fr": "San José",
        },
        "descripcion_i18n": {
            "es": "Principal núcleo turístico del Parque Natural, base ideal para visitar las playas.",
            "en": "Main tourist hub of the natural park and ideal base to visit the beaches.",
            "de": "Wichtigstes Touristenzentrum des Naturparks und idealer Ausgangspunkt für die Strände.",
            "fr": "Principal pôle touristique du parc naturel, base idéale pour visiter les plages.",
        },
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
        "nombre_i18n": {
            "es": "Casco histórico de Níjar",
            "en": "Historic centre of Níjar",
            "de": "Altstadt von Níjar",
            "fr": "Centre historique de Níjar",
        },
        "descripcion_i18n": {
            "es": "Casco histórico declarado conjunto histórico-artístico, famoso por su artesanía y jarapas.",
            "en": "Officially listed historic-artistic ensemble, renowned for its craftsmanship and jarapa rugs.",
            "de": "Als historisch-künstlerisches Ensemble ausgezeichnete Altstadt, bekannt für Handwerk und Jarapas.",
            "fr": "Centre historique classé ensemble historico-artistique, réputé pour son artisanat et ses jarapas.",
        },
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
        "nombre_i18n": {
            "es": "Mirador de la Amatista",
            "en": "Amatista Viewpoint",
            "de": "Aussichtspunkt La Amatista",
            "fr": "Belvédère de la Amatista",
        },
        "descripcion_i18n": {
            "es": "Mirador con vistas espectaculares de la costa y el Arrecife de las Sirenas.",
            "en": "Viewpoint with spectacular views of the coast and the Arrecife de las Sirenas reef.",
            "de": "Aussichtspunkt mit spektakulärem Blick auf die Küste und das Arrecife de las Sirenas.",
            "fr": "Belvédère offrant une vue spectaculaire sur la côte et l'Arrecife de las Sirenas.",
        },
        "lon": -2.0113,
        "lat": 36.8360,
        "etiquetas": ["mirador", "panoramica", "fotografia"],
        "publicado": True,
    },
]

# Red oficial de senderos de turismonijar.es (S01–S16 + Camino Argar Sureste)
from nijar_dti.data.seeds.senderos import SENDEROS_SEED  # noqa: E402

RECURSOS_SEED.extend(SENDEROS_SEED)
