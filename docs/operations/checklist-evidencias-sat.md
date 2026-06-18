# Checklist de evidencias para el SAT — Exp. 18962/2025

| | |
|---|---|
| **Objeto** | Acta de Recepción / Prueba de Aceptación del Servicio (SAT, Hito 4) |
| **Uso** | Guion de verificación conjunta Ayuntamiento ↔ IT DIGITTAL: cada requisito del Pliego con su evidencia y cómo comprobarlo |

**Leyenda de estado**
- ✅ Implementado y verificable en la plataforma (software).
- 🟡 Implementado en software; pendiente de datos reales o de su activación.
- 🏗️ Pendiente físico / obra civil / autorización (fuera del software).
- 🗂️ Entregable administrativo (acta, informe, formación).

---

## 1. Requisitos transversales (PPT, cláusula QUINTA)

| Requisito | Evidencia | Estado | Verificación en el SAT |
|-----------|-----------|--------|------------------------|
| Plataforma DTI como núcleo integrador (UNE 178104 «o equiv.») | `src/nijar_dti/`, arquitectura por capas, `docs/architecture/` | ✅ | Revisar arquitectura y `GET /api/v1/health` |
| APIs abiertas REST/JSON con OpenAPI | `/docs`, `/openapi.json`, `docs/api/openapi.yaml` | ✅ | Abrir Swagger UI; 45 endpoints |
| Modelo semántico FIWARE («o equiv.») | `models/` + `docs/data-model/schemas/` (7 JSON Schemas) | ✅ | Revisar URNs y schemas |
| GIS integrado (WGS84/GeoJSON) | PostGIS, `core/geo.py`, mapa Leaflet en dashboard | ✅ | Ver mapa del dashboard; `/rutas/planificar` |
| Pub/sub y ETL/cargas periódicas | Redis, workers MQTT/social, backfill contexto | ✅ | Levantar workers; `/data/contexto/ingest` |
| Seguridad ENS Medio, RBAC, cifrado, auditoría | `core/security.py` (JWT, bcrypt, 5 roles), ENS docs | ✅ | Login OAuth2; probar roles |
| Pentest pre-producción | `docs/security/plan-pentest-sat.md` | 🟡 | Plan listo; ejecutar informe |
| Accesibilidad WCAG 2.1 AA + i18n 4 idiomas | `frontend/`, `docs/accessibility/`, axe-core en CI | ✅ | Auditar tótem/dashboard; cambiar idioma |
| Propiedad, código fuente y portabilidad | Repositorio Git, formatos abiertos, `docs/operations/` | ✅ | Entregar repo + dumps |

## 2. A.1 — Tótems interactivos

| Requisito | Evidencia | Estado | Verificación |
|-----------|-----------|--------|--------------|
| Hardware exterior (2000 nits, IP65/IK10, −20/+50 °C) | Pliego de suministro / albaranes | 🏗️ | Inspección física |
| Obra civil, acometidas, autorizaciones Parque | Proyecto de obra / licencias | 🏗️ | Inspección instalación |
| Bucle magnético, altura accesible, lectura fácil | Hardware + `frontend/totem/` (alto contraste, texto grande) | 🟡 | Verificar bucle físico; UI accesible |
| CMS centralizado sincronizado web/app | `services/cms_service.py`, `/cms/content` | ✅ | Publicar contenido y verlo en tótem |
| Agente IA / chatbot multilingüe en el tótem | `frontend/totem/` + `/chatbot/query` | ✅ | Preguntar al chatbot en 4 idiomas |
| Asistente por voz (entrada/lectura) | `frontend/totem/assets/totem.js` (STT/TTS) | ✅ | Probar micrófono y lectura |
| Planificador de rutas y propuesta de eventos | `/rutas/planificar`, `/rutas/recomendaciones` | ✅ | Botones «Sugerir ruta» / «Qué visitar» |
| Estadísticas de uso e interacción | tabla `visitas`, `/dashboards/totems/usage` | ✅ | Ver panel de uso de tótems |
| Telemetría y teleoperación (heartbeat, reinicio) | sensores tótem en seed; alertas observabilidad | 🟡 | Requiere tótem físico conectado |

## 3. A.2 — Smart Office DTI

| Requisito | Evidencia | Estado | Verificación |
|-----------|-----------|--------|--------------|
| Panel de control con KPIs en tiempo real | `/dashboards/smart-office/*`, `frontend/dashboard/` | ✅ | Abrir dashboard, pestaña Ambiental |
| Ingesta IoT (sensores ambientales) | `mqtt/`, `/data/iot/observations` | ✅ | Publicar lecturas MQTT de prueba |
| Alertas automáticas configurables | umbrales en `sensor`, `smart_office_overview` | ✅ | Ver alertas activas |
| Ejecución de acciones (banderas/aforos) | CMS + eventos; aforo en eventos | 🟡 | Documentar flujo de actuación |
| ML: predicción de afluencia, anomalías | `/prediccion/afluencia`, `/prediccion/anomalias` | 🟡 | Ejecutar con datos; ver MAPE |
| Informes PDF/Excel programados | `/dashboards/monthly-report` | ✅ | Generar informe mensual |

## 4. A.3 — Social Listening y Big Data

