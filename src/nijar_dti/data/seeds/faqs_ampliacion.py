"""Ampliación de la base de FAQs del chatbot hasta el mínimo contractual.

La Memoria Técnica y el PPT comprometen una base de conocimiento de **≥100
FAQs** en los cuatro idiomas obligatorios (ES/EN/DE/FR). Este módulo amplía
la base inicial (``faqs.py``) cubriendo playas, parque natural, rutas y
actividades, servicios, gastronomía, alojamiento, cultura y patrimonio,
eventos, transporte, accesibilidad, información práctica y emergencias.

Cada entrada mantiene el mismo esquema que ``FAQS_SEED`` y se concatena a
ella, de modo que el generador de Rasa y el motor lexical la consumen sin
cambios. Para añadir una FAQ basta con sumarla aquí y re-generar/re-entrenar.
"""

from __future__ import annotations


def _faq(intent, categoria, p, r, nivel="alta", fuente=None):
    """Crea una FAQ a partir de dicts {es,en,de,fr} de pregunta y respuesta."""
    d: dict = {
        "intent": intent,
        "categoria": categoria,
        "pregunta_es": p["es"],
        "pregunta_en": p["en"],
        "pregunta_de": p["de"],
        "pregunta_fr": p["fr"],
        "respuesta_es": r["es"],
        "respuesta_en": r["en"],
        "respuesta_de": r["de"],
        "respuesta_fr": r["fr"],
        "nivel_confianza": nivel,
    }
    if fuente:
        d["fuente_descripcion"] = fuente
    return d


