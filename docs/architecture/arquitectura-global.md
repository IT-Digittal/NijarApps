# Arquitectura global — Plataforma DTI Níjar

**Expediente:** 18962/2025
**Versión:** 0.1 (Hito 1 — entregable preliminar)
**Estándar de referencia:** UNE 178104:2017 «Sistemas Integrales de Gestión de la Ciudad Inteligente»

---

## 1. Visión general

La Plataforma DTI Níjar es el **núcleo troncal e integrador** de los servicios Smart City del destino turístico de Níjar. Actúa como sistema nervioso central que conecta los subsistemas existentes (web turística, app Vive Níjar, sensores IoT, beacons, alumbrado, videocámaras, estaciones meteorológicas) con los nuevos componentes de este contrato (tótems, chatbot IA, Big Data, Smart Office, CMS centralizado).

Se diseña como **arquitectura modular de tres capas** conforme a UNE 178104, garantizando interoperabilidad, seguridad, sostenibilidad operativa y la incorporación futura de nuevos verticales Smart City sin rediseñar el núcleo.

## 2. Capas de la arquitectura

### Capa de adquisición

Recibe datos heterogéneos del entorno físico y digital del destino:

- **Sensores ambientales** (CO₂, temperatura, humedad, ruido) en el Smart Office y ubicaciones turísticas → MQTT con certificado y whitelist.
- **Estaciones meteorológicas** municipales → REST/JSON polling horario.
- **Beacons BLE** → eventos de proximidad vía SDK de la app Vive Níjar.
- **WiFi público** → conexiones anonimizadas (hash MAC, RGPD), agregación batch diaria.
- **APIs de redes sociales** (X, Facebook, Instagram, TripAdvisor) → polling 5–15 min.
- **Facebook/Instagram municipal** → publicaciones oficiales como fuente de contenidos para chatbot y CMS.
- **Analítica web/app** → integración con Google Analytics 4 Data API.
- **Formularios ciudadanos** → encuestas insertadas en la web municipal.

### Capa de plataforma (núcleo DTI)

Centro de procesamiento y exposición de servicios compartidos:

- **Bus de eventos pub/sub** — notificaciones en tiempo real (alertas de aforo, banderas de playa, avisos, cambios de contenido).
- **CMS centralizado** — publicación multicanal con caché e invalidación por eventos (latencia comprometida < 5 min hacia tótems, web y app).
- **Motor NLP/IA** — procesamiento del lenguaje natural, detección de intenciones, control de alucinaciones en cuatro niveles (restricción de dominio, trazabilidad de fuentes, umbral de confianza, revisión humana mensual ISO 42001).
- **Motor Big Data y analítica** — ETL/ELT, análisis de sentimiento NLP, modelos predictivos, segmentación, detección de anomalías.
- **Módulo GIS** — geoposicionamiento, mapas de calor, alertas geolocalizadas (WGS84 / GeoJSON).
- **Modelo semántico FIWARE** — entidades normalizadas (`RecursoTuristico`, `EventoTuristico`, `Servicio`, `Sensor`, `Observacion`, `Visita`, `Opinion`).
- **Seguridad transversal** — RBAC, TLS 1.2+, AES-256, SIEM, WAF, EDR, gestión de certificados SSL/TLS.

### Capa de consumo

Aplicaciones y módulos frontales con los que interactúan turistas, ciudadanos y gestores municipales:

- **Tótems interactivos** (2 unidades en ruta Rodalquilar–Albaricoques) — interfaz táctil multilingüe con agente IA por voz y mapas integrados.
- **Panel Smart Office** — dashboards operativos con KPIs en tiempo real, alertas configurables, informes PDF/Excel programados.
- **Chatbot IA 24/7** — asistente de turismo multicanal (web, app, tótems) accesible WCAG AA.
- **Web turística + App Vive Níjar** — aplicaciones existentes integradas vía APIs.
- **Dashboards Big Data** — Social Listening, sentimiento, mapas de calor, share of voice, eficacia de campañas.

## 3. Principios de diseño

