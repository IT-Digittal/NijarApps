# Mapa funcional consolidado de la Plataforma DTI Níjar

| | |
|---|---|
| **Expediente** | 18962/2025 |
| **Versión** | 1.0 (consolidado tras Hito 4) |
| **Hitos** | H1 + H2 + H3 + H4 — todos al 100% |

Documento de referencia rápida que mapea cada actuación del Pliego con las funcionalidades implementadas, los componentes técnicos y los entregables.

---

## Actuaciones del contrato

### A.1 — Tótems digitales interactivos (2 unidades)

| Funcionalidad | Componente | Estado |
|---------------|------------|--------|
| Plantilla HTML accesible WCAG 2.1 AA | `frontend/totem/index.html` | ✅ |
| i18n ES/EN/DE/FR | `frontend/totem/assets/i18n.js` | ✅ |
| Modos accesibilidad (alto contraste, texto grande) | `frontend/totem/assets/totem.css` | ✅ |
| Navegación por categorías | `frontend/totem/assets/totem.js` | ✅ |
| Carga dinámica de POIs desde API | `GET /api/v1/tourism/resources` | ✅ |
| Chatbot integrado | `POST /api/v1/chatbot/query` | ✅ |
| Sensores de aforo | Tabla `sensor` con tipo `aforo` | ✅ |
| Detección inactividad y reset | `frontend/totem/assets/totem.js` | ✅ |
| Bucle magnético + texto ampliable | Hardware + CSS | ✅ Documentado |

### A.2 — Smart Office DTI

| Funcionalidad | Componente | Estado |
|---------------|------------|--------|
| Sensores ambientales (CO₂, temp, humedad, ruido, meteo) | Seed `data/seeds/sensores.py` | ✅ 9 sensores |
| Ingesta MQTT en tiempo real | `mqtt/subscriber.py` + `workers/mqtt_worker.py` | ✅ |
| Validación contra umbrales | `services/iot_service.py` | ✅ |
| Histórico de observaciones | Tabla `observacion` con paginación | ✅ |
| Dashboard operativo | `frontend/dashboard/` (pestaña Ambiental) | ✅ |
| KPIs en tiempo real | `GET /api/v1/dashboards/smart-office/overview` | ✅ |
| Series temporales con granularidad | `GET /api/v1/dashboards/smart-office/environment` | ✅ |
| Alertas Prometheus | `infra/observability/alerts.yaml` | ✅ |

### A.3 — Big Data + Social Listening

| Funcionalidad | Componente | Estado |
|---------------|------------|--------|
| Conector X (Twitter API v2) | `connectors/social/twitter.py` | ✅ |
| Conector Facebook (Graph API) | `connectors/social/facebook.py` | ✅ |
| Conector Instagram (Hashtag Search) | `connectors/social/instagram.py` | ✅ |
| Polling periódico | `workers/social_worker.py` | ✅ |
| Modo dry-run (datos sintéticos en 4 idiomas) | Cada conector | ✅ |
| Pipeline NLP (idioma, sentimiento, temas, entidades) | `connectors/social/nlp.py` | ✅ |
| Deduplicación idempotente | `connectors/social/pipeline.py` | ✅ |
| KPIs sentimiento, share-of-voice, top temas | `services/social_service.py` | ✅ |
| Dashboard Big Data | `frontend/dashboard/` (pestaña Big Data) | ✅ |
| Conector Google Analytics 4 | `connectors/analytics/ga4.py` | ✅ |

### B.2 — Plan Director + CMS + Chatbot IA

| Funcionalidad | Componente | Estado |
|---------------|------------|--------|
| CMS multicanal (tótem, web, app) | `services/cms_service.py` | ✅ |
| Plantillas de contenido | Schema `Contenido` con i18n | ✅ |
| Estado automático (borrador, publicado, archivado) | `cms_service` | ✅ |
| Motor lexical chatbot | `services/chatbot_service.py` | ✅ |
| Motor Rasa Open Source | `rasa/` + `services/chatbot_rasa_adapter.py` | ✅ |
| 22 FAQs base ES/EN/DE/FR | `data/seeds/faqs.py` | ✅ |
| Generación automática Rasa desde FAQs | `workers/rasa_generator.py` | ✅ |
| Failover automático Rasa → lexical | `chatbot_rasa_adapter.py` | ✅ |
| Telemetría completa | Tabla `interaccion_chatbot` | ✅ |
| Dashboard chatbot | `frontend/dashboard/` (pestaña Chatbot) | ✅ |