FAQS_AMPLIACION: list[dict] = [
    # ===================== PLAYAS =====================
    _faq(
        "playa_genoveses",
        "playas",
        {
            "es": "¿Cómo es la playa de los Genoveses?",
            "en": "What is Genoveses beach like?",
            "de": "Wie ist der Strand Genoveses?",
            "fr": "Comment est la plage de Genoveses ?",
        },
        {
            "es": "Genoveses es una amplia playa virgen de arena fina, sin edificaciones, rodeada de dunas y retamares. En verano el acceso en coche está regulado por aforo.",
            "en": "Genoveses is a wide, unspoilt fine-sand beach with no buildings, surrounded by dunes. In summer car access is capacity-controlled.",
            "de": "Genoveses ist ein weiter, unberührter Feinsandstrand ohne Bebauung, umgeben von Dünen. Im Sommer ist die Anfahrt mit dem Auto kapazitätsgeregelt.",
            "fr": "Genoveses est une vaste plage sauvage de sable fin, sans constructions, entourée de dunes. En été l'accès en voiture est régulé par capacité.",
        },
        fuente="Parque Natural Cabo de Gata-Níjar",
    ),
    _faq(
        "playa_cala_enmedio",
        "playas",
        {
            "es": "¿Cómo llego a Cala de Enmedio?",
            "en": "How do I get to Cala de Enmedio?",
            "de": "Wie komme ich zur Cala de Enmedio?",
            "fr": "Comment aller à Cala de Enmedio ?",
        },
        {
            "es": "Cala de Enmedio solo es accesible a pie (unos 20-30 min andando desde Agua Amarga) o en kayak. No hay acceso rodado; lleva agua y calzado cómodo.",
            "en": "Cala de Enmedio is only reachable on foot (about 20-30 min walking from Agua Amarga) or by kayak. There is no road access; bring water and comfortable shoes.",
            "de": "Die Cala de Enmedio ist nur zu Fuß (ca. 20-30 Min. von Agua Amarga) oder mit dem Kajak erreichbar. Keine Zufahrt; Wasser und bequeme Schuhe mitnehmen.",
            "fr": "Cala de Enmedio n'est accessible qu'à pied (environ 20-30 min depuis Agua Amarga) ou en kayak. Pas d'accès routier ; prévoyez de l'eau et de bonnes chaussures.",
        },
    ),
    _faq(
        "playa_playazo",
        "playas",
        {
            "es": "¿Qué tiene de especial El Playazo de Rodalquilar?",
            "en": "What is special about El Playazo de Rodalquilar?",
            "de": "Was ist das Besondere am Playazo de Rodalquilar?",
            "fr": "Qu'a de spécial El Playazo de Rodalquilar ?",
        },
        {
            "es": "El Playazo es una playa de fácil acceso junto al Castillo de San Ramón (s. XVIII), con fondos ideales para snorkel. Hay aparcamiento cercano.",
            "en": "El Playazo is an easy-access beach next to the 18th-century San Ramón Castle, with seabeds ideal for snorkelling. Parking is nearby.",
            "de": "El Playazo ist ein leicht zugänglicher Strand neben der Burg San Ramón (18. Jh.), mit idealem Schnorchelgrund. Parkplatz in der Nähe.",
            "fr": "El Playazo est une plage d'accès facile près du château de San Ramón (XVIIIe), avec des fonds idéaux pour le snorkeling. Parking à proximité.",
        },
    ),
    _faq(
        "playa_agua_amarga",
        "playas",
        {
            "es": "¿Cómo es Agua Amarga?",
            "en": "What is Agua Amarga like?",
            "de": "Wie ist Agua Amarga?",
            "fr": "Comment est Agua Amarga ?",
        },
        {
            "es": "Agua Amarga es un pequeño pueblo costero con playa de arena en el casco, ambiente tranquilo y oferta de restaurantes. Muy popular en verano.",
            "en": "Agua Amarga is a small coastal village with a sandy town beach, a relaxed atmosphere and several restaurants. Very popular in summer.",
            "de": "Agua Amarga ist ein kleines Küstendorf mit Sandstrand im Ort, ruhiger Atmosphäre und Restaurants. Im Sommer sehr beliebt.",
            "fr": "Agua Amarga est un petit village côtier avec une plage de sable, une ambiance tranquille et des restaurants. Très prisé en été.",
        },
    ),
    _faq(
        "playas_seguridad_medusas",
        "playas",
        {
            "es": "¿Hay medusas o banderas de aviso en las playas?",
            "en": "Are there jellyfish or warning flags on the beaches?",
            "de": "Gibt es Quallen oder Warnflaggen an den Stränden?",
            "fr": "Y a-t-il des méduses ou des drapeaux d'avertissement sur les plages ?",
        },
        {
            "es": "El estado de las playas y los avisos (banderas) se actualizan en la app municipal y en los tótems. Respeta siempre la bandera roja: prohíbe el baño.",
            "en": "Beach status and flag warnings are updated in the municipal app and on the totems. Always respect the red flag: bathing is forbidden.",
            "de": "Strandzustand und Flaggenwarnungen werden in der städtischen App und an den Totems aktualisiert. Rote Flagge stets beachten: Baden verboten.",
            "fr": "L'état des plages et les drapeaux sont mis à jour dans l'app municipale et sur les totems. Respectez toujours le drapeau rouge : baignade interdite.",
        },
        nivel="media",
    ),
    _faq(
        "playas_nudismo",
        "playas",
        {
            "es": "¿Hay playas nudistas en Cabo de Gata?",
            "en": "Are there nudist beaches in Cabo de Gata?",
            "de": "Gibt es FKK-Strände am Cabo de Gata?",
            "fr": "Y a-t-il des plages naturistes à Cabo de Gata ?",
        },
        {
            "es": "Sí, algunas calas más apartadas como San Pedro o tramos de Genoveses son tradicionalmente de uso nudista, sin regulación específica. Se pide respeto mutuo.",
            "en": "Yes, some remote coves such as San Pedro or sections of Genoveses are traditionally nudist, without specific regulation. Mutual respect is expected.",
            "de": "Ja, einige abgelegene Buchten wie San Pedro oder Abschnitte von Genoveses sind traditionell FKK, ohne besondere Regelung. Gegenseitiger Respekt wird erwartet.",
            "fr": "Oui, certaines criques isolées comme San Pedro ou des sections de Genoveses sont traditionnellement naturistes, sans réglementation. Respect mutuel demandé.",
        },
        nivel="media",
    ),
    # ===================== PARQUE NATURAL =====================
    _faq(
        "parque_reserva_biosfera",
        "parque",
        {
            "es": "¿Qué figuras de protección tiene Cabo de Gata-Níjar?",
            "en": "What protection status does Cabo de Gata-Níjar have?",
            "de": "Welchen Schutzstatus hat Cabo de Gata-Níjar?",
            "fr": "Quels statuts de protection a Cabo de Gata-Níjar ?",
        },
        {
            "es": "Es Parque Natural, Reserva de la Biosfera de la UNESCO, Geoparque Mundial de la UNESCO y zona ZEPA/LIC de la Red Natura 2000.",
            "en": "It is a Natural Park, a UNESCO Biosphere Reserve, a UNESCO Global Geopark and a Natura 2000 SPA/SCI area.",
            "de": "Es ist Naturpark, UNESCO-Biosphärenreservat, globaler UNESCO-Geopark und Natura-2000-Gebiet (ZEPA/LIC).",
            "fr": "C'est un Parc Naturel, une Réserve de Biosphère UNESCO, un Géoparc Mondial UNESCO et une zone Natura 2000 (ZPS/SIC).",
        },
        fuente="UNESCO / Junta de Andalucía",
    ),
    _faq(
        "parque_aves_flamencos",
        "parque",
        {
            "es": "¿Dónde puedo ver flamencos?",
            "en": "Where can I see flamingos?",
            "de": "Wo kann ich Flamingos sehen?",
            "fr": "Où puis-je voir des flamants roses ?",
        },
        {
            "es": "En las Salinas de Cabo de Gata hay observatorios de aves donde es habitual ver flamencos, especialmente de primavera a otoño. El acceso es libre y gratuito.",
            "en": "At the Cabo de Gata Salt Flats there are bird hides where flamingos are commonly seen, especially from spring to autumn. Access is free.",
            "de": "An den Salinen von Cabo de Gata gibt es Vogelbeobachtungshütten, wo man oft Flamingos sieht, vor allem von Frühling bis Herbst. Zugang frei.",
            "fr": "Aux Salines de Cabo de Gata, des observatoires permettent de voir des flamants, surtout du printemps à l'automne. Accès libre et gratuit.",
        },
        fuente="Centro de Visitantes Las Amoladeras",
    ),
    _faq(
        "parque_salinas",
        "parque",
        {
            "es": "¿Qué son las Salinas de Cabo de Gata?",
            "en": "What are the Cabo de Gata Salt Flats?",
            "de": "Was sind die Salinen von Cabo de Gata?",
            "fr": "Que sont les Salines de Cabo de Gata ?",
        },
        {
            "es": "Son salinas en activo y un humedal protegido de gran valor para las aves migratorias. Junto a ellas está la iglesia de Las Salinas y miradores de observación.",
            "en": "They are working salt flats and a protected wetland of great value for migratory birds, with the Las Salinas church and observation points nearby.",
            "de": "Es sind aktive Salinen und ein geschütztes Feuchtgebiet von großem Wert für Zugvögel, mit der Kirche Las Salinas und Beobachtungspunkten.",
            "fr": "Ce sont des salines en activité et une zone humide protégée, précieuse pour les oiseaux migrateurs, avec l'église de Las Salinas et des observatoires.",
        },
    ),
    _faq(
        "parque_faro_cabo_gata",
        "parque",
        {
            "es": "¿Merece la pena ir al Faro de Cabo de Gata?",
            "en": "Is the Cabo de Gata Lighthouse worth visiting?",
            "de": "Lohnt sich der Leuchtturm von Cabo de Gata?",
            "fr": "Le phare de Cabo de Gata vaut-il la visite ?",
        },
        {
            "es": "Sí. El Faro ofrece vistas al Arrecife de las Sirenas y al mirador de la Vela Blanca. Es uno de los enclaves más fotografiados del parque.",
            "en": "Yes. The Lighthouse offers views of the Arrecife de las Sirenas and the Vela Blanca viewpoint. It is one of the most photographed spots in the park.",
            "de": "Ja. Der Leuchtturm bietet Blick auf das Arrecife de las Sirenas und den Aussichtspunkt Vela Blanca. Einer der meistfotografierten Orte des Parks.",
            "fr": "Oui. Le phare offre une vue sur l'Arrecife de las Sirenas et le belvédère de Vela Blanca. L'un des sites les plus photographiés du parc.",
        },
    ),
    _faq(
        "parque_buceo_normativa",
        "parque",
        {
            "es": "¿Se puede bucear en el parque? ¿Hay normas?",
            "en": "Can I dive in the park? Are there rules?",
            "de": "Darf man im Park tauchen? Gibt es Regeln?",
            "fr": "Peut-on plonger dans le parc ? Y a-t-il des règles ?",
        },
        {
            "es": "Sí, hay reserva marina con zonas reguladas. El buceo se realiza con centros autorizados; en algunas áreas hay límites de fondeo y de número de embarcaciones.",
            "en": "Yes, there is a marine reserve with regulated zones. Diving is done through authorised centres; some areas limit anchoring and the number of boats.",
            "de": "Ja, es gibt ein Meeresschutzgebiet mit regulierten Zonen. Tauchen über autorisierte Zentren; in einigen Bereichen sind Ankern und Bootszahl begrenzt.",
            "fr": "Oui, il y a une réserve marine avec des zones régulées. La plongée se fait via des centres agréés ; certaines zones limitent le mouillage et le nombre de bateaux.",
        },
        nivel="media",
    ),
    # ===================== RUTAS Y ACTIVIDADES =====================
    _faq(
        "ruta_minera_rodalquilar",
        "rutas",
        {
            "es": "¿Qué puedo ver en Rodalquilar y su zona minera?",
            "en": "What can I see in Rodalquilar and its mining area?",
            "de": "Was kann ich in Rodalquilar und im Bergbaugebiet sehen?",
            "fr": "Que voir à Rodalquilar et sa zone minière ?",
        },
        {
            "es": "Rodalquilar conserva las antiguas minas de oro, el Jardín Botánico El Albardinal y senderos interpretativos. Es un paisaje volcánico único en Europa.",
            "en": "Rodalquilar preserves the former gold mines, the El Albardinal Botanical Garden and interpretive trails. It is a volcanic landscape unique in Europe.",
            "de": "Rodalquilar bewahrt die ehemaligen Goldminen, den Botanischen Garten El Albardinal und Lehrpfade. Eine in Europa einzigartige Vulkanlandschaft.",
            "fr": "Rodalquilar conserve les anciennes mines d'or, le Jardin Botanique El Albardinal et des sentiers d'interprétation. Un paysage volcanique unique en Europe.",
        },
    ),
    _faq(
        "rutas_dificultad",
        "rutas",
        {
            "es": "¿Las rutas de senderismo son difíciles?",
            "en": "Are the hiking trails difficult?",
            "de": "Sind die Wanderwege schwierig?",
            "fr": "Les sentiers de randonnée sont-ils difficiles ?",
        },
        {
            "es": "Hay rutas para todos los niveles, la mayoría de dificultad baja-media. Lleva agua, gorra y protección solar; hay poca sombra y el calor estival es intenso.",
            "en": "There are trails for all levels, most of low-medium difficulty. Bring water, a hat and sun protection; there is little shade and summer heat is intense.",
            "de": "Es gibt Wege für alle Niveaus, meist leicht bis mittel. Wasser, Hut und Sonnenschutz mitnehmen; wenig Schatten und intensive Sommerhitze.",
            "fr": "Il y a des sentiers pour tous niveaux, la plupart de difficulté faible à moyenne. Prévoyez eau, casquette et protection solaire ; peu d'ombre et forte chaleur estivale.",
        },
    ),
    _faq(
        "actividad_kayak_snorkel",
        "rutas",
        {
            "es": "¿Dónde puedo hacer kayak o snorkel?",
            "en": "Where can I do kayaking or snorkelling?",
            "de": "Wo kann ich Kajak fahren oder schnorcheln?",
            "fr": "Où puis-je faire du kayak ou du snorkeling ?",
        },
        {
            "es": "Hay empresas de actividades en San José, Las Negras y Agua Amarga que ofrecen rutas guiadas de kayak y snorkel por las calas, con material incluido.",
            "en": "Activity companies in San José, Las Negras and Agua Amarga offer guided kayak and snorkelling tours of the coves, equipment included.",
            "de": "Anbieter in San José, Las Negras und Agua Amarga bieten geführte Kajak- und Schnorcheltouren durch die Buchten an, Ausrüstung inklusive.",
            "fr": "Des prestataires à San José, Las Negras et Agua Amarga proposent des sorties guidées de kayak et snorkeling dans les criques, matériel inclus.",
        },
    ),
    _faq(
        "actividad_bici_alquiler",
        "rutas",
        {
            "es": "¿Puedo alquilar bicicletas para la ruta ciclista?",
            "en": "Can I rent bikes for the cycle route?",
            "de": "Kann ich Fahrräder für den Radweg mieten?",
            "fr": "Puis-je louer des vélos pour la voie cyclable ?",
        },
        {
            "es": "Sí, hay alquiler de bicicletas (incluidas eléctricas) en San José y Rodalquilar, ideales para la ruta ciclista Rodalquilar-Albaricoques. Reserva en temporada alta.",
            "en": "Yes, bike rental (including e-bikes) is available in San José and Rodalquilar, ideal for the Rodalquilar-Albaricoques cycle route. Book ahead in high season.",
            "de": "Ja, Fahrradverleih (auch E-Bikes) in San José und Rodalquilar, ideal für den Radweg Rodalquilar-Albaricoques. In der Hochsaison vorab buchen.",
            "fr": "Oui, location de vélos (y compris électriques) à San José et Rodalquilar, idéale pour la voie cyclable Rodalquilar-Albaricoques. Réservez en haute saison.",
        },
    ),
    _faq(
        "astroturismo",
        "rutas",
        {
            "es": "¿Se pueden ver las estrellas? ¿Hay astroturismo?",
            "en": "Can I stargaze? Is there astrotourism?",
            "de": "Kann man Sterne beobachten? Gibt es Astrotourismus?",
            "fr": "Peut-on observer les étoiles ? Y a-t-il de l'astrotourisme ?",
        },
        {
            "es": "Sí. La baja contaminación lumínica del parque lo hace excelente para observar estrellas. Hay empresas que organizan observaciones guiadas, sobre todo en verano.",
            "en": "Yes. The park's low light pollution makes it excellent for stargazing. Some companies run guided night-sky sessions, especially in summer.",
            "de": "Ja. Die geringe Lichtverschmutzung macht den Park ideal zur Sternbeobachtung. Anbieter organisieren geführte Beobachtungen, vor allem im Sommer.",
            "fr": "Oui. La faible pollution lumineuse du parc le rend idéal pour observer les étoiles. Des entreprises organisent des séances guidées, surtout en été.",
        },
    ),
    # ===================== SERVICIOS =====================
    _faq(
        "servicio_wifi",
        "servicios",
        {
            "es": "¿Hay WiFi público gratuito?",
            "en": "Is there free public WiFi?",
            "de": "Gibt es kostenloses öffentliches WLAN?",
            "fr": "Y a-t-il du WiFi public gratuit ?",
        },
        {
            "es": "Sí, hay puntos de WiFi público municipal en varios núcleos y en la Oficina de Turismo. La conexión es gratuita y anonimizada conforme al RGPD.",
            "en": "Yes, there are municipal public WiFi points in several villages and at the Tourist Office. The connection is free and anonymised under GDPR.",
            "de": "Ja, es gibt kommunale öffentliche WLAN-Punkte in mehreren Orten und im Tourismusbüro. Die Verbindung ist kostenlos und DSGVO-konform anonymisiert.",
            "fr": "Oui, des points WiFi publics municipaux existent dans plusieurs villages et à l'Office de Tourisme. Connexion gratuite et anonymisée selon le RGPD.",
        },
    ),
    _faq(
        "servicio_cajeros",
        "servicios",
        {
            "es": "¿Dónde hay cajeros automáticos?",
            "en": "Where are there ATMs?",
            "de": "Wo gibt es Geldautomaten?",
            "fr": "Où y a-t-il des distributeurs ?",
        },
        {
            "es": "Hay cajeros en Níjar pueblo, San José y Campohermoso. En núcleos pequeños y calas puede no haber, así que conviene llevar algo de efectivo.",
            "en": "There are ATMs in Níjar town, San José and Campohermoso. Small villages and coves may have none, so carrying some cash is advisable.",
            "de": "Geldautomaten gibt es in Níjar-Dorf, San José und Campohermoso. In kleinen Orten und Buchten ggf. keine; etwas Bargeld mitnehmen.",
            "fr": "Il y a des distributeurs à Níjar village, San José et Campohermoso. Les petits villages et criques peuvent en manquer ; prévoyez un peu d'espèces.",
        },
        nivel="media",
    ),
    _faq(
        "servicio_farmacia",
        "servicios",
        {
            "es": "¿Dónde hay farmacias?",
            "en": "Where are there pharmacies?",
            "de": "Wo gibt es Apotheken?",
            "fr": "Où y a-t-il des pharmacies ?",
        },
        {
            "es": "Hay farmacias en Níjar pueblo, San José, Campohermoso y San Isidro. Fuera de horario funciona el sistema de farmacia de guardia; consúltalo en la propia farmacia.",
            "en": "There are pharmacies in Níjar town, San José, Campohermoso and San Isidro. Out of hours an on-duty pharmacy rota applies; check at any pharmacy.",
            "de": "Apotheken gibt es in Níjar-Dorf, San José, Campohermoso und San Isidro. Außerhalb der Zeiten gilt der Notdienst; an jeder Apotheke erfragen.",
            "fr": "Il y a des pharmacies à Níjar village, San José, Campohermoso et San Isidro. Hors horaires, une pharmacie de garde fonctionne ; renseignez-vous en pharmacie.",
        },
        nivel="media",
    ),
    _faq(
        "servicio_parking_san_jose",
        "servicios",
        {
            "es": "¿Dónde puedo aparcar en San José?",
            "en": "Where can I park in San José?",
            "de": "Wo kann ich in San José parken?",
            "fr": "Où puis-je me garer à San José ?",
        },
        {
            "es": "San José cuenta con aparcamientos en el pueblo, algunos de pago en temporada alta. Para Genoveses y Mónsul hay un parking regulado y bus lanzadera en verano.",
            "en": "San José has car parks in the village, some paid in high season. For Genoveses and Mónsul there is a regulated car park and a summer shuttle bus.",
            "de": "San José hat Parkplätze im Ort, in der Hochsaison teils kostenpflichtig. Für Genoveses und Mónsul gibt es einen geregelten Parkplatz und im Sommer einen Pendelbus.",
            "fr": "San José dispose de parkings au village, certains payants en haute saison. Pour Genoveses et Mónsul, un parking régulé et une navette en été.",
        },
        nivel="media",
    ),
    _faq(
        "servicio_supermercado",
        "servicios",
        {
            "es": "¿Hay supermercados cerca de las playas?",
            "en": "Are there supermarkets near the beaches?",
            "de": "Gibt es Supermärkte in Strandnähe?",
            "fr": "Y a-t-il des supermarchés près des plages ?",
        },
        {
            "es": "Sí, en San José, Las Negras, Agua Amarga y los núcleos principales hay supermercados y tiendas de alimentación, con horario ampliado en verano.",
            "en": "Yes, in San José, Las Negras, Agua Amarga and the main villages there are supermarkets and grocery shops, with extended hours in summer.",
            "de": "Ja, in San José, Las Negras, Agua Amarga und den Hauptorten gibt es Supermärkte und Lebensmittelgeschäfte, im Sommer mit längeren Öffnungszeiten.",
            "fr": "Oui, à San José, Las Negras, Agua Amarga et les villages principaux il y a des supermarchés et épiceries, avec horaires élargis en été.",
        },
    ),
    _faq(
        "servicio_taxi",
        "servicios",
        {
            "es": "¿Cómo pido un taxi en la zona?",
            "en": "How do I get a taxi in the area?",
            "de": "Wie bekomme ich ein Taxi in der Gegend?",
            "fr": "Comment trouver un taxi dans la région ?",
        },
        {
            "es": "Hay servicio de taxi en los principales núcleos. Conviene reservar por teléfono con antelación, especialmente en temporada alta y para trayectos a las calas.",
            "en": "Taxi service is available in the main villages. Booking by phone in advance is advisable, especially in high season and for trips to the coves.",
            "de": "Taxidienst gibt es in den Hauptorten. Telefonische Vorabreservierung empfohlen, besonders in der Hochsaison und für Fahrten zu den Buchten.",
            "fr": "Un service de taxi existe dans les villages principaux. Réservation téléphonique conseillée, surtout en haute saison et pour les criques.",
        },
        nivel="media",
    ),
    # ===================== GASTRONOMÍA =====================
    _faq(
        "gastronomia_platos",
        "gastronomia",
        {
            "es": "¿Cuáles son los platos típicos de Níjar?",
            "en": "What are the typical dishes of Níjar?",
            "de": "Was sind typische Gerichte aus Níjar?",
            "fr": "Quels sont les plats typiques de Níjar ?",
        },
        {
            "es": "Destacan el pescado fresco y mariscos, la 'gurullos con conejo', el ajo colorao, la pelota (cocido) y los dulces de almendra. Acompáñalo con vino de la tierra.",
            "en": "Highlights include fresh fish and seafood, 'gurullos con conejo', ajo colorao, the 'pelota' stew and almond sweets. Pair it with local wine.",
            "de": "Höhepunkte sind frischer Fisch und Meeresfrüchte, 'gurullos con conejo', Ajo Colorao, der Eintopf 'pelota' und Mandelsüßspeisen. Dazu Wein der Region.",
            "fr": "À découvrir : poisson frais et fruits de mer, 'gurullos con conejo', ajo colorao, le ragoût 'pelota' et les douceurs aux amandes. Avec un vin local.",
        },
    ),
    _faq(
        "gastronomia_horarios",
        "gastronomia",
        {
            "es": "¿A qué hora se come y se cena aquí?",
            "en": "What are the local lunch and dinner times?",
            "de": "Wann isst man hier zu Mittag und zu Abend?",
            "fr": "À quelle heure déjeune-t-on et dîne-t-on ici ?",
        },
        {
            "es": "En general se come de 14:00 a 16:00 y se cena de 21:00 a 23:00. En temporada alta conviene reservar mesa, sobre todo en los pueblos costeros.",
            "en": "Lunch is usually 14:00-16:00 and dinner 21:00-23:00. In high season booking a table is advisable, especially in the coastal villages.",
            "de": "Mittagessen meist 14:00-16:00, Abendessen 21:00-23:00 Uhr. In der Hochsaison Tisch reservieren, vor allem in den Küstendörfern.",
            "fr": "Le déjeuner est généralement 14h-16h et le dîner 21h-23h. En haute saison, réservez une table, surtout dans les villages côtiers.",
        },
    ),
    _faq(
        "gastronomia_vegetariano",
        "gastronomia",
        {
            "es": "¿Hay opciones vegetarianas o veganas?",
            "en": "Are there vegetarian or vegan options?",
            "de": "Gibt es vegetarische oder vegane Optionen?",
            "fr": "Y a-t-il des options végétariennes ou véganes ?",
        },
        {
            "es": "Sí, cada vez más restaurantes ofrecen platos vegetarianos y veganos, especialmente en San José, Las Negras y Agua Amarga. Pregunta por verduras de la huerta local.",
            "en": "Yes, more and more restaurants offer vegetarian and vegan dishes, especially in San José, Las Negras and Agua Amarga. Ask for local garden vegetables.",
            "de": "Ja, immer mehr Restaurants bieten vegetarische und vegane Gerichte, besonders in San José, Las Negras und Agua Amarga. Nach lokalem Gemüse fragen.",
            "fr": "Oui, de plus en plus de restaurants proposent des plats végétariens et véganes, surtout à San José, Las Negras et Agua Amarga. Demandez les légumes locaux.",
        },
        nivel="media",
    ),
    _faq(
        "gastronomia_vino",
        "gastronomia",
        {
            "es": "¿Hay vino o productos locales para comprar?",
            "en": "Is there local wine or products to buy?",
            "de": "Gibt es lokalen Wein oder Produkte zu kaufen?",
            "fr": "Y a-t-il du vin ou des produits locaux à acheter ?",
        },
        {
            "es": "Sí, la zona produce vinos, aceite, miel, tomate 'raf' y dulces artesanos. Los encontrarás en tiendas locales, mercados y en algunas bodegas que ofrecen visitas.",
            "en": "Yes, the area produces wine, olive oil, honey, 'raf' tomato and artisan sweets. Find them in local shops, markets and some wineries offering visits.",
            "de": "Ja, die Region erzeugt Wein, Olivenöl, Honig, 'Raf'-Tomaten und handgemachte Süßigkeiten. In Geschäften, Märkten und einigen Weingütern mit Besuch.",
            "fr": "Oui, la région produit vin, huile d'olive, miel, tomate 'raf' et douceurs artisanales. Dans les boutiques, marchés et certaines caves proposant des visites.",
        },
    ),
    # ===================== ALOJAMIENTO =====================
    _faq(
        "alojamiento_tipos",
        "servicios",
        {
            "es": "¿Qué tipos de alojamiento hay?",
            "en": "What types of accommodation are there?",
            "de": "Welche Unterkunftsarten gibt es?",
            "fr": "Quels types d'hébergement existe-t-il ?",
        },
        {
            "es": "Hay hoteles, apartamentos turísticos, casas rurales, campings y alojamientos con encanto. La oferta es muy variada en San José, Agua Amarga y Níjar pueblo.",
            "en": "There are hotels, tourist apartments, rural houses, campsites and boutique stays. The offer is wide in San José, Agua Amarga and Níjar town.",
            "de": "Es gibt Hotels, Ferienwohnungen, Landhäuser, Campingplätze und charmante Unterkünfte. Großes Angebot in San José, Agua Amarga und Níjar-Dorf.",
            "fr": "Il y a des hôtels, appartements touristiques, maisons rurales, campings et hébergements de charme. Offre variée à San José, Agua Amarga et Níjar village.",
        },
    ),
    _faq(
        "alojamiento_camping",
        "servicios",
        {
            "es": "¿Hay campings en la zona?",
            "en": "Are there campsites in the area?",
            "de": "Gibt es Campingplätze in der Gegend?",
            "fr": "Y a-t-il des campings dans la région ?",
        },
        {
            "es": "Sí, hay campings autorizados en San José y Tau (Los Escullos). Está prohibido acampar libremente dentro del Parque Natural. Reserva en verano.",
            "en": "Yes, there are authorised campsites in San José and Tau (Los Escullos). Free camping inside the Natural Park is forbidden. Book in summer.",
            "de": "Ja, autorisierte Campingplätze in San José und Tau (Los Escullos). Wildcampen im Naturpark ist verboten. Im Sommer reservieren.",
            "fr": "Oui, des campings agréés à San José et Tau (Los Escullos). Le camping sauvage dans le Parc Naturel est interdit. Réservez en été.",
        },
        nivel="media",
    ),
    _faq(
        "alojamiento_temporada",
        "servicios",
        {
            "es": "¿Cuándo conviene reservar alojamiento?",
            "en": "When should I book accommodation?",
            "de": "Wann sollte ich eine Unterkunft buchen?",
            "fr": "Quand réserver un hébergement ?",
        },
        {
            "es": "En julio y agosto la ocupación es muy alta; reserva con varias semanas de antelación. En primavera y otoño hay más disponibilidad y mejores precios.",
            "en": "In July and August occupancy is very high; book several weeks ahead. Spring and autumn offer more availability and better prices.",
            "de": "Im Juli und August ist die Auslastung sehr hoch; Wochen im Voraus buchen. Frühling und Herbst bieten mehr Verfügbarkeit und bessere Preise.",
            "fr": "En juillet-août l'occupation est très élevée ; réservez plusieurs semaines à l'avance. Printemps et automne offrent plus de disponibilités et de meilleurs prix.",
        },
        nivel="media",
    ),
    # ===================== CULTURA Y PATRIMONIO =====================
    _faq(
        "cultura_ceramica_nijar",
        "cultura",
        {
            "es": "¿Dónde puedo comprar cerámica de Níjar?",
            "en": "Where can I buy Níjar pottery?",
            "de": "Wo kann ich Keramik aus Níjar kaufen?",
            "fr": "Où puis-je acheter de la céramique de Níjar ?",
        },
        {
            "es": "En Níjar pueblo, en la Calle Real y el Barrio Alto, hay numerosos talleres y tiendas de cerámica tradicional y jarapas. Muchos permiten ver el proceso artesanal.",
            "en": "In Níjar town, along Calle Real and the Barrio Alto, there are many workshops and shops of traditional pottery and 'jarapas' rugs. Many show the craft process.",
            "de": "In Níjar-Dorf, in der Calle Real und im Barrio Alto, gibt es viele Werkstätten und Läden für traditionelle Keramik und 'Jarapas'. Oft mit Vorführung.",
            "fr": "À Níjar village, Calle Real et Barrio Alto, de nombreux ateliers et boutiques de céramique traditionnelle et de 'jarapas'. Beaucoup montrent le savoir-faire.",
        },
    ),
    _faq(
        "cultura_cortijo_fraile",
        "cultura",
        {
            "es": "¿Qué es el Cortijo del Fraile?",
            "en": "What is the Cortijo del Fraile?",
            "de": "Was ist der Cortijo del Fraile?",
            "fr": "Qu'est-ce que le Cortijo del Fraile ?",
        },
        {
            "es": "Es un cortijo histórico que inspiró 'Bodas de Sangre' de Lorca y escenario de rodajes de cine. Está protegido como BIC; admíralo desde el exterior con respeto.",
            "en": "It is a historic farmhouse that inspired Lorca's 'Blood Wedding' and a film location. Protected as a heritage site (BIC); admire it from outside with respect.",
            "de": "Ein historisches Gehöft, das Lorcas 'Bluthochzeit' inspirierte und Drehort war. Als Kulturgut (BIC) geschützt; bitte respektvoll von außen betrachten.",
            "fr": "Une ferme historique qui a inspiré 'Noces de sang' de Lorca et lieu de tournage. Protégée (BIC) ; admirez-la de l'extérieur avec respect.",
        },
        nivel="media",
    ),
    _faq(
        "cultura_cine_western",
        "cultura",
        {
            "es": "¿Dónde se rodaron las películas del oeste?",
            "en": "Where were the western films shot?",
            "de": "Wo wurden die Westernfilme gedreht?",
            "fr": "Où ont été tournés les westerns ?",
        },
        {
            "es": "El desierto de Tabernas (cerca de Níjar) y parajes del Cabo de Gata fueron escenario de muchos 'spaghetti westerns'. Hay poblados del oeste visitables en Tabernas.",
            "en": "The Tabernas Desert (near Níjar) and Cabo de Gata spots hosted many 'spaghetti westerns'. There are visitable western towns in Tabernas.",
            "de": "Die Wüste von Tabernas (bei Níjar) und Orte am Cabo de Gata waren Kulisse vieler 'Spaghetti-Western'. In Tabernas gibt es besuchbare Westernstädte.",
            "fr": "Le désert de Tabernas (près de Níjar) et des sites de Cabo de Gata ont accueilli de nombreux 'westerns spaghetti'. Villages western visitables à Tabernas.",
        },
    ),
    _faq(
        "cultura_mercadillo",
        "cultura",
        {
            "es": "¿Hay mercadillos artesanales?",
            "en": "Are there craft markets?",
            "de": "Gibt es Kunsthandwerksmärkte?",
            "fr": "Y a-t-il des marchés artisanaux ?",
        },
        {
            "es": "Sí, hay mercadillos semanales y mercados artesanales, especialmente en verano. Las fechas y ubicaciones se publican en la agenda municipal y en este tótem.",
            "en": "Yes, there are weekly and craft markets, especially in summer. Dates and locations are published in the municipal calendar and on this totem.",
            "de": "Ja, es gibt Wochen- und Kunsthandwerksmärkte, vor allem im Sommer. Termine und Orte stehen im Veranstaltungskalender und auf diesem Totem.",
            "fr": "Oui, des marchés hebdomadaires et artisanaux, surtout en été. Dates et lieux publiés dans l'agenda municipal et sur ce totem.",
        },
        nivel="media",
    ),
    # ===================== EVENTOS =====================
    _faq(
        "eventos_fiestas_san_jose",
        "eventos",
        {
            "es": "¿Cuándo son las fiestas de San José?",
            "en": "When are the San José festivities?",
            "de": "Wann sind die Feste von San José?",
            "fr": "Quand ont lieu les fêtes de San José ?",
        },
        {
            "es": "San José celebra sus fiestas patronales en torno al 19 de marzo, y en verano hay fiestas y verbenas en los distintos núcleos. Consulta la agenda actualizada en el tótem.",
            "en": "San José holds its patron festivities around 19 March, and in summer there are local fiestas across the villages. Check the updated calendar on the totem.",
            "de": "San José feiert sein Patronatsfest um den 19. März, im Sommer gibt es Feste in den Orten. Aktuellen Kalender am Totem prüfen.",
            "fr": "San José fête son saint patron autour du 19 mars ; en été, fêtes locales dans les villages. Consultez l'agenda à jour sur le totem.",
        },
        nivel="media",
    ),
    _faq(
        "eventos_conciertos_verano",
        "eventos",
        {
            "es": "¿Hay conciertos o cine de verano?",
            "en": "Are there concerts or summer cinema?",
            "de": "Gibt es Konzerte oder Sommerkino?",
            "fr": "Y a-t-il des concerts ou du cinéma d'été ?",
        },
        {
            "es": "En verano se programan conciertos, cine al aire libre y actividades culturales. La programación detallada se publica en la agenda municipal y aquí en el tótem.",
            "en": "In summer there are concerts, open-air cinema and cultural activities. The detailed programme is published in the municipal calendar and here on the totem.",
            "de": "Im Sommer gibt es Konzerte, Open-Air-Kino und Kulturprogramm. Das Detailprogramm steht im städtischen Kalender und hier am Totem.",
            "fr": "En été : concerts, cinéma en plein air et activités culturelles. Le programme détaillé est publié dans l'agenda municipal et ici sur le totem.",
        },
        nivel="media",
    ),
    # ===================== TRANSPORTE =====================
    _faq(
        "transporte_aeropuerto",
        "servicios",
        {
            "es": "¿Cómo llego desde el aeropuerto de Almería?",
            "en": "How do I get here from Almería airport?",
            "de": "Wie komme ich vom Flughafen Almería hierher?",
            "fr": "Comment venir depuis l'aéroport d'Almería ?",
        },
        {
            "es": "El aeropuerto de Almería (LEI) está a unos 30-40 min en coche. Lo más cómodo es alquilar coche; también hay taxis y conexiones de autobús con transbordo en Almería.",
            "en": "Almería airport (LEI) is about 30-40 min by car. Renting a car is most convenient; there are also taxis and bus connections with a transfer in Almería.",
            "de": "Der Flughafen Almería (LEI) ist ca. 30-40 Min. mit dem Auto entfernt. Am bequemsten ist ein Mietwagen; auch Taxis und Busverbindungen mit Umstieg in Almería.",
            "fr": "L'aéroport d'Almería (LEI) est à 30-40 min en voiture. Le plus pratique est la location de voiture ; aussi taxis et bus avec correspondance à Almería.",
        },
    ),
    _faq(
        "transporte_distancias",
        "servicios",
        {
            "es": "¿A qué distancia están las playas del pueblo de Níjar?",
            "en": "How far are the beaches from Níjar town?",
            "de": "Wie weit sind die Strände vom Dorf Níjar entfernt?",
            "fr": "À quelle distance sont les plages du village de Níjar ?",
        },
        {
            "es": "El casco de Níjar está a unos 25-35 km de las playas del litoral (San José, Mónsul, Genoveses). En coche son 30-45 min por carreteras de montaña.",
            "en": "Níjar town is about 25-35 km from the coastal beaches (San José, Mónsul, Genoveses). By car it is 30-45 min on mountain roads.",
            "de": "Níjar-Dorf liegt ca. 25-35 km von den Küstenstränden (San José, Mónsul, Genoveses) entfernt. Mit dem Auto 30-45 Min. über Bergstraßen.",
            "fr": "Le village de Níjar est à 25-35 km des plages (San José, Mónsul, Genoveses). En voiture, 30-45 min par routes de montagne.",
        },
    ),
    _faq(
        "transporte_bus_lanzadera",
        "servicios",
        {
            "es": "¿Existe bus lanzadera a las playas en verano?",
            "en": "Is there a summer shuttle bus to the beaches?",
            "de": "Gibt es im Sommer einen Pendelbus zu den Stränden?",
            "fr": "Y a-t-il une navette estivale vers les plages ?",
        },
        {
            "es": "Sí. En temporada alta funciona un bus lanzadera desde San José a Mónsul y Genoveses para reducir el tráfico. Consulta horarios y paradas en el tótem o la app.",
            "en": "Yes. In high season a shuttle bus runs from San José to Mónsul and Genoveses to reduce traffic. Check times and stops on the totem or app.",
            "de": "Ja. In der Hochsaison fährt ein Pendelbus von San José nach Mónsul und Genoveses, um Verkehr zu reduzieren. Zeiten und Halte am Totem oder in der App.",
            "fr": "Oui. En haute saison, une navette relie San José à Mónsul et Genoveses pour réduire le trafic. Horaires et arrêts sur le totem ou l'app.",
        },
        nivel="media",
    ),
    # ===================== ACCESIBILIDAD =====================
    _faq(
        "accesibilidad_silla_anfibia",
        "accesibilidad",
        {
            "es": "¿Hay sillas anfibias o baño asistido para personas con movilidad reducida?",
            "en": "Are there amphibious chairs or assisted bathing for reduced mobility?",
            "de": "Gibt es Amphibienstühle oder Badehilfe für Menschen mit eingeschränkter Mobilität?",
            "fr": "Y a-t-il des fauteuils amphibies ou un bain assisté pour mobilité réduite ?",
        },
        {
            "es": "Algunas playas accesibles disponen de sillas anfibias y puntos de baño asistido en temporada. Consulta disponibilidad y horarios en la Oficina de Turismo.",
            "en": "Some accessible beaches provide amphibious chairs and assisted bathing points in season. Check availability and hours at the Tourist Office.",
            "de": "Einige barrierefreie Strände bieten in der Saison Amphibienstühle und Badehilfe. Verfügbarkeit und Zeiten im Tourismusbüro erfragen.",
            "fr": "Certaines plages accessibles offrent des fauteuils amphibies et un bain assisté en saison. Vérifiez disponibilité et horaires à l'Office de Tourisme.",
        },
    ),
    _faq(
        "accesibilidad_perro_guia",
        "accesibilidad",
        {
            "es": "¿Puedo acceder con perro guía o de asistencia?",
            "en": "Can I enter with a guide or assistance dog?",
            "de": "Darf ich mit einem Blinden- oder Assistenzhund hinein?",
            "fr": "Puis-je entrer avec un chien guide ou d'assistance ?",
        },
        {
            "es": "Sí. Los perros guía y de asistencia están permitidos en playas y establecimientos públicos durante todo el año, conforme a la legislación vigente.",
            "en": "Yes. Guide and assistance dogs are allowed on beaches and in public premises all year round, in accordance with current law.",
            "de": "Ja. Blinden- und Assistenzhunde sind ganzjährig an Stränden und in öffentlichen Einrichtungen erlaubt, gemäß geltendem Recht.",
            "fr": "Oui. Les chiens guides et d'assistance sont autorisés sur les plages et dans les lieux publics toute l'année, conformément à la loi.",
        },
    ),
    _faq(
        "accesibilidad_totem_bucle",
        "accesibilidad",
        {
            "es": "¿El tótem es accesible para personas con discapacidad auditiva o visual?",
            "en": "Is the totem accessible for people with hearing or visual impairment?",
            "de": "Ist das Totem für Menschen mit Hör- oder Sehbehinderung zugänglich?",
            "fr": "Le totem est-il accessible aux personnes malentendantes ou malvoyantes ?",
        },
        {
            "es": "Sí. Este tótem dispone de bucle de inducción magnética, texto ampliable, alto contraste y asistente por voz (entrada y lectura), conforme a WCAG 2.1 AA.",
            "en": "Yes. This totem has a magnetic induction loop, enlargeable text, high contrast and a voice assistant (input and read-out), compliant with WCAG 2.1 AA.",
            "de": "Ja. Dieses Totem bietet eine Induktionsschleife, vergrößerbaren Text, hohen Kontrast und Sprachassistenz (Eingabe und Vorlesen), gemäß WCAG 2.1 AA.",
            "fr": "Oui. Ce totem dispose d'une boucle magnétique, d'un texte agrandissable, d'un fort contraste et d'un assistant vocal (saisie et lecture), conforme WCAG 2.1 AA.",
        },
    ),
    # ===================== INFORMACIÓN PRÁCTICA =====================
    _faq(
        "practico_clima",
        "general",
        {
            "es": "¿Qué tiempo hace en Cabo de Gata?",
            "en": "What is the weather like in Cabo de Gata?",
            "de": "Wie ist das Wetter am Cabo de Gata?",
            "fr": "Quel temps fait-il à Cabo de Gata ?",
        },
        {
            "es": "Es de los lugares más secos y soleados de Europa, con unos 3.000 horas de sol al año. Veranos calurosos e inviernos suaves; lleva siempre protección solar y agua.",
            "en": "It is one of Europe's driest and sunniest spots, with around 3,000 hours of sun a year. Hot summers and mild winters; always carry sun protection and water.",
            "de": "Einer der trockensten und sonnigsten Orte Europas, ca. 3.000 Sonnenstunden im Jahr. Heiße Sommer, milde Winter; immer Sonnenschutz und Wasser mitnehmen.",
            "fr": "L'un des endroits les plus secs et ensoleillés d'Europe, environ 3 000 heures de soleil par an. Étés chauds, hivers doux ; emportez protection solaire et eau.",
        },
    ),
    _faq(
        "practico_agua_potable",
        "general",
        {
            "es": "¿Hay agua potable en las playas y calas?",
            "en": "Is there drinking water at the beaches and coves?",
            "de": "Gibt es Trinkwasser an den Stränden und Buchten?",
            "fr": "Y a-t-il de l'eau potable sur les plages et criques ?",
        },
        {
            "es": "En muchas calas vírgenes no hay fuentes ni servicios. Lleva agua suficiente, especialmente en verano, y recoge siempre tus residuos al salir.",
            "en": "Many unspoilt coves have no fountains or facilities. Bring enough water, especially in summer, and always take your litter with you.",
            "de": "Viele unberührte Buchten haben weder Brunnen noch Einrichtungen. Genug Wasser mitnehmen, besonders im Sommer, und Müll stets wieder mitnehmen.",
            "fr": "De nombreuses criques sauvages n'ont ni fontaines ni services. Emportez assez d'eau, surtout en été, et reprenez toujours vos déchets.",
        },
    ),
    _faq(
        "practico_idiomas",
        "general",
        {
            "es": "¿Se habla inglés u otros idiomas en la zona?",
            "en": "Is English or other languages spoken in the area?",
            "de": "Wird in der Gegend Englisch oder andere Sprachen gesprochen?",
            "fr": "Parle-t-on anglais ou d'autres langues dans la région ?",
        },
        {
            "es": "En zonas turísticas es habitual la atención en inglés y, a menudo, en francés o alemán. Este asistente y los tótems funcionan en español, inglés, alemán y francés.",
            "en": "In tourist areas English is common, and often French or German too. This assistant and the totems work in Spanish, English, German and French.",
            "de": "In touristischen Gebieten ist Englisch üblich, oft auch Französisch oder Deutsch. Dieser Assistent und die Totems funktionieren auf Spanisch, Englisch, Deutsch und Französisch.",
            "fr": "Dans les zones touristiques, l'anglais est courant, souvent aussi le français ou l'allemand. Cet assistant et les totems fonctionnent en espagnol, anglais, allemand et français.",
        },
    ),
    _faq(
        "practico_sostenibilidad",
        "parque",
        {
            "es": "¿Cómo puedo visitar el parque de forma responsable?",
            "en": "How can I visit the park responsibly?",
            "de": "Wie besuche ich den Park verantwortungsvoll?",
            "fr": "Comment visiter le parc de façon responsable ?",
        },
        {
            "es": "No salgas de los senderos, no recojas plantas ni minerales, no dejes residuos, respeta la fauna y el aforo de las playas, y reduce el uso del coche cuando puedas.",
            "en": "Stay on the trails, do not pick plants or minerals, leave no litter, respect wildlife and beach capacity, and reduce car use when possible.",
            "de": "Auf den Wegen bleiben, keine Pflanzen oder Mineralien sammeln, keinen Müll hinterlassen, Tierwelt und Strandkapazität respektieren und Autofahrten reduzieren.",
            "fr": "Restez sur les sentiers, ne cueillez ni plantes ni minéraux, ne laissez aucun déchet, respectez la faune et la capacité des plages, et limitez la voiture.",
        },
    ),
    # ===================== EMERGENCIAS (alta confianza obligatoria) =====================
    _faq(
        "emergencia_incendio",
        "emergencias",
        {
            "es": "¿Qué hago si veo un incendio forestal?",
            "en": "What do I do if I see a wildfire?",
            "de": "Was tue ich, wenn ich einen Waldbrand sehe?",
            "fr": "Que faire si je vois un feu de forêt ?",
        },
        {
            "es": "Llama de inmediato al 112. Aléjate del fuego en dirección contraria al viento, no intentes apagarlo tú y sigue las indicaciones de las autoridades.",
            "en": "Call 112 immediately. Move away from the fire, upwind, do not try to put it out yourself and follow the authorities' instructions.",
            "de": "Sofort 112 anrufen. Vom Feuer weg, gegen den Wind, nicht selbst löschen und den Anweisungen der Behörden folgen.",
            "fr": "Appelez immédiatement le 112. Éloignez-vous du feu, face au vent, n'essayez pas de l'éteindre et suivez les consignes des autorités.",
        },
    ),
    _faq(
        "emergencia_rescate_costa",
        "emergencias",
        {
            "es": "¿A quién llamo ante una emergencia en el mar o en una cala?",
            "en": "Who do I call for an emergency at sea or in a cove?",
            "de": "Wen rufe ich bei einem Notfall im Meer oder in einer Bucht an?",
            "fr": "Qui appeler en cas d'urgence en mer ou dans une crique ?",
        },
        {
            "es": "Llama al 112 (emergencias generales) o a Salvamento Marítimo (900 202 202). Indica el nombre de la cala o un punto de referencia para localizarte rápido.",
            "en": "Call 112 (general emergencies) or Maritime Rescue (900 202 202). Give the cove name or a landmark so they can locate you quickly.",
            "de": "Rufen Sie 112 (allgemeine Notfälle) oder die Seenotrettung (900 202 202) an. Nennen Sie den Namen der Bucht oder einen Bezugspunkt zur schnellen Ortung.",
            "fr": "Appelez le 112 (urgences générales) ou le Sauvetage en mer (900 202 202). Indiquez le nom de la crique ou un repère pour vous localiser vite.",
        },
    ),
    _faq(
        "emergencia_documentos_perdidos",
        "emergencias",
        {
            "es": "He perdido la documentación o me han robado, ¿qué hago?",
            "en": "I lost my documents or was robbed, what do I do?",
            "de": "Ich habe meine Dokumente verloren oder wurde bestohlen, was tun?",
            "fr": "J'ai perdu mes papiers ou on m'a volé, que faire ?",
        },
        {
            "es": "Denúncialo ante la Guardia Civil (062) o en el puesto más cercano. Para emergencias generales, 112. Si eres extranjero, contacta también con tu consulado.",
            "en": "Report it to the Guardia Civil (062) or the nearest post. For general emergencies, 112. If you are a foreign visitor, also contact your consulate.",
            "de": "Bei der Guardia Civil (062) oder der nächsten Dienststelle anzeigen. Allgemeine Notfälle: 112. Als ausländischer Gast auch das Konsulat kontaktieren.",
            "fr": "Signalez-le à la Guardia Civil (062) ou au poste le plus proche. Urgences générales : 112. Si vous êtes étranger, contactez aussi votre consulat.",
        },
    ),
    # ===================== META / CHATBOT =====================
    _faq(
        "meta_que_puedes_hacer",
        "general",
        {
            "es": "¿Qué puedes hacer por mí?",
            "en": "What can you do for me?",
            "de": "Was kannst du für mich tun?",
            "fr": "Que peux-tu faire pour moi ?",
        },
        {
            "es": "Puedo informarte sobre playas, rutas, el parque natural, eventos, servicios y emergencias, proponerte una ruta cercana y recomendarte qué visitar hoy. ¿Por dónde empezamos?",
            "en": "I can tell you about beaches, trails, the natural park, events, services and emergencies, suggest a nearby route and recommend what to visit today. Where shall we start?",
            "de": "Ich informiere über Strände, Wege, den Naturpark, Veranstaltungen, Dienste und Notfälle, schlage eine Route in der Nähe vor und empfehle Ausflüge für heute. Womit fangen wir an?",
            "fr": "Je peux vous renseigner sur les plages, sentiers, le parc naturel, événements, services et urgences, proposer un itinéraire proche et recommander quoi visiter aujourd'hui. Par où commencer ?",
        },
    ),
    _faq(
        "meta_idiomas_chatbot",
        "general",
        {
            "es": "¿En qué idiomas puedes atenderme?",
            "en": "Which languages can you assist me in?",
            "de": "In welchen Sprachen kannst du mir helfen?",
            "fr": "Dans quelles langues peux-tu m'aider ?",
        },
        {
            "es": "Puedo atenderte en español, inglés, alemán y francés. Cambia el idioma con los botones del tótem y te responderé en el idioma seleccionado.",
            "en": "I can assist you in Spanish, English, German and French. Switch language with the totem buttons and I will reply in the selected language.",
            "de": "Ich helfe auf Spanisch, Englisch, Deutsch und Französisch. Sprache mit den Totem-Tasten wechseln, dann antworte ich in der gewählten Sprache.",
            "fr": "Je peux vous aider en espagnol, anglais, allemand et français. Changez de langue avec les boutons du totem et je répondrai dans la langue choisie.",
        },
    ),
    _faq(
        "meta_agradecimiento",
        "general",
        {"es": "¡Gracias!", "en": "Thank you!", "de": "Danke!", "fr": "Merci !"},
        {
            "es": "¡De nada! Que disfrutes mucho de Cabo de Gata-Níjar. Si necesitas algo más, aquí estoy.",
            "en": "You're welcome! Enjoy Cabo de Gata-Níjar. If you need anything else, I'm here.",
            "de": "Gern geschehen! Viel Freude in Cabo de Gata-Níjar. Wenn Sie noch etwas brauchen, bin ich da.",
            "fr": "Avec plaisir ! Profitez bien de Cabo de Gata-Níjar. Si vous avez besoin d'autre chose, je suis là.",
        },
    ),
]
