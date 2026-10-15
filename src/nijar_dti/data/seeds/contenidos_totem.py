"""Contenidos del tótem: Cabo de Gata, cerámica y jarapas, y gastronomía.

Las secciones «Cabo de Gata» y «Cerámica y jarapas» de la portada del tótem no
tenían fichas propias. Estos recursos describen los lugares y oficios más
representativos del municipio con textos propios en los cuatro idiomas del
tótem (es, en, de, fr).

Las coordenadas son aproximadas (precisión de decenas de metros) y sirven para
el mapa y la distancia desde el tótem. Las fotos no se fijan aquí: las añade el
importador de contenidos abiertos (``workers/contenidos_abiertos.py``) desde
Wikipedia/Wikimedia Commons, con su crédito de autoría y licencia.

Los negocios (restaurantes, bares, alfarerías y talleres de jarapas) no se
escriben a mano: los importa ese mismo worker desde OpenStreetMap.
"""

from __future__ import annotations

_URN = "urn:ngsi-ld:RecursoTuristico:nijar:"


def _r(
    slug: str,
    categoria: str,
    lat: float,
    lon: float,
    nombre: dict[str, str],
    desc: dict[str, str],
    etiquetas: list[str],
) -> dict:
    return {
        "urn": _URN + slug,
        "nombre": nombre["es"],
        "categoria": categoria,
        "descripcion_corta": desc["es"],
        "nombre_i18n": nombre,
        "descripcion_i18n": desc,
        "lat": lat,
        "lon": lon,
        "etiquetas": etiquetas,
        "publicado": True,
    }


