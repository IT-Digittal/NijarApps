/**
 * Datos demo del tótem — se muestran cuando el backend no responde
 * (demos sin Docker) o cuando una categoría devuelve vacío.
 * Cubren los 4 idiomas del contrato y los recursos más
 * representativos del Parque Natural Cabo de Gata-Níjar.
 *
 * Cada item incluye todos los campos que el modal sabe pintar:
 *   nombre / nombre_i18n
 *   descripcion / descripcion_i18n
 *   categoria  (rutea las clases del badge)
 *   direccion, latitud, longitud
 *   Rutas:     distancia_km, duracion_min, desnivel_m, dificultad, modalidad, temporada, recomendaciones
 *   Playas:    longitud_m, tipo_arena, bandera_azul, servicios, accesibilidad, recomendaciones
 *   Patrimonio: epoca, estilo, bic, horario, precio
 *   Servicios: telefono, horario, idiomas, web
 *   Eventos:   fecha_inicio, precio, organizador, aforo
 */

const T = (es, en, de, fr) => ({ es, en, de, fr });

export const DEMO_RESOURCES = {
  rutas: [
    {
      id: "demo-r-genoveses",
      nombre: "Sendero de los Genoveses",
      nombre_i18n: T(
        "Sendero de los Genoveses",
        "Genoveses Trail",
        "Genoveses-Wanderweg",
        "Sentier de Los Genoveses",
      ),
      descripcion_corta: "Ruta circular de 7 km por dunas, calas y atalayas con vistas al mar.",
      descripcion_i18n: T(
        "Recorrido circular muy popular que conecta la playa de los Genoveses con miradores y antiguas torres vigía. Pasa por dunas fósiles, palmitos y restos de la antigua almazara.",
        "Popular circular route linking Genoveses Beach with viewpoints and old watchtowers. Passes fossil dunes, dwarf palms and the ruins of an old oil mill.",
        "Beliebte Rundwanderung, die den Strand Los Genoveses mit Aussichtspunkten und alten Wachtürmen verbindet. Vorbei an fossilen Dünen, Zwergpalmen und Ruinen einer Ölmühle.",
        "Itinéraire circulaire reliant la plage de Los Genoveses à des points de vue et anciennes tours de guet. Dunes fossiles, palmiers nains et ruines d'un ancien moulin à huile.",
      ),
      categoria: "ruta",
      direccion: "Cabo de Gata · San José",
      latitud: 36.7588,
      longitud: -2.1325,
      distancia_km: 7.4,
      duracion_min: 135,
      desnivel_m: 110,
      dificultad: "media",
      modalidad: ["pie", "bici"],
      temporada: T("Todo el año (mejor en otoño-primavera)", "All year (best in autumn-spring)", "Ganzjährig (am besten Herbst-Frühling)", "Toute l'année (idéal automne-printemps)"),
      recomendaciones: T(
        "Llevar 2 L de agua, gorra y calzado cerrado. Casi sin sombra. Aparcamiento limitado en verano.",
        "Bring 2 L of water, a cap and closed shoes. Almost no shade. Limited parking in summer.",
        "2 L Wasser, Mütze und festes Schuhwerk mitbringen. Kaum Schatten. Im Sommer wenige Parkplätze.",
        "Apporter 2 L d'eau, casquette et chaussures fermées. Très peu d'ombre. Parking limité en été.",
      ),
    },
    {
      id: "demo-r-faro",
      nombre: "Sendero al Faro de Cabo de Gata",
      nombre_i18n: T(
        "Sendero al Faro de Cabo de Gata",
        "Cabo de Gata Lighthouse Trail",
        "Wanderweg zum Leuchtturm Cabo de Gata",
        "Sentier du Phare de Cabo de Gata",
      ),
      descripcion_corta: "10 km bordeando acantilados volcánicos hasta el faro y el Arrecife de las Sirenas.",
      descripcion_i18n: T(
        "Recorrido lineal que sale de San José y bordea acantilados volcánicos hasta llegar al faro de 1863 y al impresionante Arrecife de las Sirenas. Termina en la cala de Mónsul.",
        "Linear route from San José along volcanic cliffs to the 1863 lighthouse and the striking Las Sirenas reef. Ends at Mónsul cove.",
        "Linearer Weg von San José entlang vulkanischer Klippen zum Leuchtturm von 1863 und zum Sirenenriff. Endet an der Bucht Mónsul.",
        "Itinéraire linéaire depuis San José le long des falaises volcaniques jusqu'au phare de 1863 et au récif des Sirènes. Termine à la crique de Mónsul.",
      ),
      categoria: "ruta",
      direccion: "Carretera del Faro · Cabo de Gata",
      latitud: 36.7274,
      longitud: -2.1933,
      distancia_km: 10.2,
      duracion_min: 210,
      desnivel_m: 280,
      dificultad: "alta",
      modalidad: ["pie"],
      temporada: T("Otoño, invierno y primavera", "Autumn, winter and spring", "Herbst, Winter und Frühling", "Automne, hiver et printemps"),
      recomendaciones: T(
        "Tramo expuesto al viento. Empezar al amanecer para evitar calor. Volver en taxi o autobús lanzadera.",
        "Wind-exposed stretch. Start at dawn to avoid heat. Return by taxi or shuttle bus.",
        "Windexponierte Strecke. Bei Sonnenaufgang starten, um Hitze zu vermeiden. Rückweg per Taxi oder Shuttle.",
        "Tronçon exposé au vent. Démarrer à l'aube pour éviter la chaleur. Retour en taxi ou navette.",
      ),
    },
    {
      id: "demo-r-fraile",
      nombre: "Ruta del Cerro del Fraile",
      nombre_i18n: T(
        "Ruta del Cerro del Fraile",
        "Cerro del Fraile Route",
        "Cerro-del-Fraile-Route",
        "Itinéraire du Cerro del Fraile",
      ),
      descripcion_corta: "Ascensión moderada (5 km) a uno de los picos volcánicos del Parque, vistas 360°.",
      descripcion_i18n: T(
        "Ascensión circular al pico volcánico de 493 m. Pasa por el Pozo de los Frailes, antiguas norias y miradores con vistas a la bahía y al desierto de Tabernas.",
        "Circular climb to the 493 m volcanic peak. Passes Pozo de los Frailes hamlet, old water wheels and viewpoints over the bay and Tabernas desert.",
        "Rundwanderung zum 493 m hohen Vulkangipfel. Vorbei am Weiler Pozo de los Frailes, alten Schöpfrädern und Aussichtspunkten zur Bucht und Wüste Tabernas.",
        "Ascension circulaire au sommet volcanique de 493 m. Passe par Pozo de los Frailes, anciennes norias et points de vue sur la baie et le désert de Tabernas.",
      ),
      categoria: "ruta",
      direccion: "Los Escullos · Níjar",
      latitud: 36.8161,
      longitud: -2.0731,
      distancia_km: 5.6,
      duracion_min: 150,
      desnivel_m: 320,
      dificultad: "media",
      modalidad: ["pie"],
      temporada: T("Todo el año (no recomendado al mediodía en verano)", "All year (avoid summer midday)", "Ganzjährig (Sommermittag meiden)", "Toute l'année (éviter midi en été)"),
      recomendaciones: T(
        "Sendero pedregoso en la parte alta. Bastones útiles. Cuidado con los desprendimientos tras lluvia.",
        "Stony upper section. Trekking poles recommended. Watch for rockfall after rain.",
        "Steiniger Abschnitt im oberen Teil. Trekkingstöcke empfohlen. Vorsicht Steinschlag nach Regen.",
        "Tronçon supérieur rocailleux. Bâtons recommandés. Attention aux éboulements après la pluie.",
      ),
    },
    {
      id: "demo-r-sirenas",
      nombre: "Sendero de las Sirenas a La Almadraba",
      nombre_i18n: T(
        "Sendero de las Sirenas a La Almadraba",
        "Las Sirenas to La Almadraba Trail",
        "Wanderweg von Las Sirenas zur Almadraba",
        "Sentier de Las Sirenas à La Almadraba",
      ),
      descripcion_corta: "Costero de 6 km entre arrecifes y salinas históricas. Apto para todas las edades.",
      descripcion_i18n: T(
        "Paseo costero llano por la antigua carretera del faro, las salinas del Cabo de Gata —importante humedal Ramsar— y el poblado pesquero de La Almadraba de Monteleva.",
        "Flat coastal walk along the old lighthouse road, the Cabo de Gata salt flats —a Ramsar wetland— and the fishing village of La Almadraba de Monteleva.",
        "Flacher Küstenweg entlang der alten Leuchtturmstraße, Salinen Cabo de Gata (Ramsar-Gebiet) und Fischerdorf La Almadraba.",
        "Promenade côtière plate sur l'ancienne route du phare, salines de Cabo de Gata (zone Ramsar) et village de pêcheurs de La Almadraba.",
      ),
      categoria: "ruta",
      direccion: "La Almadraba de Monteleva · Cabo de Gata",
      latitud: 36.7445,
      longitud: -2.2160,
      distancia_km: 6.1,
      duracion_min: 95,
      desnivel_m: 25,
      dificultad: "baja",
      modalidad: ["pie", "bici", "silla"],
      temporada: T("Todo el año", "All year", "Ganzjährig", "Toute l'année"),
      recomendaciones: T(
        "Ideal en familia. Llevar prismáticos para observar flamencos en las salinas (mar-oct).",
        "Family-friendly. Bring binoculars to spot flamingos in the salt flats (Mar-Oct).",
        "Familienfreundlich. Fernglas mitbringen für Flamingobeobachtung (März-Okt).",
        "Idéal en famille. Apporter des jumelles pour les flamants (mars-oct).",
      ),
    },
  ],

  playas: [
    {
      id: "demo-p-monsul",
      nombre: "Playa de Mónsul",
      nombre_i18n: T("Playa de Mónsul", "Mónsul Beach", "Strand Mónsul", "Plage de Mónsul"),
      descripcion_corta: "Arena dorada y la famosa duna volcánica. Aparcamiento limitado en verano.",
      descripcion_i18n: T(
        "Cala de 350 m bordeada por farallones volcánicos y la mítica duna vegetada que sirvió de escenario a 'Indiana Jones y la última cruzada'. Aguas tranquilas, ideal para snorkel.",
        "350 m cove framed by volcanic rocks and the iconic vegetated dune featured in 'Indiana Jones and the Last Crusade'. Calm waters, great for snorkelling.",
        "350 m Bucht umrahmt von Vulkanfelsen und der berühmten bewachsenen Düne aus 'Indiana Jones und der letzte Kreuzzug'. Ruhiges Wasser, ideal zum Schnorcheln.",
        "Crique de 350 m bordée de rochers volcaniques et de la célèbre dune végétalisée d'« Indiana Jones et la dernière croisade ». Eaux calmes, idéale pour le snorkeling.",
      ),
      categoria: "playa",
      direccion: "Cabo de Gata · San José",
      latitud: 36.7479,
      longitud: -2.1846,
      longitud_m: 350,
      tipo_arena: T("Arena fina dorada", "Fine golden sand", "Feiner Goldsand", "Sable fin doré"),
      bandera_azul: false,
      servicios: T(
        ["Socorrismo en verano", "Aparcamiento", "Sin chiringuito"],
        ["Lifeguard in summer", "Parking", "No beach bar"],
        ["Rettungsschwimmer (Sommer)", "Parkplatz", "Keine Strandbar"],
        ["Sauveteur en été", "Parking", "Pas de buvette"],
      ),
      accesibilidad: T(
        "Acceso peatonal desde el aparcamiento (200 m). Sin pasarela hasta la arena.",
        "Pedestrian access from the car park (200 m). No accessible walkway to the sand.",
        "Fußweg vom Parkplatz (200 m). Kein barrierefreier Zugang zum Sand.",
        "Accès piéton depuis le parking (200 m). Pas de passerelle accessible jusqu'au sable.",
      ),
      recomendaciones: T(
        "Acceso restringido en julio y agosto: lanzadera desde San José.",
        "Restricted access in July and August: shuttle from San José.",
        "Im Juli und August Zugang nur per Shuttle ab San José.",
        "Accès régulé en juillet-août : navette depuis San José.",
      ),
    },
    {
      id: "demo-p-genoveses",
      nombre: "Playa de los Genoveses",
      nombre_i18n: T("Playa de los Genoveses", "Genoveses Beach", "Strand Genoveses", "Plage de Los Genoveses"),
      descripcion_corta: "Cala virgen de 1 km enmarcada por dunas y eucaliptos. Acceso restringido en verano.",
      descripcion_i18n: T(
        "Una de las playas más extensas y vírgenes del Parque. Sin construcciones, sin sombrillas, sin chiringuitos. Tomó su nombre del fondeo de la flota genovesa en 1147.",
        "One of the longest pristine beaches in the park. No buildings, no sun umbrellas, no bars. Named after the Genoese fleet anchored here in 1147.",
        "Einer der längsten unberührten Strände im Park. Keine Bauten, keine Sonnenschirme, keine Bars. Benannt nach der genuesischen Flotte (1147).",
        "L'une des plus longues plages vierges du parc. Aucun bâtiment, aucun parasol, aucune buvette. Nommée d'après la flotte génoise (1147).",
      ),
      categoria: "playa",
      direccion: "Cabo de Gata · San José",
      latitud: 36.7560,
      longitud: -2.1490,
      longitud_m: 1100,
      tipo_arena: T("Arena fina dorada", "Fine golden sand", "Feiner Goldsand", "Sable fin doré"),
      bandera_azul: false,
      servicios: T(
        ["Sin servicios", "Aparcamiento de tierra"],
        ["No facilities", "Dirt parking"],
        ["Keine Einrichtungen", "Erdparkplatz"],
        ["Aucun service", "Parking en terre"],
      ),
      accesibilidad: T(
        "Camino de tierra desde el aparcamiento. No apto para sillas de ruedas.",
        "Dirt path from the car park. Not wheelchair accessible.",
        "Erdweg vom Parkplatz. Nicht rollstuhlgeeignet.",
        "Chemin de terre depuis le parking. Non accessible aux fauteuils roulants.",
      ),
      recomendaciones: T(
        "Acceso regulado en verano. Lleva agua y sombrilla — no hay sombra natural.",
        "Regulated access in summer. Bring water and a parasol — no natural shade.",
        "Im Sommer Zugang geregelt. Wasser und Sonnenschirm mitbringen — kein Schatten.",
        "Accès régulé l'été. Apporter eau et parasol — pas d'ombre naturelle.",
      ),
    },
    {
      id: "demo-p-playazo",
      nombre: "Playa del Playazo",
      nombre_i18n: T("Playa del Playazo", "El Playazo Beach", "Strand El Playazo", "Plage de El Playazo"),
      descripcion_corta: "Arena fina, aguas cristalinas y el castillo de San Ramón al fondo.",
      descripcion_i18n: T(
        "Playa de 400 m con dunas vegetadas, agua transparente y el castillo de San Ramón (s. XVIII) en un extremo. Fondo rocoso ideal para snorkel.",
        "400 m beach with vegetated dunes, crystal-clear water and the 18th-century San Ramón castle at one end. Rocky seabed great for snorkelling.",
        "400 m Strand mit bewachsenen Dünen, kristallklarem Wasser und der Burg San Ramón (18. Jh.). Felsiger Meeresboden zum Schnorcheln.",
        "Plage de 400 m avec dunes végétalisées, eau cristalline et le château San Ramón (XVIIIᵉ s.). Fond rocheux idéal pour le snorkeling.",
      ),
      categoria: "playa",
      direccion: "Rodalquilar · Níjar",
      latitud: 36.8528,
      longitud: -2.0234,
      longitud_m: 400,
      tipo_arena: T("Arena fina dorada", "Fine golden sand", "Feiner Goldsand", "Sable fin doré"),
      bandera_azul: true,
      servicios: T(
        ["Socorrismo en verano", "Aparcamiento gratuito", "Chiringuito"],
        ["Lifeguard in summer", "Free parking", "Beach bar"],
        ["Rettungsschwimmer (Sommer)", "Kostenloser Parkplatz", "Strandbar"],
        ["Sauveteur en été", "Parking gratuit", "Buvette"],
      ),
      accesibilidad: T(
        "Pasarela de madera y silla anfibia disponible bajo reserva.",
        "Wooden walkway and amphibious wheelchair available on request.",
        "Holzsteg und Strandrollstuhl auf Anfrage verfügbar.",
        "Passerelle en bois et fauteuil amphibie sur demande.",
      ),
    },
    {
      id: "demo-p-negras",
      nombre: "Playa de Las Negras",
      nombre_i18n: T("Playa de Las Negras", "Las Negras Beach", "Strand Las Negras", "Plage de Las Negras"),
      descripcion_corta: "Playa de cantos rodados con vistas al cerro Negro y al pueblo pesquero.",
      descripcion_i18n: T(
        "Playa urbana de 450 m de cantos rodados frente al pintoresco pueblo de Las Negras. Aguas profundas, buena pesca submarina.",
        "450 m pebble urban beach facing the picturesque village of Las Negras. Deep waters, good for spearfishing.",
        "450 m städtischer Kieselstrand vor dem malerischen Ort Las Negras. Tiefes Wasser, gut zum Speerfischen.",
        "Plage urbaine de galets de 450 m face au pittoresque village de Las Negras. Eaux profondes, bonne pêche sous-marine.",
      ),
      categoria: "playa",
      direccion: "Las Negras · Níjar",
      latitud: 36.8755,
      longitud: -2.0036,
      longitud_m: 450,
      tipo_arena: T("Canto rodado oscuro", "Dark pebbles", "Dunkler Kies", "Galets sombres"),
      bandera_azul: false,
      servicios: T(
        ["Socorrismo en verano", "Restaurantes", "Aparcamiento del pueblo"],
        ["Lifeguard in summer", "Restaurants", "Village parking"],
        ["Rettungsschwimmer (Sommer)", "Restaurants", "Dorfparkplatz"],
        ["Sauveteur en été", "Restaurants", "Parking du village"],
      ),
      accesibilidad: T(
        "Paseo marítimo accesible. Acceso al agua dificultado por los cantos.",
        "Accessible promenade. Pebbles make water access difficult.",
        "Barrierefreie Promenade. Steiniger Wasserzugang erschwert.",
        "Promenade accessible. Accès à l'eau difficile à cause des galets.",
      ),
    },
    {
      id: "demo-p-san-pedro",
      nombre: "Cala de San Pedro",
      nombre_i18n: T("Cala de San Pedro", "San Pedro Cove", "Bucht San Pedro", "Crique de San Pedro"),
      descripcion_corta: "Cala remota accesible solo a pie o en barco. Aljibes y ruinas del antiguo poblado.",
      descripcion_i18n: T(
        "Cala de 150 m de arena dorada, accesible solo por sendero (1 h desde Las Negras) o en kayak. Antiguo poblado morisco con manantial y palmeral.",
        "150 m golden-sand cove reachable only by trail (1 h from Las Negras) or by kayak. Old Moorish hamlet with spring and palm grove.",
        "150 m goldener Sandstrand, nur zu Fuß (1 h ab Las Negras) oder per Kajak erreichbar. Alter maurischer Weiler mit Quelle und Palmenhain.",
        "Crique de 150 m de sable doré, accessible uniquement à pied (1 h depuis Las Negras) ou en kayak. Ancien hameau mauresque avec source et palmeraie.",
      ),
      categoria: "playa",
      direccion: "Sendero La Caleta · Las Negras",
      latitud: 36.8941,
      longitud: -1.9778,
      longitud_m: 150,
      tipo_arena: T("Arena fina dorada", "Fine golden sand", "Feiner Goldsand", "Sable fin doré"),
      bandera_azul: false,
      servicios: T(
        ["Sin servicios", "Manantial de agua dulce"],
        ["No facilities", "Freshwater spring"],
        ["Keine Einrichtungen", "Süßwasserquelle"],
        ["Aucun service", "Source d'eau douce"],
      ),
      accesibilidad: T(
        "Solo accesible a pie o en barco. No apto para sillas de ruedas.",
        "Only reachable on foot or by boat. Not wheelchair accessible.",
        "Nur zu Fuß oder per Boot. Nicht rollstuhlgeeignet.",
        "Accessible uniquement à pied ou en bateau. Non adapté aux fauteuils.",
      ),
    },
  ],

  patrimonio: [
    {
      id: "demo-h-faro",
      nombre: "Faro de Cabo de Gata",
      nombre_i18n: T("Faro de Cabo de Gata", "Cabo de Gata Lighthouse", "Leuchtturm Cabo de Gata", "Phare de Cabo de Gata"),
      descripcion_corta: "Faro de 1863 sobre el antiguo castillo de San Francisco de Paula, mirador del Arrecife de las Sirenas.",
      descripcion_i18n: T(
        "Construido en 1863 sobre las ruinas del castillo de San Francisco de Paula. Su luz alcanza 30 millas náuticas. Mirador con vistas al Arrecife de las Sirenas y a la costa marroquí en días claros.",
        "Built in 1863 on the ruins of San Francisco de Paula castle. Its light reaches 30 nautical miles. Viewpoint overlooking Las Sirenas reef and the Moroccan coast on clear days.",
        "1863 auf den Ruinen der Burg San Francisco de Paula erbaut. Reichweite 30 Seemeilen. Aussichtspunkt zum Sirenenriff und zur marokkanischen Küste.",
        "Construit en 1863 sur les ruines du château San Francisco de Paula. Sa lumière porte à 30 milles. Vue sur le récif des Sirènes et la côte marocaine.",
      ),
      categoria: "monumento",
      direccion: "Punta del Faro · Cabo de Gata",
      latitud: 36.7269,
      longitud: -2.1934,
      epoca: T("Siglo XIX (1863)", "19th century (1863)", "19. Jh. (1863)", "XIXᵉ s. (1863)"),
      estilo: T("Faro marítimo", "Maritime lighthouse", "Seezeichen", "Phare maritime"),
      bic: false,
      horario: T(
        "Mirador exterior 24/7 · Interior cerrado al público",
        "Outdoor viewpoint 24/7 · Interior closed to the public",
        "Aussichtspunkt 24/7 · Innenraum geschlossen",
        "Belvédère extérieur 24/7 · Intérieur fermé au public",
      ),
      precio: T("Gratuito", "Free", "Kostenlos", "Gratuit"),
    },
    {
      id: "demo-h-escullos",
      nombre: "Castillo de San Felipe",
      nombre_i18n: T("Castillo de San Felipe", "San Felipe Castle", "Burg San Felipe", "Château de San Felipe"),
      descripcion_corta: "Fortaleza de planta estrellada del s. XVIII en Los Escullos. Sala de exposiciones.",
      descripcion_i18n: T(
        "Construido en 1771 dentro del plan de defensa costera de Carlos III. Planta hexagonal estrellada, parte de una red de torres y baterías costeras. Sala de exposiciones permanente sobre patrimonio defensivo.",
        "Built in 1771 as part of Charles III's coastal defence plan. Star-shaped hexagonal layout, part of a chain of coastal towers and batteries. Permanent exhibition on coastal defence heritage.",
        "1771 als Teil des Küstenverteidigungsplans von Karl III. erbaut. Sternförmiger Sechseck-Grundriss, Teil einer Kette von Türmen und Batterien. Dauerausstellung zum Wehrerbe.",
        "Construit en 1771 dans le plan de défense côtière de Charles III. Plan hexagonal en étoile, élément d'un réseau de tours et batteries côtières. Exposition permanente sur le patrimoine défensif.",
      ),
      categoria: "monumento",
      direccion: "Los Escullos · Níjar",
      latitud: 36.8051,
      longitud: -2.0673,
      epoca: T("Siglo XVIII (1771)", "18th century (1771)", "18. Jh. (1771)", "XVIIIᵉ s. (1771)"),
      estilo: T("Fortificación abaluartada", "Bastioned fortification", "Bastionärbefestigung", "Fortification bastionnée"),
      bic: true,
      horario: T(
        "Mar-Dom 10:00-14:00 y 17:00-20:00 (verano)",
        "Tue-Sun 10:00-14:00 and 17:00-20:00 (summer)",
        "Di-So 10:00-14:00 und 17:00-20:00 (Sommer)",
        "Mar-Dim 10:00-14:00 et 17:00-20:00 (été)",
      ),
      precio: T("Entrada gratuita", "Free entry", "Eintritt frei", "Entrée gratuite"),
    },
    {
      id: "demo-h-rodalquilar",
      nombre: "Pueblo minero de Rodalquilar",
      nombre_i18n: T("Pueblo minero de Rodalquilar", "Rodalquilar mining village", "Bergbaudorf Rodalquilar", "Village minier de Rodalquilar"),
      descripcion_corta: "Antigua explotación de oro reconvertida en jardín botánico y centro de interpretación.",
      descripcion_i18n: T(
        "Yacimiento minero de oro activo entre 1864 y 1990. Hoy alberga el Jardín Botánico El Albardinal, el Centro Geoturístico y rutas autoguiadas por los lavaderos y poblados abandonados.",
        "Gold mining site active 1864-1990. Now houses the El Albardinal Botanical Garden, the Geotourism Centre and self-guided routes through the washing plants and abandoned villages.",
        "Goldbergwerk (1864-1990). Heute Botanischer Garten El Albardinal, Geotourismuszentrum und selbstgeführte Routen durch Aufbereitungsanlagen und verlassene Siedlungen.",
        "Site minier d'or actif 1864-1990. Aujourd'hui Jardin Botanique El Albardinal, Centre Géo-touristique et parcours autoguidés à travers les laveries et villages abandonnés.",
      ),
      categoria: "yacimiento",
      direccion: "Rodalquilar · Níjar",
      latitud: 36.8472,
      longitud: -2.0408,
      epoca: T("Siglos XIX-XX (1864-1990)", "19th-20th c. (1864-1990)", "19.-20. Jh. (1864-1990)", "XIXᵉ-XXᵉ s. (1864-1990)"),
      estilo: T("Patrimonio industrial minero", "Mining industrial heritage", "Bergbau-Industrieerbe", "Patrimoine industriel minier"),
      bic: true,
      horario: T(
        "Jardín Botánico Mar-Dom 9:00-14:00",
        "Botanical garden Tue-Sun 9:00-14:00",
        "Botanischer Garten Di-So 9:00-14:00",
        "Jardin botanique Mar-Dim 9:00-14:00",
      ),
      precio: T("Acceso libre · Visitas guiadas 3 €", "Free access · Guided tours 3 €", "Freier Zugang · Führung 3 €", "Accès libre · Visite guidée 3 €"),
    },
    {
      id: "demo-h-iglesia",
      nombre: "Iglesia de Nuestra Señora de la Anunciación",
      nombre_i18n: T(
        "Iglesia de Nuestra Señora de la Anunciación",
        "Church of Our Lady of the Annunciation",
        "Kirche Unserer Lieben Frau von der Verkündigung",
        "Église Notre-Dame de l'Annonciation",
      ),
      descripcion_corta: "Templo mudéjar del s. XVI declarado Bien de Interés Cultural.",
      descripcion_i18n: T(
        "Edificio del s. XVI con artesonado mudéjar de madera labrada, una de las muestras más notables de Almería. Custodia la imagen de la Patrona de Níjar.",
        "16th-century church with a Mudéjar carved-wood coffered ceiling, one of the finest in Almería. Houses the image of the patron saint of Níjar.",
        "Kirche aus dem 16. Jh. mit Mudéjar-Holzkassettendecke, eine der schönsten in Almería. Beherbergt das Bild der Patronin von Níjar.",
        "Église du XVIᵉ siècle avec plafond à caissons mudéjar en bois sculpté, l'un des plus beaux d'Almería. Abrite l'image de la patronne de Níjar.",
      ),
      categoria: "monumento",
      direccion: "Plaza La Glorieta · Níjar",
      latitud: 36.9658,
      longitud: -2.2090,
      epoca: T("Siglo XVI", "16th century", "16. Jh.", "XVIᵉ siècle"),
      estilo: T("Mudéjar", "Mudéjar", "Mudéjar-Stil", "Mudéjar"),
      bic: true,
      horario: T(
        "Misa diaria 19:30 · Visitas con cita previa",
        "Daily mass 19:30 · Visits by appointment",
        "Tägliche Messe 19:30 · Besichtigung nach Vereinbarung",
        "Messe quotidienne 19:30 · Visites sur rendez-vous",
      ),
      precio: T("Gratuito", "Free", "Kostenlos", "Gratuit"),
    },
    {
      id: "demo-h-amoladeras",
      nombre: "Centro de Visitantes Las Amoladeras",
      nombre_i18n: T(
        "Centro de Visitantes Las Amoladeras",
        "Las Amoladeras Visitor Centre",
        "Besucherzentrum Las Amoladeras",
        "Centre des visiteurs Las Amoladeras",
      ),
      descripcion_corta: "Punto de entrada al Parque Natural con exposición sobre flora, fauna y geología.",
      descripcion_i18n: T(
        "Edificio de la Junta de Andalucía con exposición permanente sobre los valores naturales del Parque, sala audiovisual y punto de información turística. Inicio del sendero de Las Amoladeras.",
        "Andalusian government building with a permanent exhibition on the park's natural values, audiovisual room and tourist information point. Start of the Las Amoladeras trail.",
        "Gebäude der Junta de Andalucía mit Dauerausstellung zum Naturraum, Audiovisualsaal und Tourist-Info. Ausgangspunkt des Wanderwegs Las Amoladeras.",
        "Bâtiment de la Junta de Andalucía avec exposition permanente, salle audiovisuelle et point d'information touristique. Départ du sentier de Las Amoladeras.",
      ),
      categoria: "centro_visitantes",
      direccion: "Carretera AL-3115 km 7 · Retamar",
      latitud: 36.8169,
      longitud: -2.2913,
      epoca: T("Edificio actual: 2001", "Current building: 2001", "Aktueller Bau: 2001", "Bâtiment actuel : 2001"),
      estilo: T("Equipamiento de uso público", "Public-use facility", "Öffentliche Einrichtung", "Équipement d'usage public"),
      bic: false,
      horario: T(
        "Mar-Dom 10:00-15:00",
        "Tue-Sun 10:00-15:00",
        "Di-So 10:00-15:00",
        "Mar-Dim 10:00-15:00",
      ),
      precio: T("Gratuito", "Free", "Kostenlos", "Gratuit"),
    },
  ],

  servicios: [
    {
      id: "demo-s-oficina-sj",
      nombre: "Oficina de Turismo de San José",
      nombre_i18n: T(
        "Oficina de Turismo de San José",
        "San José Tourist Office",
        "Touristenbüro San José",
        "Office de tourisme de San José",
      ),
      descripcion_corta: "Información, mapas y reserva de visitas guiadas. Atención multilingüe.",
      descripcion_i18n: T(
        "Punto principal de información del Parque Natural en San José. Mapas oficiales, autorización para acceder a los Genoveses en verano, reservas de visitas guiadas y alquiler de bicicletas.",
        "Main visitor info point in San José. Official maps, summer permits for Genoveses access, guided-tour bookings and bike rental.",
        "Hauptinformationsstelle in San José. Offizielle Karten, Sommer-Zugangserlaubnis Genoveses, Buchung von Führungen und Fahrradverleih.",
        "Principal point d'information à San José. Cartes officielles, autorisations d'accès aux Genoveses en été, réservation de visites guidées et location de vélos.",
      ),
      categoria: "oficina_turismo",
      direccion: "Av. de San José 27 · San José · Níjar",
      latitud: 36.7647,
      longitud: -2.1085,
      telefono: "+34 950 38 02 99",
      horario: T(
        "Lun-Dom 10:00-14:00 y 17:00-20:00 (verano)",
        "Mon-Sun 10:00-14:00 and 17:00-20:00 (summer)",
        "Mo-So 10:00-14:00 und 17:00-20:00 (Sommer)",
        "Lun-Dim 10:00-14:00 et 17:00-20:00 (été)",
      ),
      idiomas: ["es", "en", "fr", "de"],
      web: "turismo.nijar.es",
    },
    {
      id: "demo-s-mercado",
      nombre: "Mercado Artesano de Níjar",
      nombre_i18n: T(
        "Mercado Artesano de Níjar",
        "Níjar Craft Market",
        "Kunsthandwerksmarkt Níjar",
        "Marché artisanal de Níjar",
      ),
      descripcion_corta: "Cerámica, jarapas y productos locales en el casco histórico. Sábado por la mañana.",
      descripcion_i18n: T(
        "Mercadillo semanal con cerámica nijareña, jarapas tejidas a mano, productos ecológicos y gastronomía local. Demostraciones en vivo de artesanos.",
        "Weekly craft market with Níjar ceramics, hand-woven jarapa rugs, organic produce and local cuisine. Live artisan demonstrations.",
        "Wöchentlicher Markt mit Níjar-Keramik, handgewebten Jarapa-Teppichen, Bio-Produkten und lokaler Küche. Live-Vorführungen.",
        "Marché hebdomadaire avec céramiques de Níjar, tapis jarapa tissés main, produits bio et cuisine locale. Démonstrations d'artisans en direct.",
      ),
      categoria: "punto_interes",
      direccion: "Plaza del Mercado · Níjar",
      latitud: 36.9654,
      longitud: -2.2095,
      telefono: "+34 950 36 00 88",
      horario: T(
        "Sábados 9:00-14:00",
        "Saturdays 9:00-14:00",
        "Samstags 9:00-14:00",
        "Samedis 9:00-14:00",
      ),
      idiomas: ["es", "en"],
    },
    {
      id: "demo-s-puerto",
      nombre: "Puerto Deportivo de San José",
      nombre_i18n: T(
        "Puerto Deportivo de San José",
        "San José Marina",
        "Yachthafen San José",
        "Port de plaisance de San José",
      ),
      descripcion_corta: "Excursiones en barco, alquiler de kayak y submarinismo en el Parque Natural.",
      descripcion_i18n: T(
        "Puerto pesquero y deportivo con empresas de excursiones costeras, alquiler de kayak y paddle surf, escuela de submarinismo y restaurantes con vistas a la bahía.",
        "Fishing and sport harbour with coastal-cruise operators, kayak and paddle-board rental, diving school and bay-view restaurants.",
        "Fischer- und Sporthafen mit Küstenfahrten, Kajak- und SUP-Verleih, Tauchschule und Restaurants mit Buchtblick.",
        "Port de pêche et de plaisance avec excursions côtières, location de kayak et paddle, école de plongée et restaurants avec vue sur la baie.",
      ),
      categoria: "punto_interes",
      direccion: "Puerto · San José · Níjar",
      latitud: 36.7626,
      longitud: -2.1066,
      telefono: "+34 950 38 00 41",
      horario: T(
        "Acceso libre 24/7 · Empresas según operador",
        "24/7 free access · Operator hours vary",
        "24/7 freier Zugang · Anbieterzeiten variieren",
        "Accès libre 24/7 · Horaires selon opérateur",
      ),
      idiomas: ["es", "en", "fr"],
    },
    {
      id: "demo-s-oficina-nijar",
      nombre: "Oficina Municipal de Turismo de Níjar",
      nombre_i18n: T(
        "Oficina Municipal de Turismo de Níjar",
        "Níjar Municipal Tourist Office",
        "Städtisches Touristenbüro Níjar",
        "Office municipal de tourisme de Níjar",
      ),
      descripcion_corta: "Punto de información oficial del Ayuntamiento. Rutas urbanas e itinerarios temáticos.",
      descripcion_i18n: T(
        "Punto de información municipal con rutas guiadas del casco histórico, itinerario de la cerámica, programa cultural y reservas de eventos del Ayuntamiento.",
        "Municipal info point with guided old-town tours, ceramics itinerary, cultural programme and council event bookings.",
        "Städtische Information mit Altstadtführungen, Keramik-Route, Kulturprogramm und Veranstaltungsbuchungen.",
        "Point d'information municipal avec visites guidées du centre historique, itinéraire de la céramique, programme culturel et réservations d'événements.",
      ),
      categoria: "oficina_turismo",
      direccion: "C/ Real 1 · Níjar",
      latitud: 36.9663,
      longitud: -2.2086,
      telefono: "+34 950 36 04 73",
      horario: T(
        "Lun-Vie 9:00-14:00 · Sab 10:00-13:00",
        "Mon-Fri 9:00-14:00 · Sat 10:00-13:00",
        "Mo-Fr 9:00-14:00 · Sa 10:00-13:00",
        "Lun-Ven 9:00-14:00 · Sam 10:00-13:00",
      ),
      idiomas: ["es", "en"],
      web: "turismo.nijar.es",
    },
  ],
};

