"""Red oficial de senderos de turismonijar.es (S01–S16) + Camino Argar Sureste.

Contenido rescatado de las fichas públicas de la web municipal de turismo
(https://turismonijar.es → Experiencias → Senderos) el 02/09/2026, a petición
del Ayuntamiento, para alimentar la sección de rutas del tótem, la web y el
chatbot:

- Descripción y puntos de interés: condensados de la ficha de cada sendero.
- Punto de inicio: primer punto del track GPX oficial que publica la web.
- Ficha técnica (longitud, duración, dificultad, trayecto, desnivel):
  ``metadata_adicional``.
- Enlaces a la ficha web y al GPX descargable: ``enlaces_externos``.

Los textos EN/DE/FR son traducciones propias del contenido en castellano.
"""

_BASE = "https://turismonijar.es/experiencias/senderos"
_GPX = "https://turismonijar.es/rutas"


def _sendero(
    slug: str,
    codigo: str,
    gpx: str | None,
    lat: float,
    lon: float,
    nombre_i18n: dict[str, str],
    desc_i18n: dict[str, str],
    etiquetas: list[str],
    ficha: dict[str, str] | None = None,
) -> dict:
    return {
        "urn": f"urn:ngsi-ld:RecursoTuristico:nijar:sendero-{codigo.lower()}",
        "nombre": nombre_i18n["es"],
        "categoria": "ruta",
        "descripcion_corta": desc_i18n["es"],
        "nombre_i18n": nombre_i18n,
        "descripcion_i18n": desc_i18n,
        "lat": lat,
        "lon": lon,
        "etiquetas": ["ruta", "senderismo", *etiquetas],
        "web": f"{_BASE}/{slug}/",
        "enlaces_externos": {
            "ficha_web": f"{_BASE}/{slug}/",
            **({"gpx": gpx} if gpx else {}),
        },
        "metadata_adicional": {
            "codigo_sendero": codigo,
            "fuente": "turismonijar.es",
            **(ficha or {}),
        },
        "publicado": True,
    }