# ---------------- Cabo de Gata (categoría parque_natural) ----------------
# Las etiquetas «volcánico», «geología» y «patrimonio» alimentan los sub-chips
# de la sección en el tótem.
CABO_DE_GATA: list[dict] = [
    _r(
        "parque-natural-cabo-de-gata",
        "parque_natural",
        36.7900,
        -2.0950,
        {
            "es": "Parque Natural Cabo de Gata-Níjar",
            "en": "Cabo de Gata-Níjar Natural Park",
            "de": "Naturpark Cabo de Gata-Níjar",
            "fr": "Parc naturel de Cabo de Gata-Níjar",
        },
        {
            "es": "Primer espacio protegido marítimo-terrestre de Andalucía (1987), Reserva de la "
            "Biosfera y Geoparque de la UNESCO. Un paisaje volcánico único en Europa, con calas "
            "vírgenes, fondos marinos de posidonia y el clima más árido del continente.",
            "en": "Andalusia's first protected land-and-sea area (1987), a UNESCO Biosphere Reserve "
            "and Geopark. A volcanic landscape unique in Europe, with unspoilt coves, posidonia "
            "seabeds and the driest climate on the continent.",
            "de": "Erstes Land- und Meeresschutzgebiet Andalusiens (1987), UNESCO-Biosphärenreservat "
            "und Geopark. Eine in Europa einzigartige Vulkanlandschaft mit unberührten Buchten, "
            "Posidonia-Seegraswiesen und dem trockensten Klima des Kontinents.",
            "fr": "Premier espace protégé terrestre et marin d'Andalousie (1987), Réserve de "
            "biosphère et Géoparc de l'UNESCO. Un paysage volcanique unique en Europe, avec des "
            "criques préservées, des herbiers de posidonie et le climat le plus aride du continent.",
        },
        ["parque-natural", "volcánico", "geología"],
    ),
    _r(
        "castillo-san-felipe-escullos",
        "parque_natural",
        36.8017,
        -2.0651,
        {
            "es": "Castillo de San Felipe (Los Escullos)",
            "en": "San Felipe Castle (Los Escullos)",
            "de": "Burg San Felipe (Los Escullos)",
            "fr": "Château de San Felipe (Los Escullos)",
        },
        {
            "es": "Fortaleza costera del siglo XVIII levantada sobre la roca volcánica para "
            "defender la costa de los ataques berberiscos. Domina la playa de El Arco y la duna "
            "fósil de Los Escullos.",
            "en": "18th-century coastal fortress built on volcanic rock to defend the shore from "
            "Barbary pirates. It overlooks El Arco beach and the Los Escullos fossil dune.",
            "de": "Küstenfestung aus dem 18. Jahrhundert auf Vulkangestein, errichtet zum Schutz "
            "vor Berberpiraten. Sie überblickt den Strand El Arco und die fossile Düne von Los "
            "Escullos.",
            "fr": "Forteresse côtière du XVIIIe siècle bâtie sur la roche volcanique pour défendre "
            "le littoral des pirates barbaresques. Elle domine la plage d'El Arco et la dune "
            "fossile de Los Escullos.",
        },
        ["patrimonio", "parque-natural", "fotografia"],
    ),
    _r(
        "duna-fosil-escullos",
        "parque_natural",
        36.8005,
        -2.0640,
        {
            "es": "Duna fósil de Los Escullos",
            "en": "Los Escullos fossil dune",
            "de": "Fossile Düne von Los Escullos",
            "fr": "Dune fossile de Los Escullos",
        },
        {
            "es": "Antigua duna de arena petrificada por el paso del tiempo, modelada por el viento "
            "y el mar en formas caprichosas. Uno de los paisajes geológicos más fotografiados del "
            "parque.",
            "en": "An ancient sand dune turned to stone over time and sculpted by wind and sea into "
            "striking shapes. One of the park's most photographed geological sights.",
            "de": "Eine im Laufe der Zeit versteinerte Sanddüne, von Wind und Meer zu bizarren "
            "Formen geschliffen. Eines der meistfotografierten geologischen Motive des Parks.",
            "fr": "Ancienne dune de sable pétrifiée avec le temps et sculptée par le vent et la mer "
            "en formes étonnantes. L'un des paysages géologiques les plus photographiés du parc.",
        },
        ["geología", "parque-natural", "fotografia"],
    ),
    _r(
        "cerro-de-los-frailes",
        "parque_natural",
        36.8175,
        -2.0870,
        {
            "es": "Cerro de los Frailes",
            "en": "Los Frailes hills",
            "de": "Cerro de los Frailes",
            "fr": "Cerro de los Frailes",
        },
        {
            "es": "Las dos cumbres volcánicas que dan nombre al paraje son las más altas del parque. "
            "Su silueta gemela es visible desde casi toda la costa y su ascenso ofrece vistas de "
            "todo el Cabo de Gata.",
            "en": "The twin volcanic peaks that name the area are the highest in the park. Their "
            "silhouette can be seen from most of the coast, and the climb rewards you with views "
            "over the whole of Cabo de Gata.",
            "de": "Die beiden Vulkangipfel, die der Gegend ihren Namen geben, sind die höchsten des "
            "Parks. Ihre Silhouette ist von fast der ganzen Küste aus sichtbar; der Aufstieg bietet "
            "Ausblicke über ganz Cabo de Gata.",
            "fr": "Les deux sommets volcaniques qui donnent leur nom au site sont les plus hauts du "
            "parc. Leur silhouette jumelle se voit de presque toute la côte et l'ascension offre une "
            "vue sur tout le Cabo de Gata.",
        },
        ["volcánico", "geología", "senderismo"],
    ),
    _r(
        "cerro-negro-las-negras",
        "parque_natural",
        36.8760,
        -2.0010,
        {
            "es": "Cerro Negro (Las Negras)",
            "en": "Cerro Negro (Las Negras)",
            "de": "Cerro Negro (Las Negras)",
            "fr": "Cerro Negro (Las Negras)",
        },
        {
            "es": "Domo volcánico de roca oscura que cierra la playa de Las Negras y da nombre al "
            "pueblo. Desde aquí parte el camino a pie hacia la cala de San Pedro.",
            "en": "A dark volcanic dome that closes off Las Negras beach and gives the village its "
            "name. The footpath to San Pedro cove starts here.",
            "de": "Dunkler Vulkandom, der den Strand von Las Negras abschließt und dem Dorf seinen "
            "Namen gibt. Von hier führt der Fußweg zur Bucht von San Pedro.",
            "fr": "Dôme volcanique de roche sombre qui ferme la plage de Las Negras et donne son nom "
            "au village. C'est d'ici que part le sentier vers la crique de San Pedro.",
        },
        ["volcánico", "geología", "pueblo"],
    ),
    _r(
        "torre-vela-blanca",
        "parque_natural",
        36.7213,
        -2.1622,
        {
            "es": "Torre de Vela Blanca",
            "en": "Vela Blanca Tower",
            "de": "Turm von Vela Blanca",
            "fr": "Tour de Vela Blanca",
        },
        {
            "es": "Torre vigía del siglo XVIII asomada a un alto acantilado sobre el mar. "
            "Es el final de la pista desde el faro y uno de los mejores miradores de las playas de "
            "Mónsul y Genoveses.",
            "en": "18th-century watchtower perched on a high cliff above the sea. It marks "
            "the end of the track from the lighthouse and is one of the best viewpoints over Mónsul "
            "and Genoveses beaches.",
            "de": "Wachturm aus dem 18. Jahrhundert auf einer hohen Klippe über dem Meer. "
            "Endpunkt der Piste vom Leuchtturm und einer der besten Aussichtspunkte auf die Strände "
            "Mónsul und Genoveses.",
            "fr": "Tour de guet du XVIIIe siècle perchée sur une haute falaise au-dessus de la "
            "mer. Elle marque la fin de la piste depuis le phare et offre l'un des "
            "meilleurs points de vue sur les plages de Mónsul et Genoveses.",
        },
        ["patrimonio", "mirador", "panoramica"],
    ),
    _r(
        "molino-de-los-genoveses",
        "parque_natural",
        36.7505,
        -2.1135,
        {
            "es": "Molino de los Genoveses",
            "en": "Los Genoveses windmill",
            "de": "Windmühle von Los Genoveses",
            "fr": "Moulin de Los Genoveses",
        },
        {
            "es": "Antiguo molino de viento harinero sobre la ensenada de los Genoveses, testigo del "
            "pasado agrícola de la zona. Una de las estampas más reconocibles del parque.",
            "en": "Old flour windmill overlooking Los Genoveses bay, a reminder of the area's "
            "farming past and one of the park's most recognisable sights.",
            "de": "Alte Getreidewindmühle über der Bucht von Los Genoveses, Zeugnis der "
            "landwirtschaftlichen Vergangenheit und eines der bekanntesten Motive des Parks.",
            "fr": "Ancien moulin à vent à farine dominant l'anse de Los Genoveses, témoin du passé "
            "agricole de la région et l'une des images les plus reconnaissables du parc.",
        },
        ["patrimonio", "fotografia"],
    ),
    _r(
        "cortijo-del-fraile",
        "parque_natural",
        36.8800,
        -2.1100,
        {
            "es": "Cortijo del Fraile",
            "en": "Cortijo del Fraile",
            "de": "Cortijo del Fraile",
            "fr": "Cortijo del Fraile",
        },
        {
            "es": "Cortijo del siglo XVIII donde ocurrió en 1928 el crimen que inspiró a Federico "
            "García Lorca «Bodas de sangre». También fue escenario de westerns. Hoy en ruinas, se "
            "contempla desde el exterior.",
            "en": "18th-century farmstead where the 1928 crime that inspired Federico García "
            "Lorca's «Blood Wedding» took place. It was also a western film set. Now in ruins, it "
            "can be viewed from outside.",
            "de": "Gutshof aus dem 18. Jahrhundert, Schauplatz des Verbrechens von 1928, das "
            "Federico García Lorca zu «Bluthochzeit» inspirierte, und Drehort von Western. Heute "
            "eine Ruine, nur von außen zu besichtigen.",
            "fr": "Ferme du XVIIIe siècle où eut lieu en 1928 le crime qui inspira à Federico "
            "García Lorca «Noces de sang». Elle servit aussi de décor de westerns. Aujourd'hui en "
            "ruines, elle se visite de l'extérieur.",
        },
        ["patrimonio", "cine"],
    ),
    _r(
        "casa-de-los-volcanes-rodalquilar",
        "parque_natural",
        36.8500,
        -2.0470,
        {
            "es": "Casa de los Volcanes (Rodalquilar)",
            "en": "House of Volcanoes (Rodalquilar)",
            "de": "Haus der Vulkane (Rodalquilar)",
            "fr": "Maison des Volcans (Rodalquilar)",
        },
        {
            "es": "Centro de interpretación geológica junto a las antiguas minas de oro de "
            "Rodalquilar. Explica el origen volcánico del Cabo de Gata y la historia minera del "
            "valle, que se asienta sobre una antigua caldera.",
            "en": "Geology interpretation centre next to the old Rodalquilar gold mines. It explains "
            "the volcanic origin of Cabo de Gata and the mining history of the valley, which sits in "
            "an ancient caldera.",
            "de": "Geologisches Informationszentrum neben den alten Goldminen von Rodalquilar. Es "
            "erklärt den vulkanischen Ursprung von Cabo de Gata und die Bergbaugeschichte des Tals, "
            "das in einer alten Caldera liegt.",
            "fr": "Centre d'interprétation géologique près des anciennes mines d'or de Rodalquilar. "
            "Il explique l'origine volcanique du Cabo de Gata et l'histoire minière de la vallée, "
            "nichée dans une ancienne caldeira.",
        },
        ["geología", "volcánico", "patrimonio"],
    ),
    _r(
        "jardin-botanico-el-albardinal",
        "parque_natural",
        36.8455,
        -2.0395,
        {
            "es": "Jardín Botánico El Albardinal (Rodalquilar)",
            "en": "El Albardinal Botanical Garden (Rodalquilar)",
            "de": "Botanischer Garten El Albardinal (Rodalquilar)",
            "fr": "Jardin botanique El Albardinal (Rodalquilar)",
        },
        {
            "es": "Jardín botánico dedicado a la flora del sureste árido: palmito, cornical, "
            "azufaifo y plantas endémicas del parque, con un huerto tradicional y paneles "
            "explicativos.",
            "en": "Botanical garden devoted to the plants of the arid south-east: dwarf fan palm, "
            "jujube and the park's endemic species, with a traditional vegetable garden and "
            "information panels.",
            "de": "Botanischer Garten mit der Flora des trockenen Südostens: Zwergpalme, Jujube und "
            "endemische Arten des Parks, dazu ein traditioneller Gemüsegarten und Infotafeln.",
            "fr": "Jardin botanique consacré à la flore du sud-est aride : palmier nain, jujubier et "
            "espèces endémiques du parc, avec un potager traditionnel et des panneaux explicatifs.",
        },
        ["naturaleza", "parque-natural"],
    ),
]