| Requisito | Evidencia | Estado | Verificación |
|-----------|-----------|--------|--------------|
| Conectores X / Facebook / Instagram | `connectors/social/` | 🟡 | Dry-run; real con tokens del Ayto. |
| Reviews de portales de viaje | Pendiente (C.1) | 🟡 | Mejora planificada (Plan Mejora Continua) |
| Movilidad WiFi anonimizada | DPIA + k-anonimato listos; ingesta pendiente | 🟡 | `docs/security/dpia-observatorio-movilidad.md` |
| Formularios/encuestas ciudadanas | fuente `encuesta_municipal` en `Opinion` | 🟡 | Documentar formulario |
| Análisis de sentimiento multiidioma | `connectors/social/nlp.py` | ✅ | `/data/social/kpis/sentiment` |
| Share of voice | `/data/social/kpis/share-of-voice` | ✅ | Endpoint |
| Índice tipo NPS | `/data/social/kpis/nps` | ✅ | Endpoint |
| Composición lingüística (origen aprox.) | `/data/social/kpis/composicion-linguistica` | ✅ | Endpoint |
| Modelos predictivos + validación (MAPE) | `/prediccion/validacion` | ✅ | Endpoint con holdout |
| Backfill histórico (INE/Junta/AENA) | `connectors/contexto/`, `/data/contexto/*` | ✅ | `python -m nijar_dti.workers.contexto_backfill` |
| Exportación CSV/JSON | API REST JSON; export CSV pendiente | 🟡 | Endpoints JSON disponibles |
| KPIs verificables y trazables | `docs/big-data/metodologia-y-limitaciones.md` | ✅ | Revisar metodología |
| k-anonimato ≥5 / RGPD | `core/anonimizacion.py` + DPIA | ✅ | Revisar regla y DPIA |

## 5. B.2 — Plan Director + Chatbot

| Requisito | Evidencia | Estado | Verificación |
|-----------|-----------|--------|--------------|
| Plan Director TD (diagnóstico, hoja de ruta, CAPEX/OPEX) | `docs/plan-director/plan-transformacion-digital.md` | ✅ | Revisar documento |
| Plan de infraestructura Smart City (LoRaWAN/fibra) | sección 7 del Plan Director | ✅ | Revisar documento |
| Chatbot 24/7 multicanal multilingüe | `/chatbot/query`, motor lexical + Rasa | ✅ | Preguntar en web/app/tótem |
| Grounding 3 niveles / control de alucinaciones | `chatbot_service.py` (alta/media/fuera de dominio) | ✅ | Probar preguntas fuera de dominio |
| Base de conocimiento ≥100 FAQs | `data/seeds/faqs*.py` (105 FAQs) | ✅ | `len(FAQS_SEED)` = 105 |
| Accesibilidad AA + voz | tótem STT/TTS, ARIA, contraste | ✅ | Probar voz y lectores |
| Telemetría del chatbot | `/chatbot/telemetry` | ✅ | Panel de telemetría |

## 6. C.1 — Mantenimiento, hosting y ANS

| Requisito | Evidencia | Estado | Verificación |
|-----------|-----------|--------|--------------|
| Hosting cloud UE, SLA 99% | `infra/terraform/`, `docs/operations/sla-monitoring.md` | 🟡 | Revisar IaC; desplegar |
| Firewall + WAF | WAF en Terraform / k8s ingress | ✅ | Revisar configuración |
| Backups off-site, RTO/RPO 24h | `docs/operations/disaster-recovery.md` | ✅ | Revisar plan DR |
| Monitorización 24/7 | `infra/observability/` (Prometheus/Grafana/Loki) | ✅ | Revisar dashboards/alertas |
| Helpdesk + matriz ANS | `core/ans.py`, `/incidencias/*` | ✅ | Registrar y resolver incidencia |
| Informe mensual con datos reales | `/dashboards/monthly-report` | ✅ | Generar informe del mes |
| Cumplimiento ANS por severidad | `/incidencias/ans` | ✅ | Consultar cumplimiento |

## 7. Hitos y entregables administrativos

| Entregable | Estado | Notas |
|------------|--------|-------|
| H1 Plan de proyecto, diseños, arquitectura | ✅ | Documentado |
| H2 Implementación intermedia + Plan TD definitivo | ✅ | Plan Director entregado |
| H3 Integración, pruebas, formación ≥10h | 🗂️ | Acta de formación pendiente |
| H4 Puesta en producción + SAT + as-built | 🗂️ | Acta de recepción a firmar |
| Pruebas FAT/SAT | 🗂️ | Ejecutar con el Ayuntamiento |
| Informe de pentest | 🟡 | Plan listo; ejecutar |
| Simulacro de backup/restauración | 🗂️ | Procedimiento en DR |

---

## 8. Comandos rápidos de verificación

```bash
# Arrancar la plataforma
cp .env.example .env && ./scripts/dev_up.sh && docker compose up api

# Suite de pruebas (unitarias)
pytest tests/ -m "not integration"

# Nº de FAQs (>=100)
python -c "from nijar_dti.data.seeds.faqs import FAQS_SEED; print(len(FAQS_SEED))"

# Backfill de contexto histórico (dry-run)
python -m nijar_dti.workers.contexto_backfill --dry-run --output dataset.json

# Swagger UI con todos los endpoints
# http://localhost:8000/docs
```

> Este checklist se actualiza conforme se cierran los puntos 🟡/🏗️/🗂️ y se firma junto con el Acta de Recepción del SAT.
