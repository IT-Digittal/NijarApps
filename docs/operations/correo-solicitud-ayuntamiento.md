# Correo de solicitud de información y accesos al Ayuntamiento de Níjar

> Borrador listo para enviar. Ajusta destinatarios, nombres y fechas antes del envío.

---

**Para:** [Responsable del contrato — Ayuntamiento de Níjar]
**CC:** [Interlocutor técnico municipal] · [DPD/DPO] · [Dirección de Proyecto IT DIGITTAL]
**Asunto:** Exp. 18962/2025 — Información, accesos y documentación necesarios para completar la implantación DTI

---

Estimado/a [nombre]:

En el marco del proyecto **«Implantación de soluciones de transformación digital del sector turístico de Níjar» (Exp. 18962/2025)**, la plataforma DTI, el chatbot, los tótems (software), el observatorio Big Data, el panel Smart Office y el módulo de mantenimiento (C.1) están desarrollados y probados.

Para **completar la integración real y la puesta en producción** necesitamos de su parte una serie de accesos, datos y autorizaciones que solo el Ayuntamiento, como titular de los sistemas y del dato, puede facilitar. Los agrupamos a continuación por bloques, indicando para qué se utilizan. Quedamos a su disposición para una breve reunión de coordinación si lo prefieren.

---

## 1. Accesos e integración con los sistemas municipales existentes

Necesarios para conectar los verticales actuales a la Plataforma DTI (requisito del PPT: integrar sin sustituir).

| Sistema | Qué necesitamos | Para qué |
|---|---|---|
| **Plataforma DTI actual** (`plataforma.nijardti.com`) | URL de acceso correcta, **documentación de API** (Swagger/Postman) o lista de endpoints + método de autenticación; idealmente una **cuenta de servicio/API** | Conectar e integrar sus datos en el panel central |
| **Web turística municipal** | URL, tecnología y, si procede, acceso a su API/BD o export | Sincronización de contenidos y analítica |
| **App «Vive Níjar»** | Contacto del proveedor, API/SDK disponible, mecanismo de envío de avisos (banderas/aforo) | Sincronización de contenidos y acciones (banderas/aforo) |
| **WiFi público** | Modelo/fabricante y acceso a estadísticas (anonimizadas) | Señal de movilidad del observatorio |
| **Sensores ambientales / estaciones meteo** | Marca/modelo, protocolo (MQTT/REST), credenciales y endpoints | Ingesta IoT en el Smart Office |
| **Beacons, alumbrado IoT, videocámaras** | Inventario, protocolo y accesos disponibles | Integración de verticales |

## 2. Redes sociales y analítica web (perfiles oficiales)

Necesario para activar el Social Listening y la eficacia digital con datos reales (hoy operamos en modo simulado).

- **X / Twitter:** Bearer Token de una app del Developer Portal (o autorización para crearla).
- **Facebook:** ID de la página oficial + **Page Access Token de larga duración**.
- **Instagram:** cuenta **Instagram Business** vinculada a la página de Facebook + su *Business Account ID*.
- **Google Analytics 4:** *Property ID* y una **cuenta de servicio** (JSON) con acceso de solo lectura, o invitación a la cuenta.
- Confirmación de los **handles oficiales** (Facebook/Instagram/X) del destino.

## 3. Contenidos y datos iniciales (carga inicial)

Para la carga inicial del CMS, el chatbot y el catálogo (responsabilidad del adjudicatario, con el material del Ayuntamiento).

- **Catálogo de recursos turísticos** (playas, rutas, monumentos, servicios) con descripciones y, si existen, coordenadas y fotos.
- **Agenda de eventos** y fuentes para mantenerla.
- **FAQs oficiales de la Oficina de Turismo** (horarios, normativa del Parque, teléfonos, etc.) para validar/ampliar las del chatbot.
- **Material gráfico y de marca:** logotipos, guía de estilo, imágenes con derechos de uso.
- **Traducciones oficiales** (si las hubiera) o validación de las que aporta IT DIGITTAL (ES/EN/DE/FR).
- **Datos históricos** a migrar (afluencia, contenidos de la web actual) si se desea continuidad.