### C.1 — Mantenimiento + hosting 48 meses

| Funcionalidad | Componente | Estado |
|---------------|------------|--------|
| Hosting AWS UE Multi-AZ | `infra/terraform/` | ✅ Definido |
| EKS managed Kubernetes | `infra/k8s/` | ✅ Definido |
| Backups multinivel | RDS + AWS Backup vault + S3 | ✅ Definido |
| Monitoring 24/7 | Prometheus + Grafana + Loki | ✅ Definido |
| 9 alertas alineadas a SLAs | `infra/observability/alerts.yaml` | ✅ |
| Pentest pre-SAT + anual | `docs/security/plan-pentest-sat.md` | ✅ |
| Plan DR (RTO 4h / RPO 1h) | `docs/operations/disaster-recovery.md` | ✅ |
| Plan continuidad de negocio | `docs/operations/business-continuity.md` | ✅ |
| SLA monitoring + error budget | `docs/operations/sla-monitoring.md` | ✅ |
| Runbook operativo | `docs/operations/runbook.md` | ✅ |
| Informe mensual generable | `GET /api/v1/dashboards/monthly-report` | ✅ |

---

## Endpoints REST (API v1)

30 endpoints documentados en OpenAPI 3.1:

### Auth
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`

### Tourism
- `GET /tourism/resources`, `POST /tourism/resources`
- `GET /tourism/resources/{id}`, `PUT /tourism/resources/{id}`, `DELETE /tourism/resources/{id}`
- `GET /tourism/events`, `POST /tourism/events`
- `GET /tourism/services`

### IoT
- `POST /data/iot/observations` (ingesta HTTP además de MQTT)
- `GET /data/iot/sensors`, `GET /data/iot/sensors/{id}`
- `GET /data/iot/observations`

### Social Listening
- `GET /data/social/mentions`
- `GET /data/social/kpis/sentiment`
- `GET /data/social/kpis/share-of-voice`
- `GET /data/social/topics`

### CMS
- `GET /cms/content`, `POST /cms/content`
- `GET /cms/content/{id}`, `PUT /cms/content/{id}`

### Chatbot
- `POST /chatbot/query`
- `POST /chatbot/feedback`
- `GET /chatbot/intents`
- `GET /chatbot/telemetry`

### Dashboards
- `GET /dashboards/smart-office/overview`
- `GET /dashboards/smart-office/environment`
- `GET /dashboards/big-data/overview`
- `GET /dashboards/totems/usage`
- `GET /dashboards/monthly-report`

### Health
- `GET /health`, `GET /ready`

### Observabilidad
- `GET /metrics` (Prometheus, no en OpenAPI)

---

## Frontends

| Frontend | Ruta | Stack | Auth | Idiomas |
|----------|------|-------|------|---------|
| Dashboard Smart Office | `/dashboard` | HTML + Tailwind CDN + Chart.js + Leaflet | OAuth2 + JWT | ES |
| Tótem digital | `/totem` | HTML + Tailwind CDN | Sin auth (canal público) | ES/EN/DE/FR |

Documentación accesibilidad: `docs/accessibility/wcag-2.1-AA-compliance.md`.

---

## Tests

| Categoría | Archivos | Tests | Cobertura |
|-----------|----------|-------|-----------|
| Schemas Pydantic | `test_schemas.py` | 22 | — |
| Seguridad (JWT + bcrypt) | `test_security.py` | 8 | — |
| Chatbot lexical | `test_chatbot.py` | 11 | — |
| Chatbot Rasa adapter | `test_chatbot_rasa.py` | 12 | — |
| Seeds (integridad) | `test_seeds.py` | 7 | — |
| API endpoints | `test_api_endpoints.py` | 12 | — |
| Health | `test_health.py` | 5 | — |
| MQTT parser | `test_mqtt_parser.py` | 17 | — |
| Social NLP | `test_social_nlp.py` | 22 | — |
| Social conectores | `test_social_connectors.py` | 15 | — |
| GA4 conector | `test_ga4.py` | 11 | — |
| **Total** | **11 archivos** | **142** | **56%** |

Ejecución: `pytest tests/` (~5 segundos).

---

## Matriz de cumplimiento normativo

| Norma | Aplicación principal |
|-------|----------------------|
| **UNE 178104** | Arquitectura modular tres capas (`docs/architecture/diagramas-tecnicos.md`) |
| **UNE 178501/2** | Indicadores DTI vía dashboards |
| **FIWARE Smart Data Models** | URNs en todas las entidades, 7 JSON Schemas en `docs/data-model/schemas/` |
| **ENS Nivel Medio** | KMS rotación, MFA admin, audit logs, backups, pentest, drills DR |
| **RGPD + LOPDGDD** | UE-only, anonimización SHA-256, retention 6/12 meses, DPO, derechos ARCO-POL |
| **WCAG 2.1 AA** | Frontend dashboard + tótem auditados con axe-core en CI |
| **DNSH** | gp3, region renovable, autoscaling para evitar overprovisioning |
| **ISO 9001/14001/27001/42001/45001** | SIG IT DIGITTAL aplicado |

---

## Documentación entregable

```
docs/
├── api/openapi.yaml                              30 endpoints, 29 schemas
├── architecture/
│   ├── arquitectura-global.md                    Visión UNE 178104
│   ├── diagramas-tecnicos.md                     9 diagramas Mermaid + ER
│   ├── decisiones-tecnicas.md                    21 ADRs
│   └── dependencias-terceros.md                  Inventario dependencias
├── backend/
│   └── manual-tecnico-backend.md                 Manual completo del backend
├── chatbot/
│   └── manual-tecnico-chatbot.md                 Manual técnico del chatbot
├── accessibility/
│   └── wcag-2.1-AA-compliance.md                 50 criterios verificados
├── data-model/
│   ├── README.md
│   └── schemas/                                  7 JSON Schemas FIWARE
├── database/schema.sql                           SQL consolidado
├── mqtt/mosquitto.conf                           Config broker
├── operations/
│   ├── runbook.md                                Operativa día a día
│   ├── disaster-recovery.md                      RTO 4h / RPO 1h
│   ├── sla-monitoring.md                         SLAs y SLOs
│   └── business-continuity.md                    Plan continuidad C.1
└── security/
    └── plan-pentest-sat.md                       Plan pentest pre-SAT