export const DEMO_EVENTS = [
  {
    id: "demo-e-santa-ana",
    nombre: "Fiestas de Santa Ana",
    nombre_i18n: T("Fiestas de Santa Ana", "Saint Anne Festival", "Sankt-Anna-Fest", "Fêtes de Sainte-Anne"),
    descripcion: "Patronales de Níjar — procesión, verbena y feria con productos locales.",
    descripcion_i18n: T(
      "Las fiestas patronales más importantes del municipio. Procesión solemne, ofrenda floral, verbena popular y feria gastronómica con productos del campo nijareño.",
      "The town's main patron-saint festival. Solemn procession, floral offering, open-air dance and gastronomy fair with Níjar farm produce.",
      "Wichtigstes Schutzpatronfest der Gemeinde. Feierliche Prozession, Blumenopfer, Tanzabend und Gastronomie-Markt mit Níjar-Produkten.",
      "Principale fête patronale de la commune. Procession solennelle, offrande florale, bal populaire et foire gastronomique avec produits du terroir.",
    ),
    fecha_inicio: "2026-07-25T20:00:00",
    tipo: "fiesta",
    direccion: "Plaza La Glorieta · Níjar",
    latitud: 36.9658,
    longitud: -2.2090,
    precio: T("Gratuito", "Free", "Kostenlos", "Gratuit"),
    organizador: T("Ayuntamiento de Níjar", "Níjar Town Council", "Stadtverwaltung Níjar", "Mairie de Níjar"),
    aforo: 2500,
  },
  {
    id: "demo-e-carrera",
    nombre: "Carrera del Cabo de Gata",
    nombre_i18n: T("Carrera del Cabo de Gata", "Cabo de Gata Trail Race", "Cabo de Gata Trail-Lauf", "Course du Cabo de Gata"),
    descripcion: "Trail por senderos del Parque Natural. Modalidades 12 km y 25 km.",
    descripcion_i18n: T(
      "Décima edición de la prueba trail por los senderos costeros del Parque Natural. Dos modalidades — 12 km (popular) y 25 km (competitiva) — con avituallamiento y meta en San José.",
      "Tenth edition of the trail race on the coastal paths of the natural park. Two categories — 12 km (popular) and 25 km (competitive) — with refreshment posts and finish in San José.",
      "Zehnte Ausgabe des Trail-Laufs durch die Küstenwege des Naturparks. Zwei Strecken — 12 km (Volkslauf) und 25 km (Wettkampf) — mit Verpflegung und Ziel in San José.",
      "Dixième édition du trail sur les sentiers côtiers du parc naturel. Deux distances — 12 km (populaire) et 25 km (compétitive) — avec ravitaillements et arrivée à San José.",
    ),
    fecha_inicio: "2026-10-04T08:30:00",
    tipo: "deporte",
    direccion: "Salida: San José · Llegada: Las Negras",
    latitud: 36.7647,
    longitud: -2.1085,
    precio: T("Popular 15 € · Competitiva 25 €", "Popular €15 · Competitive €25", "Volkslauf 15 € · Wettkampf 25 €", "Populaire 15 € · Compétitive 25 €"),
    organizador: T("Club Triatlón Almería", "Almería Triathlon Club", "Triathlonclub Almería", "Club Triathlon Almería"),
    aforo: 800,
  },
  {
    id: "demo-e-patio",
    nombre: "Patio de Luces · Castillo de Los Escullos",
    nombre_i18n: T(
      "Patio de Luces · Castillo de Los Escullos",
      "Patio of Lights · Los Escullos Castle",
      "Lichterhof · Burg Los Escullos",
      "Cour de Lumières · Château de Los Escullos",
    ),
    descripcion: "Ciclo de conciertos acústicos al atardecer en la fortaleza dieciochesca.",
    descripcion_i18n: T(
      "Ciclo de seis conciertos acústicos al aire libre dentro del Castillo de San Felipe. Programación de músicas del mundo, flamenco contemporáneo y jazz. Aforo limitado.",
      "Series of six open-air acoustic concerts inside San Felipe Castle. World music, contemporary flamenco and jazz programme. Limited capacity.",
      "Sechs Akustikkonzerte unter freiem Himmel in der Burg San Felipe. Weltmusik, zeitgenössischer Flamenco und Jazz. Begrenzte Plätze.",
      "Cycle de six concerts acoustiques en plein air dans le Château San Felipe. Musiques du monde, flamenco contemporain et jazz. Places limitées.",
    ),
    fecha_inicio: "2026-08-12T21:00:00",
    tipo: "cultura",
    direccion: "Castillo de San Felipe · Los Escullos",
    latitud: 36.8051,
    longitud: -2.0673,
    precio: T("12 € · Niños gratis", "€12 · Children free", "12 € · Kinder frei", "12 € · Enfants gratuit"),
    organizador: T("Diputación de Almería", "Almería Provincial Council", "Provinzregierung Almería", "Conseil provincial d'Almería"),
    aforo: 200,
  },
  {
    id: "demo-e-salinas",
    nombre: "Aves y Sal · Visita guiada a las Salinas",
    nombre_i18n: T(
      "Aves y Sal · Visita guiada a las Salinas",
      "Birds and Salt · Guided Salt-Flats Visit",
      "Vögel und Salz · Geführter Besuch der Salinen",
      "Oiseaux et Sel · Visite guidée des Salines",
    ),
    descripcion: "Recorrido por las salinas del Cabo de Gata con observación de flamencos y aves migratorias.",
    descripcion_i18n: T(
      "Recorrido guiado de 2 horas por las salinas activas del Cabo de Gata (zona Ramsar) con observación de flamencos rosados, cigüeñuelas y aves migratorias. Incluye prismáticos.",
      "Two-hour guided tour of the active Cabo de Gata salt flats (Ramsar wetland) with pink flamingo, black-winged stilt and migratory bird watching. Binoculars provided.",
      "Zweistündige Führung durch die aktiven Salinen von Cabo de Gata (Ramsar) mit Beobachtung von Flamingos, Stelzenläufern und Zugvögeln. Fernglas inkl.",
      "Visite guidée de 2 h des salines actives de Cabo de Gata (Ramsar) avec observation de flamants roses, échasses blanches et oiseaux migrateurs. Jumelles incluses.",
    ),
    fecha_inicio: "2026-09-18T09:30:00",
    tipo: "naturaleza",
    direccion: "Centro de Visitantes Las Salinas · Cabo de Gata",
    latitud: 36.7445,
    longitud: -2.2160,
    precio: T("8 € · Reserva obligatoria", "€8 · Booking required", "8 € · Anmeldung erforderlich", "8 € · Réservation obligatoire"),
    organizador: T("SEO/BirdLife · Junta de Andalucía", "SEO/BirdLife · Andalusian government", "SEO/BirdLife · Junta de Andalucía", "SEO/BirdLife · Junta de Andalucía"),
    aforo: 25,
  },
];