| Principio | Aplicación concreta |
|-----------|---------------------|
| **Interoperabilidad** | APIs REST/JSON con OpenAPI 3.1 versionada, modelo semántico FIWARE, formatos abiertos (JSON, GeoJSON, CSV) |
| **Soberanía del dato** | Hosting cloud en UE (RGPD); credenciales propiedad del Ayuntamiento; portabilidad total al fin del contrato |
| **Privilegio mínimo** | RBAC con 5 perfiles; 2FA para administradores; tokens OAuth2 con scopes restringidos |
| **Seguridad por diseño** | ENS Medio desde el primer despliegue; hardening, pentest, SIEM, WAF, EDR |
| **Accesibilidad universal** | WCAG 2.1 AA en todos los canales; bucle magnético en tótems; lectura fácil; voz |
| **Sostenibilidad operativa** | Equipos eficientes, plan DNSH, ciclos de mantenimiento preventivo, residuos electrónicos gestionados |
| **Extensibilidad** | Patrón estandarizado de 3 pasos para añadir verticales (parking, residuos, movilidad…) sin rediseñar el núcleo |
| **Sin bloqueo tecnológico** | APIs versionadas, formatos abiertos, código entregable, alternativas documentadas para cualquier componente propietario |

## 4. Flujos de datos principales

| Flujo | Origen → Plataforma | Procesamiento | Plataforma → Destino |
|-------|---------------------|---------------|----------------------|
| **IoT → Dashboard** | Sensores MQTT publican observaciones; conector valida rango y duplicados; almacenamiento en modelo semántico | Motor de reglas evalúa umbrales → evento pub/sub si se superan; motor analítico calcula tendencias | Dashboard Smart Office vía REST + WebSocket; alertas correo/SMS |
| **RRSS → Big Data** | Conectores consultan APIs X/FB/IG cada 5–15 min; extraen texto, autor, fecha, métricas, geolocalización | NLP clasifica sentimiento y tema; calcula KPIs; almacena en data lake | Dashboards Big Data con nubes de palabras, mapas de calor, series temporales; informes PDF mensuales |
| **CMS → Canales** | Editor municipal publica contenido multilingüe con imágenes y coordenadas GIS | Evento de publicación en bus; caché invalidada; contenido disponible en < 5 min | Tótems, web y app muestran contenido sincronizado; chatbot incorpora dato a su base de conocimiento |
| **Usuario → Chatbot** | Visitante pregunta en web/app/tótem (texto o voz); NLP identifica intención y entidades | Motor consulta base de conocimiento con niveles de confianza; si match alto → responde con fuente trazable; si bajo → fallback educado | Respuesta en canal del usuario; log estructurado a telemetría |
| **Tótem → Monitorización** | Heartbeat cada 60 s con estado, temperatura, red, interacciones | Si heartbeat falta > 3 min → alerta offline; temperatura > 45 °C → alerta sobrecalentamiento | Consola con semáforo por tótem; reinicio remoto; encendido/apagado programado |

## 5. Integraciones con sistemas existentes

| Sistema | Tipo | Endpoint | Cadencia | Dirección |
|---------|------|----------|----------|-----------|
| App Vive Níjar | SDK móvil + REST | `/api/v1/tourism/*` | Tiempo real | Bidireccional |
| Web turística | REST + widget JS | `/api/v1/content/*` | Eventos + polling | Bidireccional |
| Beacons BLE | SDK app → REST | `/api/v1/data/iot/ingest` | Evento | Entrada |
| Red WiFi pública | Export CSV / API | `/api/wifi/stats` | Diaria batch | Entrada |
| Sensores ambientales | MQTT | broker MQTT | 60 s | Entrada |
| Estaciones meteo | REST | `/api/meteo/current` | Horaria | Entrada |
| Alumbrado eficiente | API fabricante | adaptador REST | 5 min | Entrada |
| Videocámaras | API fabricante / RTSP | procesador de conteo | Tiempo real | Entrada |
| Facebook/Instagram (Ayto.) | Graph API | webhook + polling | Diaria | Entrada |

