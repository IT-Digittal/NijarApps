# Fuentes de datos e integraciones · Plataforma DTI Níjar

Este documento identifica las **fuentes de datos, APIs y servicios** que
alimentan los KPIs de la plataforma, separando lo que **genera y recoge
directamente nuestra solución** (no requiere acción del Ayuntamiento) de lo
que **necesitamos que el Ayuntamiento nos facilite** (accesos, credenciales o
autorizaciones).

> El catálogo está modelado en la plataforma (`fuentes_datos`) y disponible por
> API en `GET /api/v1/integraciones/fuentes` y `GET /api/v1/integraciones/resumen`,
> con exportación CSV en `GET /api/v1/integraciones/fuentes.csv`.

---

## 1. Datos que genera y recoge nuestra solución (nuestra parte — ya preparado)

No dependen de accesos externos; los produce la propia plataforma:

| Cód. | Fuente | Estado |
|------|--------|--------|
| FD-001 | Usuarios, accesos, roles y logs del panel de gestión | Operativa |
| FD-002 | Uso del chatbot IA (consultas, idiomas, respuestas, satisfacción) | Operativa |
| FD-003 | Uso y estado de los tótems (disponibilidad, errores, interacciones) | Operativa |
| FD-004 | Contenidos del CMS (recursos, eventos, campañas) | Operativa |
| FD-005 | Social Listening (motor propio de captación y NLP) | Operativa* |
| FD-006 | Sensores IoT propios del Smart Office (CO₂, Tª, humedad, ruido) | Operativa |
| FD-007 | Datos operativos de los módulos propios (disponibilidad, incidencias, SLA) | Operativa |
| FD-008…013 | Verticales transversales (alumbrado, agua, residuos, movilidad, seguridad, energía) | Modelo + API + KPIs listos (demo); se conectan al sistema real cuando se aprueben |

\* El motor de Social Listening es propio; para operar contra las cuentas
reales necesita las credenciales de las APIs sociales (ver FD-105…107).

**Lo que ya está hecho por nuestra parte:** modelo de datos, migraciones,
seeders con datos de ejemplo, servicios de KPIs, API REST y exportaciones CSV
de todas estas fuentes, además del panel transversal.

---

## 2. Accesos y datos a facilitar por el Ayuntamiento (su parte)

Para completar la integración real y la puesta en producción:

| Cód. | Fuente / acceso | Qué necesitamos |
|------|-----------------|-----------------|
| FD-101 | Datos turísticos y contenidos oficiales | Catálogo de recursos, agenda de eventos, FAQs, material gráfico/marca y traducciones oficiales |
| FD-101b | **Noticias del Ayuntamiento (Strapi)** | ✅ **Integrado** (API pública sin auth) — ver [runbook](runbook-noticias-strapi.md); noticias de Turismo por categoría |
| FD-102 | Analítica web/app municipal | **Property ID de GA4 + cuenta de servicio** (lectura); contenedor de Tag Manager si existe — ver [runbook de activación](runbook-ga4.md) |
| FD-103 | App Vive Níjar (avisos banderas/aforo, uso) | Acceso a su API/backend o export de datos de uso |
| FD-104 | Movilidad y afluencia | Acceso a WiFi público, sensores/contadores/beacons y, si existe, dato de acceso al Parque (con DPIA) |
| FD-105 | Perfil X (Twitter) | **Bearer Token** + confirmación del handle oficial |
| FD-106 | Perfil Facebook | **Page Access Token + ID** de la página — ver [runbook de activación](runbook-social-listening-meta.md) |
| FD-107 | Perfil Instagram | **Instagram Business Account ID** — ver [runbook de activación](runbook-social-listening-meta.md) |
| FD-108 | Sensores IoT / estaciones meteo existentes | Protocolo (MQTT/HTTP), credenciales y whitelist de nodos |
| FD-109 | Campañas de promoción | Nombre, fechas, canales, objetivos y contenidos |
| FD-110 | Plataforma DTI actual (plataforma.nijardti.com) | URL correcta + documentación de API o cuenta de servicio |
| FD-111 | SSO / Directorio Activo municipal | Integración SSO/AD y titularidad de credenciales |
| FD-112 | Hosting, dominios y DNS | Proveedor cloud (UE), dominios/DNS y titularidad municipal |
| FD-113 | RGPD y seguridad | Contacto del DPD, política de privacidad, conformidad DPIA de movilidad y ventana de pentest |
| FD-114 | Tótems (camino crítico) | Ubicaciones aprobadas, autorizaciones (Parque Natural y vía pública) y acometidas eléctricas/datos |
| FD-115 | Formularios y encuestas ciudadanas | Criterios del Ayuntamiento para las encuestas de la web |

---

## 3. Resumen

- **Nuestra parte:** los datos que genera la solución se recogen directamente y
  ya están modelados, sembrados, servidos por API y exportables.
- **Su parte:** para los datos que ya existen en sistemas municipales o
  plataformas externas, necesitamos que nos indiquen las fuentes disponibles y
  nos faciliten los accesos/credenciales/autorizaciones de la tabla anterior.

Con esos accesos sustituimos progresivamente los datos de ejemplo por datos
reales, sin rediseños, sobre el mismo modelo troncal
(municipio → zona → instalación → equipo → incidencia → informe).
