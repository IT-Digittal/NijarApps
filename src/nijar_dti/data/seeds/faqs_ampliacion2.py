"""Segundo lote de ampliación de FAQs (hasta superar las 100 contractuales).

Cubre núcleos costeros, enclaves del parque, actividades, servicios prácticos
y atención a familias y mascotas. Reutiliza el helper ``_faq`` del primer lote.
"""

from __future__ import annotations

from nijar_dti.data.seeds.faqs_ampliacion import _faq

FAQS_AMPLIACION_2: list[dict] = [
    # ---- Núcleos y enclaves ----
    _faq(
        "nucleo_san_jose",
        "general",
        {
            "es": "¿Qué ofrece San José?",
            "en": "What does San José offer?",
            "de": "Was bietet San José?",
            "fr": "Que propose San José ?",
        },
        {
            "es": "San José es el principal núcleo turístico del parque: puerto deportivo, restaurantes, comercios, alquiler de actividades y acceso a Mónsul y Genoveses.",
            "en": "San José is the park's main tourist hub: marina, restaurants, shops, activity rentals and access to Mónsul and Genoveses.",
            "de": "San José ist der wichtigste Touristenort des Parks: Yachthafen, Restaurants, Geschäfte, Aktivitätenverleih und Zugang zu Mónsul und Genoveses.",
            "fr": "San José est le principal pôle touristique du parc : port de plaisance, restaurants, commerces, location d'activités et accès à Mónsul et Genoveses.",
        },
    ),
    _faq(
        "nucleo_isleta_moro",
        "general",
        {
            "es": "¿Cómo es La Isleta del Moro?",
            "en": "What is La Isleta del Moro like?",
            "de": "Wie ist La Isleta del Moro?",
            "fr": "Comment est La Isleta del Moro ?",
        },
        {
            "es": "Es un pequeño y pintoresco pueblo de pescadores con encanto, ideal para comer pescado fresco y disfrutar de un ambiente tranquilo junto al mar.",
            "en": "It is a small, charming fishing village, ideal for fresh fish and a quiet seaside atmosphere.",
            "de": "Ein kleines, charmantes Fischerdorf, ideal für frischen Fisch und eine ruhige Atmosphäre am Meer.",
            "fr": "Un petit village de pêcheurs plein de charme, idéal pour le poisson frais et une ambiance paisible au bord de mer.",
        },
    ),
    _faq(
        "nucleo_los_escullos",
        "general",
        {
            "es": "¿Qué ver en Los Escullos?",
            "en": "What to see in Los Escullos?",
            "de": "Was gibt es in Los Escullos zu sehen?",
            "fr": "Que voir à Los Escullos ?",
        },
        {
            "es": "Los Escullos destaca por el Castillo de San Felipe (s. XVIII), su playa y las formaciones de duna fósil. Hay buceo y senderos cercanos.",
            "en": "Los Escullos is known for the 18th-century San Felipe Castle, its beach and fossil dune formations. Diving and trails are nearby.",
            "de": "Los Escullos ist bekannt für die Burg San Felipe (18. Jh.), den Strand und fossile Dünen. Tauchen und Wanderwege in der Nähe.",
            "fr": "Los Escullos est connu pour le château San Felipe (XVIIIe), sa plage et ses dunes fossiles. Plongée et sentiers à proximité.",
        },
    ),
    _faq(
        "nucleo_las_negras",
        "general",
        {
            "es": "¿Cómo es Las Negras?",
            "en": "What is Las Negras like?",
            "de": "Wie ist Las Negras?",
            "fr": "Comment est Las Negras ?",
        },
        {
            "es": "Las Negras es un pueblo costero tranquilo con playa de cantos, punto de partida a pie hacia la Cala de San Pedro. Tiene restaurantes y empresas de kayak.",
            "en": "Las Negras is a quiet coastal village with a pebble beach, a starting point on foot to Cala de San Pedro. It has restaurants and kayak operators.",
            "de": "Las Negras ist ein ruhiges Küstendorf mit Kieselstrand, Ausgangspunkt zu Fuß zur Cala de San Pedro. Mit Restaurants und Kajakanbietern.",
            "fr": "Las Negras est un village côtier tranquille à plage de galets, départ à pied vers la Cala de San Pedro. Restaurants et loueurs de kayak.",
        },
    ),
    _faq(
        "enclave_arrecife_sirenas",
        "parque",
        {
            "es": "¿Qué es el Arrecife de las Sirenas?",
            "en": "What is the Arrecife de las Sirenas?",
            "de": "Was ist das Arrecife de las Sirenas?",
            "fr": "Qu'est-ce que l'Arrecife de las Sirenas ?",
        },
        {
            "es": "Son formaciones rocosas volcánicas junto al Faro de Cabo de Gata, uno de los paisajes más emblemáticos. Hay un mirador accesible con panel interpretativo.",
            "en": "They are volcanic rock formations by the Cabo de Gata Lighthouse, one of the most emblematic landscapes. There is an accessible viewpoint with an interpretive panel.",
            "de": "Vulkanische Felsformationen am Leuchtturm von Cabo de Gata, eine der markantesten Landschaften. Mit zugänglichem Aussichtspunkt und Infotafel.",
            "fr": "Des formations rocheuses volcaniques près du phare de Cabo de Gata, l'un des paysages les plus emblématiques. Belvédère accessible avec panneau d'interprétation.",
        },
    ),
    _faq(
        "enclave_mirador_amatista",
        "parque",
        {
            "es": "¿Merece la pena el Mirador de la Amatista?",
            "en": "Is the Amatista Viewpoint worth it?",
            "de": "Lohnt sich der Aussichtspunkt Amatista?",
            "fr": "Le belvédère de l'Amatista vaut-il le détour ?",
        },
        {
            "es": "Sí, ofrece una de las mejores panorámicas de la costa entre La Isleta y Las Negras. Está junto a la carretera y tiene aparcamiento.",
            "en": "Yes, it offers one of the best coastal panoramas between La Isleta and Las Negras. It is by the road and has parking.",
            "de": "Ja, einer der schönsten Küstenausblicke zwischen La Isleta und Las Negras. An der Straße gelegen, mit Parkplatz.",
            "fr": "Oui, l'un des plus beaux panoramas côtiers entre La Isleta et Las Negras. Au bord de la route, avec parking.",
        },
    ),
    # ---- Patrimonio y cultura ----
    _faq(
        "patrimonio_castillo_san_ramon",
        "cultura",
        {
            "es": "¿Se puede visitar el Castillo de San Ramón?",
            "en": "Can I visit San Ramón Castle?",
            "de": "Kann man die Burg San Ramón besichtigen?",
            "fr": "Peut-on visiter le château San Ramón ?",
        },
        {
            "es": "El Castillo de San Ramón, junto al Playazo de Rodalquilar, es de propiedad privada y no suele tener visita interior, pero su exterior es muy fotografiado.",
            "en": "San Ramón Castle, by El Playazo de Rodalquilar, is privately owned and usually not open inside, but its exterior is much photographed.",
            "de": "Die Burg San Ramón am Playazo de Rodalquilar ist in Privatbesitz und meist innen nicht zugänglich, aber außen ein beliebtes Fotomotiv.",
            "fr": "Le château San Ramón, près d'El Playazo de Rodalquilar, est privé et rarement ouvert à l'intérieur, mais son extérieur est très photographié.",
        },
        nivel="media",
    ),
    _faq(
        "patrimonio_iglesia_nijar",
        "cultura",
        {
            "es": "¿Qué ver en el pueblo de Níjar?",
            "en": "What to see in Níjar town?",
            "de": "Was gibt es im Dorf Níjar zu sehen?",
            "fr": "Que voir au village de Níjar ?",
        },
        {
            "es": "En Níjar pueblo destacan la Iglesia de Nuestra Señora de la Anunciación, el Barrio Alto, los talleres de cerámica y jarapas y sus calles tradicionales.",
            "en": "In Níjar town, highlights are the Church of Nuestra Señora de la Anunciación, the Barrio Alto, the pottery and 'jarapa' workshops and its traditional streets.",
            "de": "In Níjar-Dorf: die Kirche Nuestra Señora de la Anunciación, das Barrio Alto, Keramik- und 'Jarapa'-Werkstätten und die traditionellen Gassen.",
            "fr": "À Níjar village : l'église Nuestra Señora de la Anunciación, le Barrio Alto, les ateliers de céramique et de 'jarapas' et ses ruelles traditionnelles.",
        },
    ),
    _faq(
        "patrimonio_jardin_botanico",
        "cultura",
        {
            "es": "¿Qué es el Jardín Botánico El Albardinal?",
            "en": "What is the El Albardinal Botanical Garden?",
            "de": "Was ist der Botanische Garten El Albardinal?",
            "fr": "Qu'est-ce que le Jardin Botanique El Albardinal ?",
        },
        {
            "es": "Es un jardín en Rodalquilar dedicado a la flora autóctona de los ambientes áridos del sureste ibérico. Entrada gratuita; ideal para conocer la vegetación del parque.",
            "en": "It is a garden in Rodalquilar devoted to native flora of the arid southeast of Iberia. Free entry; ideal to learn about the park's vegetation.",
            "de": "Ein Garten in Rodalquilar mit einheimischer Flora der ariden Gebiete Südostspaniens. Eintritt frei; ideal, um die Vegetation des Parks kennenzulernen.",
            "fr": "Un jardin à Rodalquilar dédié à la flore native des milieux arides du sud-est ibérique. Entrée gratuite ; idéal pour découvrir la végétation du parc.",
        },
    ),
    # ---- Actividades y naturaleza ----
    _faq(
        "actividad_avistamiento_aves",
        "rutas",
        {
            "es": "¿Dónde observar aves además de en las salinas?",
            "en": "Where to watch birds besides the salt flats?",
            "de": "Wo Vögel beobachten außer an den Salinen?",
            "fr": "Où observer les oiseaux hormis aux salines ?",
        },
        {
            "es": "Además de las Salinas, las ramblas, acantilados y la zona de la Albufera de Adra (cercana) son buenos puntos. Primavera y otoño son las mejores épocas.",
            "en": "Besides the Salt Flats, the ramblas, cliffs and the nearby Albufera de Adra are good spots. Spring and autumn are the best seasons.",
            "de": "Neben den Salinen sind die Ramblas, Klippen und die nahe Albufera de Adra gute Orte. Frühling und Herbst sind am besten.",
            "fr": "Outre les salines, les ramblas, falaises et la proche Albufera de Adra sont de bons sites. Printemps et automne sont idéaux.",
        },
        nivel="media",
    ),
    _faq(
        "actividad_paseo_barco",
        "rutas",
        {
            "es": "¿Hay paseos en barco por las calas?",
            "en": "Are there boat trips along the coves?",
            "de": "Gibt es Bootsausflüge entlang der Buchten?",
            "fr": "Y a-t-il des sorties en bateau le long des criques ?",
        },
        {
            "es": "Sí, desde San José y otros puntos salen excursiones en barco que recorren las calas inaccesibles por tierra. Reserva con antelación en temporada alta.",
            "en": "Yes, from San José and other points there are boat trips visiting coves unreachable by land. Book ahead in high season.",
            "de": "Ja, von San José und anderen Orten gibt es Bootsausflüge zu den vom Land unerreichbaren Buchten. In der Hochsaison vorab buchen.",
            "fr": "Oui, depuis San José et d'autres points, des excursions en bateau visitent les criques inaccessibles par terre. Réservez à l'avance en haute saison.",
        },
        nivel="media",
    ),
    _faq(
        "actividad_familias_ninos",
        "general",
        {
            "es": "¿Qué actividades hay para ir con niños?",
            "en": "What activities are there for children?",
            "de": "Welche Aktivitäten gibt es für Kinder?",
            "fr": "Quelles activités pour les enfants ?",
        },
        {
            "es": "Playas tranquilas como San José o El Playazo, snorkel sencillo, el Jardín Botánico, los observatorios de aves y los castillos costeros son ideales en familia.",
            "en": "Calm beaches like San José or El Playazo, easy snorkelling, the Botanical Garden, bird hides and the coastal castles are great for families.",
            "de": "Ruhige Strände wie San José oder El Playazo, einfaches Schnorcheln, der Botanische Garten, Vogelhütten und die Küstenburgen sind ideal für Familien.",
            "fr": "Des plages calmes comme San José ou El Playazo, le snorkeling facile, le Jardin Botanique, les observatoires d'oiseaux et les châteaux côtiers sont parfaits en famille.",
        },
    ),
    # ---- Servicios prácticos ----
    _faq(
        "servicio_gasolinera",
        "servicios",
        {
            "es": "¿Dónde hay gasolineras?",
            "en": "Where are there petrol stations?",
            "de": "Wo gibt es Tankstellen?",
            "fr": "Où y a-t-il des stations-service ?",
        },
        {
            "es": "Hay gasolineras en Níjar, San José, Campohermoso y la zona de San Isidro. Dentro del parque hay pocas, conviene repostar antes de adentrarse en el litoral.",
            "en": "There are petrol stations in Níjar, San José, Campohermoso and the San Isidro area. Few inside the park, so refuel before heading to the coast.",
            "de": "Tankstellen gibt es in Níjar, San José, Campohermoso und im Gebiet San Isidro. Im Park wenige; vor der Küstenfahrt tanken.",
            "fr": "Des stations-service à Níjar, San José, Campohermoso et la zone de San Isidro. Peu dans le parc ; faites le plein avant la côte.",
        },
        nivel="media",
    ),
    _faq(
        "servicio_carga_electrico",
        "servicios",
        {
            "es": "¿Hay puntos de carga para coches eléctricos?",
            "en": "Are there EV charging points?",
            "de": "Gibt es Ladepunkte für Elektroautos?",
            "fr": "Y a-t-il des bornes de recharge électrique ?",
        },
        {
            "es": "Sí, el municipio está desplegando puntos de recarga para vehículos eléctricos en varios núcleos. Consulta su ubicación y disponibilidad en la app municipal.",
            "en": "Yes, the municipality is rolling out EV charging points in several villages. Check their location and availability in the municipal app.",
            "de": "Ja, die Gemeinde baut Ladepunkte für E-Fahrzeuge in mehreren Orten auf. Standort und Verfügbarkeit in der städtischen App.",
            "fr": "Oui, la municipalité déploie des bornes de recharge dans plusieurs villages. Localisation et disponibilité dans l'app municipale.",
        },
        nivel="media",
    ),
    _faq(
        "servicio_alquiler_coche",
        "servicios",
        {
            "es": "¿Necesito coche para moverme por la zona?",
            "en": "Do I need a car to get around?",
            "de": "Brauche ich ein Auto, um herumzukommen?",
            "fr": "Ai-je besoin d'une voiture pour me déplacer ?",
        },
        {
            "es": "El transporte público es limitado, así que tener coche facilita mucho moverse entre núcleos y playas. En verano usa el bus lanzadera para evitar problemas de aparcamiento.",
            "en": "Public transport is limited, so having a car makes moving between villages and beaches much easier. In summer use the shuttle bus to avoid parking issues.",
            "de": "Der ÖPNV ist begrenzt; ein Auto erleichtert das Reisen zwischen Orten und Stränden. Im Sommer den Pendelbus nutzen, um Parkprobleme zu vermeiden.",
            "fr": "Les transports publics sont limités ; une voiture facilite les déplacements entre villages et plages. En été, utilisez la navette pour éviter les problèmes de stationnement.",
        },
    ),
    _faq(
        "servicio_veterinario",
        "servicios",
        {
            "es": "¿Hay veterinario por si viajo con mascota?",
            "en": "Is there a vet if I travel with a pet?",
            "de": "Gibt es einen Tierarzt, falls ich mit Haustier reise?",
            "fr": "Y a-t-il un vétérinaire si je voyage avec un animal ?",
        },
        {
            "es": "Sí, hay clínicas veterinarias en Níjar y Campohermoso. Para urgencias fuera de horario, consulta el servicio de guardia anunciado en la propia clínica.",
            "en": "Yes, there are veterinary clinics in Níjar and Campohermoso. For out-of-hours emergencies, check the on-duty service announced at the clinic.",
            "de": "Ja, Tierkliniken in Níjar und Campohermoso. Für Notfälle außerhalb der Zeiten den an der Klinik angekündigten Notdienst beachten.",
            "fr": "Oui, des cliniques vétérinaires à Níjar et Campohermoso. Pour les urgences hors horaires, consultez le service de garde indiqué à la clinique.",
        },
        nivel="media",
    ),
    _faq(
        "servicio_urgencias_turista",
        "servicios",
        {
            "es": "Soy turista extranjero, ¿cómo accedo a asistencia médica?",
            "en": "I'm a foreign tourist, how do I access medical care?",
            "de": "Ich bin ausländischer Tourist, wie bekomme ich medizinische Hilfe?",
            "fr": "Touriste étranger, comment accéder aux soins médicaux ?",
        },
        {
            "es": "Para urgencias, llama al 112. En la UE, lleva tu Tarjeta Sanitaria Europea; el centro de salud de Níjar y el hospital de Almería atienden urgencias.",
            "en": "For emergencies, call 112. In the EU, carry your European Health Insurance Card; Níjar health centre and Almería hospital handle emergencies.",
            "de": "Bei Notfällen 112 anrufen. In der EU die Europäische Krankenversicherungskarte mitführen; Gesundheitszentrum Níjar und Krankenhaus Almería behandeln Notfälle.",
            "fr": "Pour les urgences, appelez le 112. Dans l'UE, munissez-vous de la Carte Européenne d'Assurance Maladie ; le centre de santé de Níjar et l'hôpital d'Almería gèrent les urgences.",
        },
    ),
    # ---- Información práctica ----
    _faq(
        "practico_pago_tarjeta",
        "general",
        {
            "es": "¿Se puede pagar con tarjeta en todas partes?",
            "en": "Can I pay by card everywhere?",
            "de": "Kann ich überall mit Karte zahlen?",
            "fr": "Peut-on payer par carte partout ?",
        },
        {
            "es": "En la mayoría de hoteles, restaurantes y comercios sí, pero en chiringuitos, mercadillos o pequeños negocios puede ser solo efectivo. Lleva algo de efectivo por si acaso.",
            "en": "In most hotels, restaurants and shops yes, but beach bars, markets or small businesses may be cash only. Carry some cash just in case.",
            "de": "In den meisten Hotels, Restaurants und Geschäften ja, aber Strandbars, Märkte oder kleine Betriebe nur bar. Etwas Bargeld mitnehmen.",
            "fr": "Dans la plupart des hôtels, restaurants et commerces oui, mais paillotes, marchés ou petits commerces peuvent être en espèces. Prévoyez du liquide.",
        },
        nivel="media",
    ),
    _faq(
        "practico_que_llevar",
        "general",
        {
            "es": "¿Qué debo llevar para visitar el parque?",
            "en": "What should I bring to visit the park?",
            "de": "Was sollte ich für den Parkbesuch mitnehmen?",
            "fr": "Que dois-je emporter pour visiter le parc ?",
        },
        {
            "es": "Agua abundante, protección solar, gorra, calzado cómodo y, si vas a calas remotas, comida. No hay sombra ni servicios en muchos enclaves.",
            "en": "Plenty of water, sun protection, a hat, comfortable footwear and, for remote coves, food. Many spots have no shade or facilities.",
            "de": "Viel Wasser, Sonnenschutz, Hut, bequeme Schuhe und für abgelegene Buchten Essen. Viele Orte haben weder Schatten noch Einrichtungen.",
            "fr": "Beaucoup d'eau, protection solaire, casquette, chaussures confortables et, pour les criques isolées, de la nourriture. Peu d'ombre et de services.",
        },
    ),
    _faq(
        "practico_temporada_evitar",
        "general",
        {
            "es": "¿Cuándo hay menos gente?",
            "en": "When are there fewer people?",
            "de": "Wann ist weniger los?",
            "fr": "Quand y a-t-il moins de monde ?",
        },
        {
            "es": "Fuera de julio y agosto. Mayo, junio, septiembre y octubre ofrecen buen clima con mucha menos afluencia; entre semana siempre hay más tranquilidad.",
            "en": "Outside July and August. May, June, September and October offer good weather with far fewer crowds; weekdays are always quieter.",
            "de": "Außerhalb Juli und August. Mai, Juni, September und Oktober bieten gutes Wetter mit viel weniger Andrang; wochentags ruhiger.",
            "fr": "Hors juillet-août. Mai, juin, septembre et octobre offrent un bon climat avec bien moins de monde ; en semaine, c'est plus calme.",
        },
    ),
    _faq(
        "practico_mascotas_general",
        "general",
        {
            "es": "¿Puedo viajar con mi mascota por la zona?",
            "en": "Can I travel with my pet in the area?",
            "de": "Kann ich mit meinem Haustier in der Gegend reisen?",
            "fr": "Puis-je voyager avec mon animal dans la région ?",
        },
        {
            "es": "Sí, pero recuerda que los perros no pueden ir a las playas de baño en verano (salvo las habilitadas) y deben ir atados en zonas del parque. Lleva agua para tu mascota.",
            "en": "Yes, but remember dogs cannot go to bathing beaches in summer (except designated ones) and must be leashed in park areas. Bring water for your pet.",
            "de": "Ja, aber Hunde dürfen im Sommer nicht an Badestrände (außer ausgewiesene) und müssen in Parkbereichen angeleint sein. Wasser für das Tier mitnehmen.",
            "fr": "Oui, mais les chiens ne peuvent pas aller aux plages de baignade en été (sauf désignées) et doivent être tenus en laisse dans le parc. Emportez de l'eau pour l'animal.",
        },
        nivel="media",
    ),
    # ---- Rutas adicionales ----
    _faq(
        "ruta_san_pedro_pie",
        "rutas",
        {
            "es": "¿Cómo llego a la Cala de San Pedro?",
            "en": "How do I reach Cala de San Pedro?",
            "de": "Wie erreiche ich die Cala de San Pedro?",
            "fr": "Comment atteindre la Cala de San Pedro ?",
        },
        {
            "es": "A pie desde Las Negras (1-1,5 h por sendero costero) o en barco-taxi en temporada. No hay acceso rodado; lleva agua y calzado de senderismo.",
            "en": "On foot from Las Negras (1-1.5 h on the coastal path) or by water-taxi in season. No road access; bring water and hiking shoes.",
            "de": "Zu Fuß von Las Negras (1-1,5 Std. auf dem Küstenpfad) oder per Boots-Taxi in der Saison. Keine Zufahrt; Wasser und Wanderschuhe mitnehmen.",
            "fr": "À pied depuis Las Negras (1-1,5 h par le sentier côtier) ou en bateau-taxi en saison. Pas d'accès routier ; eau et chaussures de marche.",
        },
    ),
    _faq(
        "ruta_sendero_amoladeras",
        "rutas",
        {
            "es": "¿Hay senderos fáciles cerca del Centro de Visitantes?",
            "en": "Are there easy trails near the Visitor Center?",
            "de": "Gibt es leichte Wege beim Besucherzentrum?",
            "fr": "Y a-t-il des sentiers faciles près du Centre des Visiteurs ?",
        },
        {
            "es": "Sí, junto a Las Amoladeras hay un sendero interpretativo corto y llano, ideal para conocer la vegetación y el paisaje del parque en familia.",
            "en": "Yes, by Las Amoladeras there is a short, flat interpretive trail, ideal to discover the park's vegetation and landscape with the family.",
            "de": "Ja, bei Las Amoladeras gibt es einen kurzen, flachen Lehrpfad, ideal, um Vegetation und Landschaft des Parks mit der Familie zu entdecken.",
            "fr": "Oui, près de Las Amoladeras, un court sentier d'interprétation plat, idéal pour découvrir la végétation et le paysage du parc en famille.",
        },
    ),
    # ---- Eventos / mercados adicionales ----
    _faq(
        "eventos_mercado_pescado",
        "eventos",
        {
            "es": "¿Hay lonja o venta de pescado fresco?",
            "en": "Is there a fish market or fresh fish sale?",
            "de": "Gibt es einen Fischmarkt oder frischen Fischverkauf?",
            "fr": "Y a-t-il une criée ou vente de poisson frais ?",
        },
        {
            "es": "El pescado fresco de la zona se sirve en los restaurantes de los pueblos pesqueros (La Isleta, San José, Las Negras). Pregunta por la captura del día.",
            "en": "Local fresh fish is served in the fishing villages' restaurants (La Isleta, San José, Las Negras). Ask for the catch of the day.",
            "de": "Frischer Fisch der Region wird in den Restaurants der Fischerdörfer (La Isleta, San José, Las Negras) serviert. Nach dem Tagesfang fragen.",
            "fr": "Le poisson frais local est servi dans les restaurants des villages de pêcheurs (La Isleta, San José, Las Negras). Demandez la pêche du jour.",
        },
        nivel="media",
    ),
    # ---- Sobre el chatbot / fallback ----
    _faq(
        "meta_no_entiende",
        "general",
        {
            "es": "No me has entendido / ¿puedes repetir?",
            "en": "You didn't understand me / can you repeat?",
            "de": "Du hast mich nicht verstanden / kannst du wiederholen?",
            "fr": "Tu ne m'as pas compris / peux-tu répéter ?",
        },
        {
            "es": "Disculpa, ¿puedes reformular la pregunta con otras palabras? Puedo ayudarte con playas, rutas, parque natural, eventos, servicios y emergencias.",
            "en": "Sorry, could you rephrase your question? I can help with beaches, trails, the natural park, events, services and emergencies.",
            "de": "Entschuldigung, können Sie die Frage anders formulieren? Ich helfe bei Stränden, Wegen, Naturpark, Veranstaltungen, Diensten und Notfällen.",
            "fr": "Désolé, pouvez-vous reformuler la question ? Je peux aider sur les plages, sentiers, parc naturel, événements, services et urgences.",
        },
    ),
    _faq(
        "meta_hablar_persona",
        "general",
        {
            "es": "Quiero hablar con una persona de la oficina de turismo",
            "en": "I want to talk to a person at the tourist office",
            "de": "Ich möchte mit einer Person im Tourismusbüro sprechen",
            "fr": "Je veux parler à une personne de l'office de tourisme",
        },
        {
            "es": "Puedes acudir a la Oficina de Turismo o llamar en horario de atención. Te muestro sus datos de contacto y horario si me lo pides ('oficina de turismo').",
            "en": "You can visit the Tourist Office or call during opening hours. I can show you its contact details and hours if you ask ('tourist office').",
            "de": "Sie können das Tourismusbüro besuchen oder während der Öffnungszeiten anrufen. Auf Wunsch zeige ich Kontaktdaten und Zeiten ('Tourismusbüro').",
            "fr": "Vous pouvez vous rendre à l'Office de Tourisme ou appeler aux heures d'ouverture. Je peux afficher ses coordonnées et horaires si vous le demandez ('office de tourisme').",
        },
    ),
    # ---- Más playas/servicios de playa ----
    _faq(
        "playa_servicios_chiringuito",
        "playas",
        {
            "es": "¿Las playas tienen chiringuitos y hamacas?",
            "en": "Do the beaches have beach bars and sunbeds?",
            "de": "Gibt es an den Stränden Strandbars und Liegen?",
            "fr": "Les plages ont-elles des paillotes et transats ?",
        },
        {
            "es": "Las playas urbanas (San José, Agua Amarga) suelen tener chiringuitos y servicios; las calas vírgenes del parque no tienen ningún servicio, ve preparado.",
            "en": "Town beaches (San José, Agua Amarga) usually have beach bars and services; the park's unspoilt coves have none, so come prepared.",
            "de": "Ortsstrände (San José, Agua Amarga) haben meist Strandbars und Service; die unberührten Buchten des Parks haben keine, kommen Sie vorbereitet.",
            "fr": "Les plages urbaines (San José, Agua Amarga) ont souvent paillotes et services ; les criques sauvages du parc n'en ont aucun, soyez prévoyant.",
        },
    ),
    _faq(
        "playa_bandera_azul",
        "playas",
        {
            "es": "¿Hay playas con bandera azul?",
            "en": "Are there Blue Flag beaches?",
            "de": "Gibt es Strände mit Blauer Flagge?",
            "fr": "Y a-t-il des plages pavillon bleu ?",
        },
        {
            "es": "Algunas playas urbanas del municipio cuentan con distintivos de calidad. El listado puede variar cada temporada; consúltalo en la Oficina de Turismo o en la app.",
            "en": "Some town beaches hold quality awards. The list can vary each season; check at the Tourist Office or in the app.",
            "de": "Einige Ortsstrände tragen Qualitätsauszeichnungen. Die Liste kann je Saison variieren; im Tourismusbüro oder in der App prüfen.",
            "fr": "Certaines plages urbaines détiennent des labels de qualité. La liste peut varier chaque saison ; vérifiez à l'Office de Tourisme ou dans l'app.",
        },
        nivel="media",
    ),
    # ---- Gastronomía adicional ----
    _faq(
        "gastronomia_reservas",
        "gastronomia",
        {
            "es": "¿Necesito reservar mesa en los restaurantes?",
            "en": "Do I need to book a table at restaurants?",
            "de": "Muss ich im Restaurant einen Tisch reservieren?",
            "fr": "Dois-je réserver une table au restaurant ?",
        },
        {
            "es": "En temporada alta (julio-agosto) y fines de semana es muy recomendable reservar, sobre todo en los pueblos costeros más demandados como San José o Agua Amarga.",
            "en": "In high season (July-August) and at weekends booking is highly recommended, especially in the busiest coastal villages like San José or Agua Amarga.",
            "de": "In der Hochsaison (Juli-August) und an Wochenenden ist Reservierung sehr empfehlenswert, vor allem in beliebten Küstenorten wie San José oder Agua Amarga.",
            "fr": "En haute saison (juillet-août) et le week-end, la réservation est vivement conseillée, surtout dans les villages côtiers prisés comme San José ou Agua Amarga.",
        },
        nivel="media",
    ),
    _faq(
        "parque_fauna_camaleon",
        "parque",
        {
            "es": "¿Qué fauna puedo ver en el parque?",
            "en": "What wildlife can I see in the park?",
            "de": "Welche Tierwelt kann ich im Park sehen?",
            "fr": "Quelle faune puis-je voir dans le parc ?",
        },
        {
            "es": "Destacan el camaleón común, aves marinas y esteparias, flamencos en las salinas y fauna marina en la reserva. Obsérvala sin molestarla ni alimentarla.",
            "en": "Highlights include the common chameleon, sea and steppe birds, flamingos at the salt flats and marine life in the reserve. Watch without disturbing or feeding.",
            "de": "Höhepunkte: das Chamäleon, See- und Steppenvögel, Flamingos an den Salinen und Meeresfauna im Reservat. Beobachten, ohne zu stören oder zu füttern.",
            "fr": "À voir : le caméléon commun, oiseaux marins et steppiques, flamants aux salines et faune marine dans la réserve. Observez sans déranger ni nourrir.",
        },
    ),
    _faq(
        "gastronomia_tapas",
        "gastronomia",
        {
            "es": "¿Hay cultura de tapas en la zona?",
            "en": "Is there a tapas culture in the area?",
            "de": "Gibt es eine Tapas-Kultur in der Gegend?",
            "fr": "Y a-t-il une culture des tapas dans la région ?",
        },
        {
            "es": "Sí, en Almería es tradición que la tapa acompañe gratis a la bebida. En los bares de Níjar y los pueblos podrás disfrutar de esta costumbre.",
            "en": "Yes, in Almería it is traditional for a free tapa to come with your drink. In the bars of Níjar and the villages you can enjoy this custom.",
            "de": "Ja, in Almería ist es Tradition, dass zum Getränk eine kostenlose Tapa serviert wird. In den Bars von Níjar und den Dörfern gilt dieser Brauch.",
            "fr": "Oui, à Almería, il est de tradition qu'une tapa gratuite accompagne la boisson. Dans les bars de Níjar et des villages, profitez de cette coutume.",
        },
    ),
    _faq(
        "servicio_correos",
        "servicios",
        {
            "es": "¿Dónde hay oficina de correos?",
            "en": "Where is there a post office?",
            "de": "Wo gibt es ein Postamt?",
            "fr": "Où y a-t-il un bureau de poste ?",
        },
        {
            "es": "Hay oficina de Correos en Níjar pueblo y en otros núcleos principales como Campohermoso y San Isidro. Consulta horarios, que se reducen en agosto.",
            "en": "There is a post office in Níjar town and in other main villages such as Campohermoso and San Isidro. Check hours, which are reduced in August.",
            "de": "Ein Postamt gibt es in Níjar-Dorf und in anderen Hauptorten wie Campohermoso und San Isidro. Öffnungszeiten prüfen, im August reduziert.",
            "fr": "Il y a un bureau de poste à Níjar village et dans d'autres villages comme Campohermoso et San Isidro. Vérifiez les horaires, réduits en août.",
        },
        nivel="media",
    ),
    _faq(
        "transporte_estado_carreteras",
        "servicios",
        {
            "es": "¿Cómo son las carreteras dentro del parque?",
            "en": "What are the roads like inside the park?",
            "de": "Wie sind die Straßen im Park?",
            "fr": "Comment sont les routes dans le parc ?",
        },
        {
            "es": "Son carreteras secundarias, estrechas y con curvas en algunos tramos hacia las calas. Conduce con precaución, respeta a ciclistas y no aparques fuera de las zonas habilitadas.",
            "en": "They are secondary roads, narrow and winding on some sections to the coves. Drive carefully, respect cyclists and do not park outside designated areas.",
            "de": "Es sind Nebenstraßen, eng und kurvig auf manchen Abschnitten zu den Buchten. Vorsichtig fahren, Radfahrer respektieren und nicht außerhalb ausgewiesener Zonen parken.",
            "fr": "Ce sont des routes secondaires, étroites et sinueuses par endroits vers les criques. Conduisez prudemment, respectez les cyclistes et ne stationnez pas hors des zones prévues.",
        },
        nivel="media",
    ),
    _faq(
        "alojamiento_precios_temporada",
        "servicios",
        {
            "es": "¿Varían mucho los precios de alojamiento según la época?",
            "en": "Do accommodation prices vary a lot by season?",
            "de": "Schwanken die Unterkunftspreise stark je Saison?",
            "fr": "Les prix d'hébergement varient-ils beaucoup selon la saison ?",
        },
        {
            "es": "Sí, en julio y agosto los precios son notablemente más altos y hay estancia mínima en muchos alojamientos. En primavera y otoño encontrarás mejores tarifas.",
            "en": "Yes, in July and August prices are notably higher and many places require a minimum stay. In spring and autumn you'll find better rates.",
            "de": "Ja, im Juli und August sind die Preise deutlich höher und viele Unterkünfte verlangen einen Mindestaufenthalt. Im Frühling und Herbst bessere Tarife.",
            "fr": "Oui, en juillet-août les prix sont nettement plus élevés et beaucoup d'hébergements imposent un séjour minimum. Au printemps et en automne, meilleurs tarifs.",
        },
        nivel="media",
    ),
]