```

---

## Estado por hito (resumen)

| Hito | Semanas | Entregable | Estado |
|------|---------|------------|--------|
| **H1** | S1-S2 | Planificación, diseños, backend base, modelo de datos, schemas, seeds, motor lexical | ✅ 100% |
| **H2** | S3-S5 | Workers MQTT y Social Listening, integración Rasa con generación automática | ✅ 100% |
| **H3** | S6-S7 | Frontend dashboard + tótem WCAG 2.1 AA, conector GA4, plan pentest | ✅ 100% |
| **H4** | S8 | Terraform AWS, K8s manifests, observabilidad Prometheus + Grafana + Loki, CI/CD bloqueante, runbook operativo | ✅ 100% |

**Total**: 142 tests verdes, 56% de cobertura, 90 archivos Python, 12 documentos markdown, 30 endpoints, 22 FAQs en 4 idiomas, 9 sensores, 14 recursos turísticos, 1051 líneas de Terraform, 7 manifests K8s, 5 dashboards Grafana, 9 alertas Prometheus, 21 ADRs.

---

## Próximos pasos (entrega administrativa pendiente)

- Cronograma operativo Excel actualizado con semanas reales del despliegue.
- Checklist de evidencias para el SAT.
- Plantilla de informe mensual del C.1 cumplimentada con un mes de ejemplo.
- Memoria técnica final consolidada en PDF/DOCX para la firma del SAT.

Estos entregables se preparan en el siguiente bloque a petición del cliente.