## 6. Despliegue

- **Producción** — cloud con datacenter en UE (RGPD), escalado vertical y horizontal sin interrupción.
- **Staging** — entorno preproductivo aislado para pruebas y validación.
- **Desarrollo** — `docker-compose` local con API + PostgreSQL/PostGIS + Redis + MQTT.

Detalles de infraestructura en [`decisiones-tecnicas.md`](decisiones-tecnicas.md) (ADR-005).

## 7. Cumplimiento normativo

| Norma / Marco | Aplicación |
|---------------|------------|
| **UNE 178104:2017** | Plataforma de ciudad inteligente — interoperabilidad |
| **UNE 178501/178502:2019** | Indicadores y herramientas de Destinos Turísticos Inteligentes |
| **ENS Nivel Medio (RD 311/2022)** | Esquema Nacional de Seguridad |
| **RGPD + LOPDGDD** | Protección de datos personales |
| **WCAG 2.1 AA** | Accesibilidad digital |
| **DNSH** | "Do No Significant Harm" — sostenibilidad ambiental PRTR |
| **ISO 9001 / 14001 / 27001 / 42001 / 45001** | Sistema integrado de gestión IT DIGITTAL |

## 8. Trazabilidad: necesidad → solución → indicador

| Necesidad de Níjar | Solución | Indicador medible |
|--------------------|----------|---------------------|
| Sin información digital en ruta ni litoral | 2 tótems interactivos con agente IA | CTR ≥ 10 %; ≥ 100 consultas IA/mes |
| Atención limitada a horario y español | Chatbot multicanal NLP avanzado | Resolución autónoma ≥ 80 %; satisfacción ≥ 80 % |
| Decisiones sin soporte de datos | Big Data + Social Listening + dashboards | ≥ 10 KPIs activos; precisión sentimiento ≥ 80 % |
| Estacionalidad concentrada | CMS dinámico + tótems + chatbot | Incremento ≥ 15 % consultas fuera de temporada |
| IoT aislado | Plataforma integradora única | 100 % verticales integrados; latencia ≤ 15 min |
| Sin hoja de ruta digital | Plan Director DTI > 80 pág. | ≥ 10 actuaciones priorizadas |
| Sin marco de seguridad | Plan ciberseguridad ENS Medio + pentest | Cumplimiento ENS evidenciado; críticas ≤ 8 h |

## 9. Diagrama de bloques (referencia)

Ver Anexo A3-1 de la Memoria Técnica para el diagrama de arquitectura global.

```
┌──────────────────────────────────────────────────────────────────────┐
│                       CAPA DE CONSUMO                                 │
│ ┌────────┐ ┌─────────┐ ┌─────────┐ ┌───────────┐ ┌───────────────┐ │
│ │ Tótems │ │ Smart   │ │ Chatbot │ │ Web + App │ │ Dashboards BD │ │
│ │   IA   │ │ Office  │ │  24/7   │ │Vive Níjar │ │  Social List. │ │
│ └────┬───┘ └────┬────┘ └────┬────┘ └─────┬─────┘ └───────┬───────┘ │
└──────┼──────────┼───────────┼────────────┼───────────────┼─────────┘
       │          │  REST/JSON · WebSocket · OpenAPI       │
┌──────┴──────────┴───────────┴────────────┴───────────────┴─────────┐
│                     CAPA DE PLATAFORMA (núcleo DTI)                 │
│   Bus eventos · CMS · NLP/IA · Big Data · GIS · Modelo FIWARE       │
│   Seguridad transversal: RBAC · TLS · AES · SIEM · WAF · EDR        │
└──────┬──────────────────────────────────────────────────────────────┘
       │  MQTT · REST · ETL · APIs de fabricante
┌──────┴──────────────────────────────────────────────────────────────┐
│                      CAPA DE ADQUISICIÓN                            │
│  Sensores · Meteo · Beacons · WiFi · RRSS · Alumbrado · Videocám.   │
└─────────────────────────────────────────────────────────────────────┘
```