SENDEROS_SEED: list[dict] = [
    _sendero(
        "vela-blanca",
        "S01",
        f"{_GPX}/s01.gpx",
        36.73353,
        -2.14723,
        {
            "es": "S01 · Sendero de Vela Blanca",
            "en": "S01 · Vela Blanca trail",
            "de": "S01 · Wanderweg Vela Blanca",
            "fr": "S01 · Sentier de Vela Blanca",
        },
        {
            "es": "Sendero litoral entre la Casa de Mónsul y el mirador de Vela Blanca, por acantilados volcánicos y calas como Media Luna y Cala Carbón, coronado por la torre vigía del siglo XV.",
            "en": "Coastal trail from Casa de Mónsul to the Vela Blanca viewpoint, along volcanic cliffs and coves such as Media Luna and Cala Carbón, crowned by the 15th-century watchtower.",
            "de": "Küstenweg von der Casa de Mónsul zum Aussichtspunkt Vela Blanca, vorbei an Vulkanklippen und Buchten wie Media Luna und Cala Carbón, gekrönt vom Wachturm aus dem 15. Jahrhundert.",
            "fr": "Sentier littoral de la Casa de Mónsul au belvédère de Vela Blanca, le long de falaises volcaniques et de criques comme Media Luna et Cala Carbón, couronné par la tour de guet du XVe siècle.",
        },
        ["parque-natural", "panoramica", "playa"],
        {
            "longitud": "5,9 km",
            "duracion": "2h 30m",
            "dificultad": "Baja",
            "trayecto": "Lineal",
            "desnivel_maximo": "120 m",
        },
    ),
    _sendero(
        "los-genoveses",
        "S02",
        f"{_GPX}/s02.gpx",
        36.75227,
        -2.10724,
        {
            "es": "S02 · Sendero de Los Genoveses",
            "en": "S02 · Los Genoveses trail",
            "de": "S02 · Wanderweg Los Genoveses",
            "fr": "S02 · Sentier de Los Genoveses",
        },
        {
            "es": "Paseo por la bahía de Los Genoveses entre dunas suaves, barrancos y vegetación adaptada al clima árido, con vistas impresionantes de una de las playas más emblemáticas del parque.",
            "en": "A walk around Los Genoveses bay among gentle dunes, gullies and arid-climate vegetation, with stunning views over one of the park's most iconic beaches.",
            "de": "Spaziergang um die Bucht von Los Genoveses zwischen sanften Dünen, Schluchten und an das Trockenklima angepasster Vegetation, mit herrlichem Blick auf einen der bekanntesten Strände des Parks.",
            "fr": "Promenade autour de la baie de Los Genoveses entre dunes douces, ravins et végétation adaptée au climat aride, avec des vues superbes sur l'une des plages les plus emblématiques du parc.",
        },
        ["parque-natural", "playa", "familiar"],
        {
            "longitud": "2,3 km",
            "duracion": "1h 30m",
            "dificultad": "Baja",
            "trayecto": "Lineal",
            "desnivel_maximo": "41 m",
        },
    ),
    _sendero(
        "loma-pelada",
        "S03",
        f"{_GPX}/s03.gpx",
        36.79693,
        -2.06229,
        {
            "es": "S03 · Sendero de Loma Pelada",
            "en": "S03 · Loma Pelada trail",
            "de": "S03 · Wanderweg Loma Pelada",
            "fr": "S03 · Sentier de Loma Pelada",
        },
        {
            "es": "Franja costera de gran belleza desde el castillo de San Felipe (Los Escullos): paisajes volcánicos, acantilados y pequeñas calas con vistas del Parque Natural Cabo de Gata-Níjar.",
            "en": "A beautiful stretch of coast from San Felipe castle (Los Escullos): volcanic landscapes, cliffs and small coves with views over the Cabo de Gata-Níjar Natural Park.",
            "de": "Wunderschöner Küstenabschnitt ab der Burg San Felipe (Los Escullos): Vulkanlandschaften, Klippen und kleine Buchten mit Blick auf den Naturpark Cabo de Gata-Níjar.",
            "fr": "Magnifique bande côtière depuis le château de San Felipe (Los Escullos) : paysages volcaniques, falaises et petites criques avec vue sur le parc naturel de Cabo de Gata-Níjar.",
        },
        ["parque-natural", "panoramica"],
        {
            "longitud": "5,9 km",
            "duracion": "2h 30m",
            "dificultad": "Baja",
            "trayecto": "Lineal",
            "desnivel_maximo": "120 m",
        },
    ),
    _sendero(
        "sendero-azul",
        "S04",
        f"{_GPX}/s04.gpx",
        36.76828,
        -2.10831,
        {
            "es": "S04 · Sendero Azul César Díaz Torres",
            "en": "S04 · César Díaz Torres blue trail",
            "de": "S04 · Blauer Weg César Díaz Torres",
            "fr": "S04 · Sentier bleu César Díaz Torres",
        },
        {
            "es": "Entre el Pozo de los Frailes y San José, junto a cortijadas y el molino de agua con noria del Pozo de los Frailes, un conjunto etnográfico que cuenta el pasado agrícola de la zona.",
            "en": "Between Pozo de los Frailes and San José, past farmsteads and the Pozo de los Frailes water mill with its waterwheel, an ethnographic site that tells the area's farming past.",
            "de": "Zwischen Pozo de los Frailes und San José, vorbei an Gehöften und der Wassermühle mit Schöpfrad von Pozo de los Frailes, einem ethnografischen Ensemble über die landwirtschaftliche Vergangenheit.",
            "fr": "Entre le Pozo de los Frailes et San José, longeant des fermes et le moulin à eau à noria du Pozo de los Frailes, ensemble ethnographique qui raconte le passé agricole de la région.",
        },
        ["etnografia", "familiar"],
        {
            "longitud": "2,6 km",
            "duracion": "1h 30m",
            "dificultad": "Baja",
            "trayecto": "Lineal",
            "desnivel_maximo": "43 m",
        },
    ),
    _sendero(
        "caldera-de-majada-redonda",
        "S05",
        f"{_GPX}/s05.gpx",
        36.81463,
        -2.09233,
        {
            "es": "S05 · Sendero de la Caldera de Majada Redonda",
            "en": "S05 · Majada Redonda caldera trail",
            "de": "S05 · Weg zur Caldera Majada Redonda",
            "fr": "S05 · Sentier de la caldeira de Majada Redonda",
        },
        {
            "es": "Por la rambla de la Majada Redonda hasta el principal atractivo geológico del parque: una enorme caldera volcánica de formación circular rodeada de cerros y depresiones.",
            "en": "Along the Majada Redonda ravine to the park's main geological attraction: a huge circular volcanic caldera surrounded by hills and hollows.",
            "de": "Durch die Rambla Majada Redonda zur wichtigsten geologischen Attraktion des Parks: einer riesigen kreisförmigen Vulkancaldera zwischen Hügeln und Senken.",
            "fr": "Par la rambla de la Majada Redonda jusqu'à la principale attraction géologique du parc : une immense caldeira volcanique circulaire entourée de collines et de dépressions.",
        },
        ["parque-natural", "geologia"],
        {
            "longitud": "2,8 km",
            "duracion": "1h",
            "dificultad": "Baja",
            "trayecto": "Lineal",
            "desnivel_maximo": "91 m",
        },
    ),
    _sendero(
        "escullos-el-pozo",
        "S06",
        f"{_GPX}/s06.gpx",
        36.8043,
        -2.06399,
        {
            "es": "S06 · Sendero Los Escullos – Pozo de los Frailes",
            "en": "S06 · Los Escullos – Pozo de los Frailes trail",
            "de": "S06 · Weg Los Escullos – Pozo de los Frailes",
            "fr": "S06 · Sentier Los Escullos – Pozo de los Frailes",
        },
        {
            "es": "Terreno ondulado entre cerros volcánicos con vistas al mar, antiguos cultivos de cereal y el castillo de San Felipe (1771), fortificación costera rehabilitada en 1991.",
            "en": "Rolling terrain among volcanic hills with sea views, old grain fields and San Felipe castle (1771), a coastal fortification restored in 1991.",
            "de": "Hügeliges Gelände zwischen Vulkanbergen mit Meerblick, alten Getreidefeldern und der Burg San Felipe (1771), einer 1991 restaurierten Küstenfestung.",
            "fr": "Terrain vallonné entre collines volcaniques avec vue sur la mer, anciens champs de céréales et le château de San Felipe (1771), fortification côtière réhabilitée en 1991.",
        },
        ["parque-natural", "historia"],
        {
            "longitud": "4,7 km",
            "duracion": "1h 50m",
            "dificultad": "Baja",
            "trayecto": "Lineal",
            "desnivel_maximo": "76 m",
        },
    ),
    _sendero(
        "escullos-isleta",
        "S07",
        f"{_GPX}/s07.gpx",
        36.80226,
        -2.06278,
        {
            "es": "S07 · Sendero Los Escullos – Isleta del Moro",
            "en": "S07 · Los Escullos – Isleta del Moro trail",
            "de": "S07 · Weg Los Escullos – Isleta del Moro",
            "fr": "S07 · Sentier Los Escullos – Isleta del Moro",
        },
        {
            "es": "Corto tramo costero desde la playa del Arco, junto a la gran duna fósil de origen marino repleta de fósiles, hasta el pintoresco pueblo pesquero de la Isleta del Moro.",
            "en": "A short coastal stretch from El Arco beach, past the great fossil-rich marine dune, to the picturesque fishing village of Isleta del Moro.",
            "de": "Kurzer Küstenabschnitt vom Strand El Arco, vorbei an der großen fossilreichen Meeresdüne, bis zum malerischen Fischerdorf Isleta del Moro.",
            "fr": "Court tronçon côtier depuis la plage de l'Arco, longeant la grande dune fossile d'origine marine riche en fossiles, jusqu'au pittoresque village de pêcheurs de l'Isleta del Moro.",
        },
        ["parque-natural", "familiar", "geologia", "playa"],
        {
            "longitud": "1,6 km",
            "duracion": "40m",
            "dificultad": "Baja",
            "trayecto": "Lineal",
            "desnivel_maximo": "19 m",
        },
    ),
    _sendero(
        "requena",
        "S08",
        f"{_GPX}/s08.gpx",
        36.82545,
        -2.0463,
        {
            "es": "S08 · Sendero de Requena",
            "en": "S08 · Requena trail",
            "de": "S08 · Wanderweg Requena",
            "fr": "S08 · Sentier de Requena",
        },
        {
            "es": "Sierras volcánicas de media altura con pendientes acusadas y barrancos; muy cerca del inicio, un oasis con palmeras, tarays y pinos que se abre a una cala de guijarros.",
            "en": "Mid-height volcanic hills with steep slopes and ravines; near the start, an oasis of palms, tamarisks and pines opens onto a pebble cove.",
            "de": "Mittelhohe Vulkanberge mit steilen Hängen und Schluchten; nahe dem Start öffnet sich eine Oase mit Palmen, Tamarisken und Kiefern zu einer Kieselbucht.",
            "fr": "Sierras volcaniques de moyenne altitude aux pentes marquées et ravins ; près du départ, une oasis de palmiers, tamaris et pins s'ouvre sur une crique de galets.",
        },
        ["parque-natural", "naturaleza"],
        {
            "longitud": "7,4 km",
            "duracion": "3h",
            "dificultad": "Media",
            "trayecto": "Lineal",
            "desnivel_maximo": "416 m",
        },
    ),
    _sendero(
        "cerro-cinto-corto",
        "S09",
        f"{_GPX}/s09.gpx",
        36.85077,
        -2.0446,
        {
            "es": "S09 · Sendero del Cerro del Cinto (corto)",
            "en": "S09 · Cerro del Cinto trail (short)",
            "de": "S09 · Weg zum Cerro del Cinto (kurz)",
            "fr": "S09 · Sentier du Cerro del Cinto (court)",
        },
        {
            "es": "Circular por el paisaje minero de Rodalquilar: formaciones volcánicas mezcladas con bocaminas, poblados mineros y las antiguas instalaciones de procesado de oro.",
            "en": "A loop through Rodalquilar's mining landscape: volcanic formations mixed with mine entrances, mining villages and the old gold-processing facilities.",
            "de": "Rundweg durch die Bergbaulandschaft von Rodalquilar: Vulkanformationen, Stollenmundlöcher, Bergarbeitersiedlungen und die alten Goldverarbeitungsanlagen.",
            "fr": "Boucle dans le paysage minier de Rodalquilar : formations volcaniques mêlées d'entrées de mines, de villages miniers et des anciennes installations de traitement de l'or.",
        },
        ["mineria", "historia", "geologia"],
        {
            "longitud": "4,4 km",
            "duracion": "1h 30m",
            "dificultad": "Baja",
            "trayecto": "Circular",
            "desnivel_maximo": "92 m",
        },
    ),
    _sendero(
        "cerro-cinto-largo",
        "S10",
        f"{_GPX}/s10.gpx",
        36.8505,
        -2.04483,
        {
            "es": "S10 · Sendero del Cerro del Cinto (largo)",
            "en": "S10 · Cerro del Cinto trail (long)",
            "de": "S10 · Weg zum Cerro del Cinto (lang)",
            "fr": "S10 · Sentier du Cerro del Cinto (long)",
        },
        {
            "es": "Gran vuelta al Cerro del Cinto por el paisaje volcánico y minero de Rodalquilar, pasando junto a la planta Denver (1956), corazón de la minería del oro hasta su cierre en 1966.",
            "en": "The long loop around Cerro del Cinto through Rodalquilar's volcanic mining landscape, past the Denver plant (1956), heart of gold mining until its closure in 1966.",
            "de": "Große Runde um den Cerro del Cinto durch die Vulkan- und Bergbaulandschaft von Rodalquilar, vorbei an der Denver-Anlage (1956), dem Herz des Goldbergbaus bis zur Schließung 1966.",
            "fr": "Grande boucle autour du Cerro del Cinto par le paysage volcanique et minier de Rodalquilar, longeant l'usine Denver (1956), cœur de l'exploitation aurifère jusqu'à sa fermeture en 1966.",
        },
        ["mineria", "historia", "geologia"],
        {
            "longitud": "10 km",
            "duracion": "4h",
            "dificultad": "Media",
            "trayecto": "Circular",
            "desnivel_maximo": "235 m",
        },
    ),
    _sendero(
        "cortijo-fraile-montano-hornillo",
        "S11",
        f"{_GPX}/s11.gpx",
        36.86626,
        -2.07467,
        {
            "es": "S11 · Sendero Cortijo del Fraile – Montano – Hornillo",
            "en": "S11 · Cortijo del Fraile – Montano – Hornillo trail",
            "de": "S11 · Weg Cortijo del Fraile – Montano – Hornillo",
            "fr": "S11 · Sentier Cortijo del Fraile – Montano – Hornillo",
        },
        {
            "es": "Circular por el entorno estepario del Cortijo del Fraile, escenario de las «Bodas de sangre» de Lorca, entre llanuras agrícolas, bancales y cortijadas tradicionales.",
            "en": "A loop through the steppe around Cortijo del Fraile, setting of Lorca's 'Blood Wedding', among farmland plains, terraces and traditional farmsteads.",
            "de": "Rundweg durch die Steppe um den Cortijo del Fraile, Schauplatz von Lorcas «Bluthochzeit», zwischen Feldern, Terrassen und traditionellen Gehöften.",
            "fr": "Boucle dans la steppe autour du Cortijo del Fraile, décor des « Noces de sang » de Lorca, entre plaines agricoles, terrasses et fermes traditionnelles.",
        },
        ["historia", "cine", "literatura"],
        {
            "longitud": "7,7 km",
            "duracion": "3h",
            "dificultad": "Baja",
            "trayecto": "Circular",
            "desnivel_maximo": "64 m",
        },
    ),
    _sendero(
        "la-molata",
        "S12",
        f"{_GPX}/s12.gpx",
        36.86332,
        -2.00346,
        {
            "es": "S12 · Sendero de La Molata",
            "en": "S12 · La Molata trail",
            "de": "S12 · Wanderweg La Molata",
            "fr": "S12 · Sentier de La Molata",
        },
        {
            "es": "Costa abrupta con acantilados y panorámicas únicas de la ensenada de El Playazo, junto al castillo de San Ramón (1510), levantado para defender las minas de alumbre.",
            "en": "Rugged coast with cliffs and unique views over El Playazo cove, next to San Ramón castle (1510), built to defend the alum mines.",
            "de": "Schroffe Küste mit Klippen und einzigartigem Blick auf die Bucht El Playazo, neben der Burg San Ramón (1510), die zum Schutz der Alaunminen errichtet wurde.",
            "fr": "Côte escarpée avec falaises et panoramas uniques sur l'anse d'El Playazo, près du château de San Ramón (1510), bâti pour défendre les mines d'alun.",
        },
        ["parque-natural", "historia", "panoramica", "playa"],
        {
            "longitud": "1,5 km",
            "duracion": "1h",
            "dificultad": "Media",
            "trayecto": "Lineal",
            "desnivel_maximo": "64 m",
        },
    ),
    _sendero(
        "san-pedro-el-plomo-agua-amarga",
        "S13",
        f"{_GPX}/s13.gpx",
        36.87927,
        -2.00733,
        {
            "es": "S13 · Sendero San Pedro – El Plomo – Agua Amarga",
            "en": "S13 · San Pedro – El Plomo – Agua Amarga trail",
            "de": "S13 · Weg San Pedro – El Plomo – Agua Amarga",
            "fr": "S13 · Sentier San Pedro – El Plomo – Agua Amarga",
        },
        {
            "es": "Gran travesía costera de origen volcánico entre Las Negras y Agua Amarga: acantilados, calas como la de San Pedro con su castillo, y conos y columnatas de lava durante todo el camino.",
            "en": "A long volcanic coastal traverse between Las Negras and Agua Amarga: cliffs, coves such as San Pedro with its castle, and lava cones and columns all along the way.",
            "de": "Große vulkanische Küstenwanderung zwischen Las Negras und Agua Amarga: Klippen, Buchten wie San Pedro mit seiner Burg sowie Lavakegel und -säulen entlang des ganzen Weges.",
            "fr": "Grande traversée côtière volcanique entre Las Negras et Agua Amarga : falaises, criques comme celle de San Pedro avec son château, et cônes et colonnades de lave tout au long du chemin.",
        },
        ["parque-natural", "panoramica", "playa"],
        {
            "longitud": "11,1 km",
            "duracion": "4h 30m",
            "dificultad": "Media-Alta",
            "trayecto": "Lineal",
            "desnivel_maximo": "249 m",
        },
    ),
    _sendero(
        "via-verde-lucainena-agua-amarga",
        "S14",
        f"{_GPX}/s14.gpx",
        36.94477,
        -1.92586,
        {
            "es": "S14 · Vía Verde de Lucainena a Agua Amarga",
            "en": "S14 · Lucainena to Agua Amarga greenway",
            "de": "S14 · Grüner Weg von Lucainena nach Agua Amarga",
            "fr": "S14 · Voie verte de Lucainena à Agua Amarga",
        },
        {
            "es": "Antiguo trazado ferroviario minero convertido en vía verde: estepas, ramblas y cortijadas hasta el cargadero donde el hierro de Lucainena embarcaba en Agua Amarga. Parte del programa estatal de Caminos Naturales y Vías Verdes.",
            "en": "A former mining railway turned greenway: steppes, ravines and farmsteads down to the loading dock where Lucainena's iron ore was shipped from Agua Amarga. Part of Spain's Natural Trails and Greenways programme.",
            "de": "Ehemalige Bergbaubahn, heute grüner Weg: Steppen, Ramblas und Gehöfte bis zur Verladestation, wo das Eisen aus Lucainena in Agua Amarga verschifft wurde. Teil des staatlichen Programms der Naturwege und Vías Verdes.",
            "fr": "Ancien tracé ferroviaire minier devenu voie verte : steppes, ravins et fermes jusqu'au quai où le fer de Lucainena embarquait à Agua Amarga. Intégrée au programme national des Chemins Naturels et Voies Vertes.",
        },
        ["via-verde", "ciclismo", "mineria", "historia", "familiar"],
        {
            "longitud": "8,2 km",
            "duracion": "2h 40m",
            "dificultad": "Baja",
            "trayecto": "Circular",
            "desnivel_maximo": "108 m",
        },
    ),
    _sendero(
        "molinos-huebro",
        "S15",
        f"{_GPX}/s15.gpx",
        36.96618,
        -2.20784,
        {
            "es": "S15 · Sendero de los Molinos – Huebro (GR-140)",
            "en": "S15 · Los Molinos – Huebro trail (GR-140)",
            "de": "S15 · Mühlenweg – Huebro (GR-140)",
            "fr": "S15 · Sentier des Moulins – Huebro (GR-140)",
        },
        {
            "es": "Desde Níjar por un barranco de vegetación exuberante, entre huertas, balates y molinos de agua, hasta la aldea de Huebro y las huellas de su alcazaba nazarí del siglo XIV.",
            "en": "From Níjar up a lush ravine, among orchards, stone terraces and water mills, to the hamlet of Huebro and the remains of its 14th-century Nasrid citadel.",
            "de": "Von Níjar durch eine üppig bewachsene Schlucht, zwischen Gärten, Trockenmauern und Wassermühlen, bis zum Weiler Huebro und den Spuren seiner nasridischen Alcazaba aus dem 14. Jahrhundert.",
            "fr": "Depuis Níjar par un ravin à la végétation luxuriante, entre potagers, terrasses et moulins à eau, jusqu'au hameau de Huebro et les vestiges de son alcazaba nasride du XIVe siècle.",
        },
        ["historia", "etnografia", "naturaleza"],
        {
            "longitud": "2,55 km",
            "duracion": "1h 30m",
            "dificultad": "Media",
            "trayecto": "Lineal",
            "desnivel_maximo": "263 m",
        },
    ),
    _sendero(
        "albaricoques-coertijo-del-fraile-rodalquilar",
        "S16",
        f"{_GPX}/s16.gpx",
        36.84912,
        -2.04305,
        {
            "es": "S16 · Circuito Los Albaricoques – Cortijo del Fraile – Rodalquilar",
            "en": "S16 · Los Albaricoques – Cortijo del Fraile – Rodalquilar circuit",
            "de": "S16 · Rundkurs Los Albaricoques – Cortijo del Fraile – Rodalquilar",
            "fr": "S16 · Circuit Los Albaricoques – Cortijo del Fraile – Rodalquilar",
        },
        {
            "es": "Circuito ciclopeatonal del Plan de Sostenibilidad Turística que conecta tres enclaves emblemáticos: Los Albaricoques y sus escenarios de cine, el Cortijo del Fraile y el valle minero de Rodalquilar.",
            "en": "A cycling-and-walking circuit from the Tourism Sustainability Plan linking three emblematic sites: Los Albaricoques and its film locations, Cortijo del Fraile and the Rodalquilar mining valley.",
            "de": "Rad- und Fußgängerrundkurs aus dem Plan für nachhaltigen Tourismus, der drei symbolträchtige Orte verbindet: Los Albaricoques mit seinen Filmkulissen, den Cortijo del Fraile und das Bergbautal von Rodalquilar.",
            "fr": "Circuit cyclo-piéton du Plan de Durabilité Touristique reliant trois sites emblématiques : Los Albaricoques et ses décors de cinéma, le Cortijo del Fraile et la vallée minière de Rodalquilar.",
        },
        ["ciclismo", "cine", "mineria", "historia"],
    ),
    _sendero(
        "camino-de-santiago-argar-sureste",
        "CSAS",
        None,
        36.9660,
        -2.2076,
        {
            "es": "Camino de Santiago · Argar Sureste",
            "en": "Way of St James · Argar Southeast route",
            "de": "Jakobsweg · Route Argar Südost",
            "fr": "Chemin de Saint-Jacques · Route Argar Sud-Est",
        },
        {
            "es": "Ruta de peregrinación del Camino de Santiago a su paso por Níjar, que el Ayuntamiento mantiene y señaliza como itinerario que combina espiritualidad, patrimonio cultural y paisaje.",
            "en": "The Way of St James pilgrimage route through Níjar, maintained and signposted by the town council as an itinerary combining spirituality, cultural heritage and landscape.",
            "de": "Pilgerroute des Jakobswegs durch Níjar, die die Gemeinde als Weg zwischen Spiritualität, Kulturerbe und Landschaft pflegt und ausschildert.",
            "fr": "Itinéraire de pèlerinage du Chemin de Saint-Jacques à son passage par Níjar, entretenu et balisé par la municipalité comme parcours mêlant spiritualité, patrimoine culturel et paysage.",
        },
        ["peregrinacion", "historia", "cultura"],
    ),
]

# Recursos sembrados antiguamente cuyo contenido queda sustituido por la ficha
# oficial equivalente de turismonijar.es: se despublican (no se borran) para
# que el tótem no muestre el mismo sendero dos veces.
RECURSOS_SUSTITUIDOS: list[str] = [
    # Versión breve antigua del sendero de Vela Blanca → sustituida por S01
    "urn:ngsi-ld:RecursoTuristico:nijar:ruta-vela-blanca",
]