/* ---------------------------------------------------------------
 * Chatbot demo — matcher léxico por intención. Se usa cuando el
 * endpoint /chatbot/query no está disponible (sin Docker), para
 * que el cuadro de preguntas no devuelva "Failed to fetch".
 * Devuelve { respuesta, sugerencias } en el idioma activo.
 * ------------------------------------------------------------- */

const CHATBOT_INTENTS = [
  {
    id: "saludo",
    keywords: T(
      ["hola", "buenos", "buenas", "saludos", "qué tal", "ola"],
      ["hi", "hello", "hey", "good morning", "good afternoon", "greetings"],
      ["hallo", "guten tag", "guten morgen", "grüß"],
      ["bonjour", "salut", "bonsoir", "coucou"],
    ),
    respuesta: T(
      "¡Hola! Soy el asistente del tótem de Níjar. Puedo recomendarte playas, rutas senderistas, patrimonio, eventos y servicios del Parque Natural Cabo de Gata-Níjar.",
      "Hi! I'm the Níjar totem assistant. I can recommend beaches, hiking trails, heritage sites, events and services in the Cabo de Gata-Níjar Natural Park.",
      "Hallo! Ich bin der Assistent des Totems von Níjar. Ich empfehle Strände, Wanderwege, Sehenswürdigkeiten, Veranstaltungen und Dienste im Naturpark Cabo de Gata-Níjar.",
      "Bonjour ! Je suis l'assistant du totem de Níjar. Je peux recommander des plages, des sentiers, du patrimoine, des événements et services du Parc Naturel Cabo de Gata-Níjar.",
    ),
    sugerencias: T(
      ["¿Qué playas hay cerca?", "Rutas a pie", "Eventos próximos"],
      ["Which beaches are nearby?", "Walking trails", "Upcoming events"],
      ["Welche Strände in der Nähe?", "Wanderwege", "Kommende Veranstaltungen"],
      ["Quelles plages à proximité ?", "Sentiers", "Événements à venir"],
    ),
  },
  {
    id: "playas",
    keywords: T(
      ["playa", "cala", "mar", "baño", "arena", "snorkel"],
      ["beach", "cove", "sea", "swim", "sand", "snorkel"],
      ["strand", "bucht", "meer", "baden", "sand", "schnorcheln"],
      ["plage", "crique", "mer", "baignade", "sable", "snorkeling"],
    ),
    respuesta: T(
      "Las playas más populares son Mónsul (la duna volcánica famosa), Los Genoveses (1 km de arena virgen), El Playazo (Bandera Azul, con chiringuito) y Las Negras (pueblo pesquero). Toca «Playas» en el menú para ver todas con servicios, longitud y accesibilidad.",
      "The most popular beaches are Mónsul (with its iconic volcanic dune), Los Genoveses (1 km of pristine sand), El Playazo (Blue Flag, with beach bar) and Las Negras (fishing village). Tap «Beaches» to see all of them with services, length and accessibility.",
      "Die beliebtesten Strände: Mónsul (berühmte Vulkandüne), Los Genoveses (1 km unberührter Sand), El Playazo (Blaue Flagge, Strandbar) und Las Negras (Fischerdorf). Tippen Sie auf «Strände», um alle mit Diensten, Länge und Barrierefreiheit zu sehen.",
      "Les plages les plus populaires : Mónsul (dune volcanique célèbre), Los Genoveses (1 km de sable vierge), El Playazo (Pavillon Bleu, buvette) et Las Negras (village de pêcheurs). Touchez « Plages » pour voir toutes avec services, longueur et accessibilité.",
    ),
    sugerencias: T(
      ["¿Mónsul tiene aparcamiento?", "Playas con Bandera Azul", "Cala accesible"],
      ["Parking at Mónsul?", "Blue Flag beaches", "Accessible cove"],
      ["Parkplatz in Mónsul?", "Blaue-Flagge-Strände", "Barrierefreie Bucht"],
      ["Parking à Mónsul ?", "Plages Pavillon Bleu", "Crique accessible"],
    ),
  },
  {
    id: "rutas",
    keywords: T(
      ["ruta", "sendero", "caminar", "andar", "camino", "trekking", "senderismo"],
      ["trail", "hike", "hiking", "walk", "route", "trekking"],
      ["wanderweg", "wandern", "route", "trekking", "pfad"],
      ["sentier", "randonnée", "marche", "route", "trekking"],
    ),
    respuesta: T(
      "Te recomiendo el Sendero de los Genoveses (7,4 km circular, dificultad media), la subida al Cerro del Fraile (5,6 km con vistas 360°) y la ruta al Faro de Cabo de Gata (10 km lineal). Para principiantes o silla de ruedas: el sendero costero Sirenas–La Almadraba (6 km llano). Pulsa «Rutas» para verlas todas.",
      "I recommend the Genoveses Trail (7.4 km circular, moderate), the climb to Cerro del Fraile (5.6 km with 360° views) and the lighthouse trail (10 km linear). For beginners or wheelchairs: the flat coastal Sirenas–La Almadraba walk (6 km). Tap «Trails» to see them all.",
      "Ich empfehle den Genoveses-Weg (7,4 km Rundweg, mittel), den Cerro del Fraile (5,6 km mit 360°-Aussicht) und den Leuchtturmweg (10 km linear). Für Anfänger oder Rollstuhl: der flache Küstenweg Sirenas–La Almadraba (6 km). Tippen Sie auf «Wanderwege».",
      "Je recommande le Sentier des Genoveses (7,4 km circulaire, modéré), l'ascension du Cerro del Fraile (5,6 km avec vues à 360°) et le sentier du phare (10 km linéaire). Débutants ou fauteuil : le parcours côtier plat Sirenas–La Almadraba (6 km). Touchez « Sentiers ».",
    ),
    sugerencias: T(
      ["Ruta accesible", "Ruta corta", "Sendero al faro"],
      ["Accessible trail", "Short walk", "Trail to the lighthouse"],
      ["Barrierefreier Weg", "Kurze Wanderung", "Weg zum Leuchtturm"],
      ["Sentier accessible", "Promenade courte", "Sentier vers le phare"],
    ),
  },
  {
    id: "patrimonio",
    keywords: T(
      ["patrimonio", "monumento", "castillo", "iglesia", "faro", "minas", "museo", "historia", "rodalquilar"],
      ["heritage", "monument", "castle", "church", "lighthouse", "mine", "museum", "history"],
      ["kulturerbe", "denkmal", "burg", "kirche", "leuchtturm", "mine", "museum", "geschichte"],
      ["patrimoine", "monument", "château", "église", "phare", "mine", "musée", "histoire"],
    ),
    respuesta: T(
      "Imprescindibles: el Faro de Cabo de Gata (1863) con su mirador, el Castillo de San Felipe en Los Escullos (s. XVIII, BIC), el antiguo pueblo minero de Rodalquilar y la iglesia mudéjar de Níjar (s. XVI). El Centro de Visitantes Las Amoladeras explica el Parque Natural. Pulsa «Patrimonio».",
      "Must-sees: the Cabo de Gata Lighthouse (1863) with its viewpoint, San Felipe Castle in Los Escullos (18th c., heritage listed), the Rodalquilar mining village and Níjar's 16th-c. Mudéjar church. The Las Amoladeras Visitor Centre introduces the park. Tap «Heritage».",
      "Sehenswert: Leuchtturm Cabo de Gata (1863), Burg San Felipe in Los Escullos (18. Jh., Kulturdenkmal), Bergbaudorf Rodalquilar und die Mudéjar-Kirche in Níjar (16. Jh.). Das Besucherzentrum Las Amoladeras stellt den Park vor. Tippen Sie auf «Kulturerbe».",
      "À ne pas manquer : le Phare de Cabo de Gata (1863), le Château San Felipe à Los Escullos (XVIIIᵉ s., classé), le village minier de Rodalquilar et l'église mudéjare de Níjar (XVIᵉ s.). Le Centre des visiteurs Las Amoladeras présente le parc. Touchez « Patrimoine ».",
    ),
    sugerencias: T(
      ["Horario del castillo", "Visita al faro", "Pueblo minero"],
      ["Castle opening hours", "Lighthouse visit", "Mining village"],
      ["Öffnungszeiten der Burg", "Besuch im Leuchtturm", "Bergbaudorf"],
      ["Horaires du château", "Visite du phare", "Village minier"],
    ),
  },
  {
    id: "eventos",
    keywords: T(
      ["evento", "fiesta", "concierto", "feria", "actividad", "programa", "agenda"],
      ["event", "festival", "concert", "fair", "activity", "programme", "schedule"],
      ["veranstaltung", "fest", "konzert", "messe", "aktivität", "programm", "termin"],
      ["événement", "fête", "concert", "foire", "activité", "programme", "agenda"],
    ),
    respuesta: T(
      "Próximamente: Fiestas de Santa Ana en Níjar (25 jul), conciertos Patio de Luces en el Castillo de Los Escullos (12 ago), Carrera del Cabo de Gata (4 oct) y visita guiada «Aves y Sal» a las salinas (18 sep). Pulsa «Eventos» para detalles, precios y aforo.",
      "Coming up: Saint Anne Festival in Níjar (25 Jul), Patio of Lights concerts at Los Escullos Castle (12 Aug), Cabo de Gata Trail Race (4 Oct) and «Birds and Salt» guided tour to the salt flats (18 Sep). Tap «Events» for prices and capacity.",
      "Demnächst: Sankt-Anna-Fest in Níjar (25. Juli), Konzertreihe Lichterhof in der Burg Los Escullos (12. Aug.), Trail-Lauf Cabo de Gata (4. Okt.) und Führung «Vögel und Salz» (18. Sep.). Tippen Sie auf «Veranstaltungen».",
      "Prochainement : Fêtes de Sainte-Anne à Níjar (25 juil.), concerts Cour de Lumières au Château de Los Escullos (12 août), Course du Cabo de Gata (4 oct.) et visite guidée « Oiseaux et Sel » (18 sep.). Touchez « Événements ».",
    ),
    sugerencias: T(
      ["¿Cuándo son las fiestas?", "Eventos gratuitos", "Conciertos"],
      ["When are the festivities?", "Free events", "Concerts"],
      ["Wann sind die Feiern?", "Kostenlose Veranstaltungen", "Konzerte"],
      ["Quand sont les fêtes ?", "Événements gratuits", "Concerts"],
    ),
  },
  {
    id: "emergencias",
    keywords: T(
      ["emergencia", "112", "ambulancia", "policía", "urgencia", "auxilio", "ayuda", "socorro"],
      ["emergency", "112", "ambulance", "police", "help", "urgent", "rescue"],
      ["notfall", "112", "krankenwagen", "polizei", "hilfe", "dringend"],
      ["urgence", "112", "ambulance", "police", "secours", "aide"],
    ),
    respuesta: T(
      "Para cualquier emergencia llama al 112 (multilingüe 24/7). Salvamento Marítimo: 900 202 202. Centro de salud Níjar: +34 950 38 12 50. Guardia Civil: 062. Pulsa «Emergencias» para ver todos los contactos.",
      "For any emergency call 112 (multilingual 24/7). Maritime Rescue: 900 202 202. Níjar Health Centre: +34 950 38 12 50. Civil Guard: 062. Tap «Emergency» for all contacts.",
      "Im Notfall 112 wählen (mehrsprachig 24/7). Seenotrettung: 900 202 202. Gesundheitszentrum Níjar: +34 950 38 12 50. Guardia Civil: 062. Tippen Sie auf «Notfall».",
      "En cas d'urgence : 112 (multilingue 24/7). Sauvetage en mer : 900 202 202. Centre de santé Níjar : +34 950 38 12 50. Guardia Civil : 062. Touchez « Urgences ».",
    ),
    sugerencias: T(
      ["Salvamento marítimo", "Centro de salud", "Guardia Civil"],
      ["Maritime rescue", "Health centre", "Civil Guard"],
      ["Seenotrettung", "Gesundheitszentrum", "Guardia Civil"],
      ["Sauvetage en mer", "Centre de santé", "Guardia Civil"],
    ),
  },
  {
    id: "comer",
    keywords: T(
      ["comer", "restaurante", "tapa", "tapas", "menú", "cena", "desayuno", "gastronomía", "almorzar"],
      ["eat", "restaurant", "food", "tapas", "menu", "dinner", "breakfast", "cuisine", "lunch"],
      ["essen", "restaurant", "tapas", "speisekarte", "abendessen", "frühstück", "küche", "mittag"],
      ["manger", "restaurant", "tapas", "menu", "dîner", "petit-déjeuner", "gastronomie", "déjeuner"],
    ),
    respuesta: T(
      "En San José, Las Negras, La Isleta del Moro y Rodalquilar tienes restaurantes con pescado fresco y arroz caldoso. En Níjar pueblo prueba el «trigo» y los dulces árabes. Los sábados, el Mercado Artesano de Níjar ofrece productos locales.",
      "In San José, Las Negras, La Isleta del Moro and Rodalquilar you'll find restaurants serving fresh fish and «arroz caldoso» rice. In Níjar town try «trigo» stew and Arab pastries. The Níjar Craft Market opens on Saturdays with local produce.",
      "In San José, Las Negras, La Isleta del Moro und Rodalquilar gibt es Restaurants mit frischem Fisch und «arroz caldoso». In Níjar probieren Sie «trigo» und arabische Süßspeisen. Samstags Kunsthandwerksmarkt mit lokalen Produkten.",
      "À San José, Las Negras, La Isleta del Moro et Rodalquilar : restaurants de poisson frais et « arroz caldoso ». À Níjar village : le « trigo » et pâtisseries arabes. Marché artisanal le samedi à Níjar.",
    ),
    sugerencias: T(
      ["Restaurantes accesibles", "Mercado de Níjar", "Productos locales"],
      ["Accessible restaurants", "Níjar market", "Local produce"],
      ["Barrierefreie Restaurants", "Markt Níjar", "Lokale Produkte"],
      ["Restaurants accessibles", "Marché de Níjar", "Produits locaux"],
    ),
  },
  {
    id: "transporte",
    keywords: T(
      ["autobús", "bus", "coche", "aparcamiento", "parking", "taxi", "transporte", "movilidad", "lanzadera", "llegar"],
      ["bus", "car", "parking", "taxi", "transport", "mobility", "shuttle", "reach", "arrive"],
      ["bus", "auto", "parkplatz", "taxi", "verkehr", "mobilität", "shuttle", "anfahrt"],
      ["bus", "voiture", "parking", "taxi", "transport", "mobilité", "navette", "arriver"],
    ),
    respuesta: T(
      "Autobuses regulares ALSA desde Almería a San José y Las Negras. En verano (jul-ago), una lanzadera conecta San José con las playas de Mónsul y los Genoveses (acceso al coche restringido). Aparcamiento gratuito en El Playazo y Rodalquilar.",
      "Regular ALSA buses run from Almería to San José and Las Negras. In summer (Jul-Aug), a shuttle connects San José with Mónsul and Genoveses beaches (cars restricted). Free parking at El Playazo and Rodalquilar.",
      "Reguläre ALSA-Busse von Almería nach San José und Las Negras. Im Sommer (Juli-Aug.) Shuttle von San José zu Mónsul und Los Genoveses (Autozugang beschränkt). Kostenloser Parkplatz in El Playazo und Rodalquilar.",
      "Bus ALSA réguliers depuis Almería vers San José et Las Negras. En été (juil.-août), navette entre San José et les plages de Mónsul et Genoveses (accès voiture régulé). Parking gratuit à El Playazo et Rodalquilar.",
    ),
    sugerencias: T(
      ["Aparcamiento en Mónsul", "Cómo llegar al faro", "Taxi en San José"],
      ["Parking at Mónsul", "How to reach the lighthouse", "Taxi in San José"],
      ["Parkplatz in Mónsul", "Anfahrt zum Leuchtturm", "Taxi in San José"],
      ["Parking à Mónsul", "Comment aller au phare", "Taxi à San José"],
    ),
  },
  {
    id: "horario",
    keywords: T(
      ["horario", "abierto", "hora", "cuando", "abre", "cierra"],
      ["hours", "open", "time", "when", "closing", "opening"],
      ["öffnungszeit", "geöffnet", "uhrzeit", "wann", "schließt"],
      ["horaire", "ouvert", "heure", "quand", "ouverture", "fermeture"],
    ),
    respuesta: T(
      "Cada lugar tiene su horario. Las oficinas de turismo: lun-dom 10:00-14:00 y 17:00-20:00 en verano. El Castillo de San Felipe: mar-dom 10:00-14:00 y 17:00-20:00 (verano). Centro de Visitantes Las Amoladeras: mar-dom 10:00-15:00. Toca «Servicios» o «Patrimonio» para más detalle.",
      "Each venue has its own hours. Tourist offices: Mon-Sun 10:00-14:00 and 17:00-20:00 (summer). San Felipe Castle: Tue-Sun 10:00-14:00 and 17:00-20:00 (summer). Las Amoladeras Centre: Tue-Sun 10:00-15:00. Tap «Services» or «Heritage» for details.",
      "Jeder Ort hat eigene Zeiten. Touristenbüros: Mo-So 10:00-14:00 und 17:00-20:00 (Sommer). Burg San Felipe: Di-So 10:00-14:00 und 17:00-20:00 (Sommer). Las Amoladeras: Di-So 10:00-15:00. Tippen Sie auf «Dienste» oder «Kulturerbe».",
      "Chaque lieu a ses horaires. Offices de tourisme : lun-dim 10:00-14:00 et 17:00-20:00 (été). Château San Felipe : mar-dim 10:00-14:00 et 17:00-20:00 (été). Centre Las Amoladeras : mar-dim 10:00-15:00. Touchez « Services » ou « Patrimoine ».",
    ),
    sugerencias: T(
      ["Oficina de turismo", "Castillo de San Felipe", "Centro de Visitantes"],
      ["Tourist office", "San Felipe Castle", "Visitor centre"],
      ["Touristenbüro", "Burg San Felipe", "Besucherzentrum"],
      ["Office de tourisme", "Château San Felipe", "Centre des visiteurs"],
    ),
  },
];