# ---------------- Cerámica y jarapas (categoría punto_interes) ----------------
CERAMICA_Y_JARAPAS: list[dict] = [
    _r(
        "barrio-alfarero-nijar",
        "punto_interes",
        36.9655,
        -2.2050,
        {
            "es": "Barrio Alfarero de Níjar",
            "en": "Níjar Potters' Quarter",
            "de": "Töpferviertel von Níjar",
            "fr": "Quartier des potiers de Níjar",
        },
        {
            "es": "La alfarería de Níjar se trabaja a torno y se decora con óxidos metálicos en "
            "verdes, azules y melados. En el barrio alfarero varios talleres abren sus puertas para "
            "ver el proceso y comprar piezas directamente al artesano.",
            "en": "Níjar pottery is thrown on the wheel and decorated with metal oxides in greens, "
            "blues and honey tones. In the potters' quarter several workshops open their doors so "
            "you can watch the process and buy straight from the potter.",
            "de": "Die Keramik von Níjar wird auf der Scheibe gedreht und mit Metalloxiden in Grün, "
            "Blau und Honigtönen bemalt. Im Töpferviertel öffnen mehrere Werkstätten ihre Türen: "
            "Man kann zusehen und direkt beim Handwerker kaufen.",
            "fr": "La poterie de Níjar est tournée et décorée d'oxydes métalliques aux tons verts, "
            "bleus et miel. Dans le quartier des potiers, plusieurs ateliers ouvrent leurs portes "
            "pour voir le travail et acheter directement à l'artisan.",
        },
        ["ceramica", "artesania", "patrimonio"],
    ),
    _r(
        "jarapas-de-nijar",
        "punto_interes",
        36.9668,
        -2.2068,
        {
            "es": "Jarapas de Níjar",
            "en": "Níjar jarapa rugs",
            "de": "Jarapa-Teppiche aus Níjar",
            "fr": "Jarapas de Níjar",
        },
        {
            "es": "Alfombras y mantas tejidas a mano en telares de madera con tiras de tela "
            "reciclada. Cada jarapa combina sus colores de forma única. En las tiendas y talleres "
            "del casco histórico aún se teje a la vista del visitante.",
            "en": "Rugs and throws hand-woven on wooden looms from strips of recycled fabric, each "
            "with its own mix of colours. In the shops and workshops of the old town they are "
            "still woven in front of visitors.",
            "de": "Teppiche und Decken, von Hand auf Holzwebstühlen aus Stoffresten gewebt – jede "
            "mit ihrer eigenen Farbmischung. In den Läden und Werkstätten der Altstadt wird noch "
            "vor den Augen der Besucher gewebt.",
            "fr": "Tapis et couvertures tissés à la main sur des métiers en bois avec des bandes de "
            "tissu recyclé, chacun avec son propre mélange de couleurs. Dans les boutiques et "
            "ateliers du centre historique, on tisse encore sous les yeux des visiteurs.",
        },
        ["jarapas", "artesania", "patrimonio"],
    ),
]

CONTENIDOS_TOTEM_SEED: list[dict] = CABO_DE_GATA + CERAMICA_Y_JARAPAS