## 4. Tótems: ubicación, obra civil y autorizaciones

Camino crítico del proyecto.

- **Ubicaciones exactas** aprobadas (inicio y fin de la ruta ciclista Rodalquilar–Albaricoques).
- **Autorizaciones del Parque Natural** y licencias de ocupación de vía pública.
- **Acometidas** eléctricas y de datos (o conformidad para su ejecución) en los puntos de instalación.
- Contacto del **órgano gestor del Parque** y del área municipal de obras/urbanismo.

## 5. Dominios e integración de acceso

> El **alojamiento y el despliegue en producción ya están resueltos y operativos** (infraestructura cloud en la UE, gestionada por IT DIGITTAL). Solo necesitamos lo siguiente:

- **Dominio(s)** del Ayuntamiento y gestión de **DNS** para publicar los servicios (panel, API, tótems) y emitir los certificados.
- **SSO / Directorio Activo** municipal, si desean integrar el acceso de los usuarios internos.

## 6. Seguridad, ENS y protección de datos (RGPD)

- Datos de contacto del **Delegado de Protección de Datos (DPD)**.
- **Política de privacidad** municipal y textos legales para web/app/tótems/chatbot/WiFi.
- Conformidad con la **DPIA de movilidad** y los tratamientos del observatorio (documento aportado por IT DIGITTAL).
- Autorización y **ventana para el pentest** previo a producción (alcance: API, web, app, tótems, IoT).
- Inventario/whitelist de **nodos IoT** autorizados.

## 7. Formularios y encuestas ciudadanas

- **Criterios del Ayuntamiento** para los formularios de encuesta/consulta pública a insertar en la web (campos, finalidad, idiomas), para que IT DIGITTAL los elabore.

## 8. Interlocución, validación y formación

- **Responsable municipal** y **interlocutor técnico** designados, y composición del **comité Go/No-Go**.
- **Fechas** para los hitos de validación y la **prueba de aceptación (SAT)** con presencia municipal.
- **Asistentes y calendario** para la **formación (≥ 10 h)** al personal (Oficina de Turismo y técnicos).

---

## Resumen de prioridades

| Prioridad | Bloque | Motivo |
|---|---|---|
| 🔴 Alta | Tótems: ubicaciones + autorizaciones Parque (§4) | Camino crítico (fabricación/instalación) |
| 🔴 Alta | API/acceso del DTI actual (§1) | Integración del panel central |
| 🔴 Alta | Tokens de RRSS + GA4 (§2) | Activar observatorio y eficacia digital reales |
| 🟠 Media | Contenidos y FAQs oficiales (§3) | Carga inicial y validación del chatbot |
| 🟠 Media | Dominios, DNS, SSO (§5) — hosting ya resuelto | Publicación en el dominio municipal |
| 🟠 Media | DPD, privacidad, ventana de pentest (§6) | Cumplimiento ENS/RGPD y SAT |
| 🟢 Normal | Formularios (§7), interlocución y formación (§8) | Operativa y cierre de hitos |

Para agilizar, podemos enviar **plantillas/formularios** donde volcar tokens y datos de acceso de forma segura, y un breve **procedimiento** para generar los Page Access Token de Meta y la cuenta de servicio de GA4.

Quedamos a la espera de sus indicaciones y agradecemos de antemano su colaboración.

Un cordial saludo,

**[Nombre] — Director de Proyecto**
IT DIGITTAL · Exp. 18962/2025
[teléfono] · [email]

---

> **Nota de seguridad:** rogamos **no enviar contraseñas ni tokens por correo en texto plano**. Facilitaremos un canal seguro (gestor de secretos / enlace cifrado) para las credenciales.