const CHATBOT_FALLBACK = {
  respuesta: T(
    "Puedo ayudarte con playas, rutas senderistas, patrimonio, eventos, gastronomía, transporte, horarios y emergencias del Parque Natural Cabo de Gata-Níjar. Prueba a preguntarme «¿Qué playas hay cerca?» o «Eventos esta semana».",
    "I can help with beaches, hiking trails, heritage, events, food, transport, opening hours and emergencies in the Cabo de Gata-Níjar Natural Park. Try asking «Which beaches are nearby?» or «Events this week».",
    "Ich helfe bei Stränden, Wanderwegen, Sehenswürdigkeiten, Veranstaltungen, Essen, Verkehr, Öffnungszeiten und Notfällen im Naturpark Cabo de Gata-Níjar. Fragen Sie z. B. «Welche Strände in der Nähe?».",
    "Je peux vous aider sur plages, sentiers, patrimoine, événements, gastronomie, transport, horaires et urgences du Parc Naturel Cabo de Gata-Níjar. Essayez « Quelles plages à proximité ? ».",
  ),
  sugerencias: T(
    ["¿Qué playas hay cerca?", "Rutas a pie", "Eventos próximos"],
    ["Which beaches are nearby?", "Walking trails", "Upcoming events"],
    ["Welche Strände in der Nähe?", "Wanderwege", "Kommende Veranstaltungen"],
    ["Quelles plages à proximité ?", "Sentiers", "Événements à venir"],
  ),
};

function normalize(text) {
  return String(text || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, ""); // sin acentos combinantes
}

export function answerChatbotDemo(text, lang) {
  const t = normalize(text);
  if (!t) {
    return {
      respuesta: CHATBOT_FALLBACK.respuesta[lang] || CHATBOT_FALLBACK.respuesta.es,
      sugerencias: CHATBOT_FALLBACK.sugerencias[lang] || CHATBOT_FALLBACK.sugerencias.es,
    };
  }
  for (const intent of CHATBOT_INTENTS) {
    const kws = intent.keywords[lang] || intent.keywords.es;
    if (kws.some(k => t.includes(normalize(k)))) {
      return {
        respuesta: intent.respuesta[lang] || intent.respuesta.es,
        sugerencias: intent.sugerencias[lang] || intent.sugerencias.es,
        intent_demo: intent.id,
      };
    }
  }
  return {
    respuesta: CHATBOT_FALLBACK.respuesta[lang] || CHATBOT_FALLBACK.respuesta.es,
    sugerencias: CHATBOT_FALLBACK.sugerencias[lang] || CHATBOT_FALLBACK.sugerencias.es,
  };
}
