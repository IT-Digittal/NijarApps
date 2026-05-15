# Modelo semántico — Plataforma DTI Níjar

Modelo basado en **FIWARE Smart Data Models** adaptado al contexto del destino turístico de Níjar (Cabo de Gata, ruta Rodalquilar–Albaricoques).

## Principios

1. **URN único por entidad** con formato `urn:ngsi-ld:<EntityType>:nijar:<slug-o-id>`.
2. **Coordenadas en WGS84** (EPSG:4326), formato GeoJSON `Point`, `Polygon` o `LineString`.
3. **Multilingüe** mediante diccionarios `{ "es": "...", "en": "...", "de": "...", "fr": "..." }`.
4. **Trazabilidad de linaje** (origen, fecha de captura, transformaciones) en cada registro analítico.
5. **Anonimización RGPD** estricta para datos de visitantes (hash SHA-256 de identificadores).

## Entidades principales

| Entidad | Equivalente FIWARE | Propósito |
|---------|--------------------|-----------|
| `RecursoTuristico` | `PointOfInterest`, `TouristAttraction` | Playas, monumentos, rutas, miradores, museos |
| `EventoTuristico` | `Event` | Eventos programados en el destino |
| `Servicio` | extensión propia | Alojamiento, gastronomía, ocio, comercio |
| `Sensor` | `Device` | Catálogo de sensores IoT |
| `Observacion` | `AirQualityObserved`, `WeatherObserved` | Lecturas puntuales de sensores |
| `Visita` | extensión propia | Interacciones de visitantes (tótem, beacon, chatbot) |
| `Opinion` | extensión propia | Menciones del destino en RRSS y reseñas |
| `Usuario` | — | Cuentas de acceso a la plataforma (RBAC) |

## Esquemas JSON Schema

Cada entidad tiene su esquema en [`schemas/`](schemas/). Los esquemas son la fuente de verdad para:

- Validación de payloads en la API
- Documentación de la API en OpenAPI
- Generación de modelos Pydantic
- Compatibilidad con FIWARE NGSI-LD

## Vocabulario controlado

Categorías y enumeraciones definidas en los modelos SQLAlchemy ([`src/nijar_dti/models/`](../../src/nijar_dti/models/)) y replicadas en los JSON Schemas. Cualquier extensión del vocabulario debe documentarse aquí y validarse con el responsable municipal.

## Coordenadas geográficas relevantes (Níjar)

| Lugar | Latitud | Longitud |
|-------|---------|----------|
| Casco urbano de Níjar | 36.965 | -2.207 |
| Rodalquilar (inicio ruta) | 36.853 | -2.052 |
| Albaricoques (fin ruta) | 36.879 | -2.108 |
| Centro Visitantes Las Amoladeras | 36.825 | -2.282 |
| Playa de los Genoveses | 36.778 | -2.130 |
| Playa de Mónsul | 36.752 | -2.139 |

## Datasets abiertos

Compromiso del contrato (Memoria Técnica §6.7): **publicación de ≥ 5 datasets abiertos** bajo licencia CC BY 4.0. Datasets candidatos:

1. Catálogo de recursos turísticos publicados.
2. Calendario de eventos turísticos.
3. Datos meteorológicos agregados (medias diarias).
4. KPIs de uso digital del destino.
5. Estadísticas anonimizadas de afluencia.
