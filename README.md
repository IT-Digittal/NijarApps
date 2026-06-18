# Plataforma DTI Níjar

Plataforma de **Destino Turístico Inteligente (DTI) Smart City** del Ayuntamiento de Níjar.

| | |
|---|---|
| **Expediente** | 18962/2025 |
| **Adjudicatario** | IT DIGITTAL |
| **Marco** | PRTR — NextGenerationEU — Componente 14 |
| **Estándares** | UNE 178104 · FIWARE Smart Data Models · ENS Nivel Medio · WCAG 2.1 AA |
| **Versión actual** | 1.3.0 (Hito 4 — SAT y puesta en producción) |

---

## Resumen funcional

La plataforma integra los componentes **A.2 (Smart Office DTI)**, **A.3 (Big Data + Social Listening)**, **A.1 (gestión de los 2 tótems interactivos)** y **B.2 (Chatbot IA multilingüe + CMS)** del contrato.

| Módulo | Descripción | Estado |
|--------|-------------|--------|
| `auth` | OAuth2 + JWT con RBAC de 5 roles | ✅ Operativo |
| `tourism` | CRUD recursos / eventos / servicios con filtros geoespaciales | ✅ Operativo |
| `iot` | Ingesta HTTP, catálogo de sensores, histórico de observaciones | ✅ Operativo |
| `iot · MQTT subscriber` | Ingesta en tiempo real desde el broker (Hito 2) | ✅ Operativo |
| `social-listening` | Menciones, KPIs sentimiento, share-of-voice, top temas | ✅ Operativo |
| `social-listening · workers` | Polling X / Facebook / Instagram (Hito 2) | ✅ Operativo |
| `cms` | Gestión multicanal (tótems / web / app) con plantillas | ✅ Operativo |
| `chatbot · lexical` | Motor de matching multilingüe ES/EN/DE/FR (Hito 1) | ✅ Operativo |
| `chatbot · rasa` | Servidor Rasa Open Source con modelo entrenado (Hito 2) | ✅ Operativo |
| `dashboards` | Smart Office, Big Data, uso de tótems, informe mensual C.1 | ✅ Operativo |
| `analitica` | KPI índice tipo NPS y composición lingüística (k-anonimato ≥5) | ✅ Operativo |
| `contexto` | Backfill de fuentes públicas (INE/Junta/AENA) + factor de expansión | ✅ Operativo |
| `prediccion` | Predicción de afluencia (estacional), validación MAPE y anomalías | ✅ Operativo |
| `rutas` | Planificador de itinerarios y recomendaciones de visitas/eventos | ✅ Operativo |
| `chatbot · 105 FAQs` | Base de conocimiento ES/EN/DE/FR (≥100), voz en tótem (STT/TTS) | ✅ Operativo |

---

## Novedades del Hito 4 — SAT y puesta en producción

### 1. Infraestructura como código (Terraform)

Despliegue completo en **AWS eu-central-1 (Frankfurt)** definido en `infra/terraform/` (7 archivos, 1051 líneas):

- **Red:** VPC con 3 AZ, subnets públicas y privadas, NAT Gateway, VPC Flow Logs (365 días).
- **Compute:** EKS managed Kubernetes 1.30 con node group `t3.large` (2-6 nodos).
- **BBDD:** RDS PostgreSQL 16.3 con PostGIS, Multi-AZ en producción, KMS rotación, backups 35 días.
- **Cache:** ElastiCache Redis 7.1 Multi-AZ con TLS y cifrado en reposo.
- **Imágenes:** ECR con escaneo automático y lifecycle (30 imágenes).
- **Backups extra:** AWS Backup vault con vault-lock 365 días.
- **Cifrado:** KMS con rotación habilitada para RDS, EKS secrets, S3, Redis, Secrets Manager y AWS Backup.
- **Edge:** ACM (cert wildcard), WAF v2 (Common, BadInputs, SQLi + RateLimit 2000 req/IP/5min).

```bash
cd infra/terraform
terraform init && terraform plan -out=tfplan && terraform apply tfplan
```

### 2. Manifests Kubernetes

`infra/k8s/` con 7 manifests YAML que despliegan toda la plataforma:

- Namespace con `pod-security: restricted` + NetworkPolicy default-deny.
- API con security context endurecido (runAsNonRoot, readOnlyRootFilesystem, drop ALL capabilities), startup/readiness/liveness probes y HPA 2-8 réplicas.
- ServiceAccount IRSA para acceso seguro a Secrets Manager y S3.
- External Secrets Operator sincronizando 9 secretos desde AWS Secrets Manager (refresh 1h).
- Workers (mqtt-subscriber, social-worker) y Job de migración Alembic con helm hooks pre-install/pre-upgrade.
- StatefulSet Mosquitto + Deployment Rasa con PVCs gp3.
- Ingress AWS LB Controller con TLS, WAF y access logs S3.

### 3. Observabilidad (Prometheus + Grafana + Loki)

`infra/observability/`:

- **Endpoint `/metrics`** en la API con métricas HTTP estándar (Counter + Histogram), métricas de dominio (sensores por estado, observaciones, chatbot por confianza, opiniones por fuente y sentimiento) y métricas de salud (`db_up`, `last_metrics_refresh`).
- **kube-prometheus-stack** con `prometheus-values.yaml`: retention 15 días + 30 GB, persistencia gp3, AlertManager con receivers críticos/default.
- **Loki** con retention 30 días para logs estructurados.
- **5 dashboards Grafana** en JSON: API overview, Smart Office, Big Data, Chatbot, Infraestructura.
- **9 alertas Prometheus** alineadas con SLAs: API down, error rate >5%, latencia p95 >1s, BBDD down, sensores offline >50%, observaciones inválidas >10%, resolución chatbot <70%, SLA mensual en riesgo.

### 4. CI/CD con escaneo bloqueante

`.github/workflows/`:

- **`ci.yml`** — tests + ruff + mypy + pip-audit + osv-scanner + semgrep (OWASP) + bandit + Trivy de imagen + axe-core + kubeconform + terraform validate. Cualquier fallo bloquea el merge.
- **`cd.yml`** — OIDC con AWS (sin secrets rotables), build/push a ECR, Trivy bloqueante pre-push, migraciones Alembic, deploy a EKS, smoke test post-deploy con rollback automático.
- **`security-nightly.yml`** — escaneo extendido diario que crea issue automáticamente si aparece CVE crítico nuevo.

### 5. Documentación operativa

`docs/operations/`:

- [`runbook.md`](docs/operations/runbook.md) — bootstrap del backend Terraform, IRSA, despliegue inicial, comandos del día a día, troubleshooting, re-entrenamiento Rasa, procedimientos de emergencia.
- [`disaster-recovery.md`](docs/operations/disaster-recovery.md) — RTO 4h, RPO 1h, escenarios y procedimientos detallados, drills trimestrales y anuales.
- [`sla-monitoring.md`](docs/operations/sla-monitoring.md) — SLA contractual 99% (mejora 99.5%), SLOs por componente, error budget, escalado on-call SOC 24/7.
- [`business-continuity.md`](docs/operations/business-continuity.md) — Plan de continuidad C.1, multi-AZ, backups multinivel, transición al fin del contrato.

---

## Novedades del Hito 3

### 1. Dashboard Smart Office y plantilla de tótem accesible

Frontend estático servido por la propia API (sin build step):

- **`/dashboard`** — panel del Smart Office con 6 pestañas: Resumen, Ambiental, Big Data, Tótems, Chatbot, Mapa. KPIs en tiempo real cada 30 s, charts Chart.js, mapa Leaflet con los recursos turísticos publicados. Login OAuth2 con auto-refresh de tokens.
- **`/totem`** — plantilla de los tótems digitales A.1 con i18n en 4 idiomas (ES/EN/DE/FR), modos de accesibilidad (alto contraste y texto grande), área táctil ≥ 44 px, detección de inactividad, integración con el chatbot y carga dinámica de POIs publicados desde el CMS.

Cumplimiento WCAG 2.1 AA documentado en [`docs/accessibility/wcag-2.1-AA-compliance.md`](docs/accessibility/wcag-2.1-AA-compliance.md).

```bash
docker compose up api
# Dashboard: http://localhost:8000/dashboard
# Tótem:     http://localhost:8000/totem
```

### 2. Conector Google Analytics 4

Eficacia digital del informe mensual del C.1 alimentada por GA4:

- Conector `connectors/analytics/ga4.py` con autenticación service-account.
- Métricas capturadas: sesiones, usuarios totales y nuevos, páginas vistas, duración media, bounce rate y desglose por canal de adquisición.
- **Modo dry-run** con datos sintéticos coherentes para desarrollo sin credenciales.
- Llamada protegida desde `informe_mensual()`: si GA4 falla, el informe se entrega igual sin la sección.

```bash
echo "GA4_PROPERTY_ID=123456789" >> .env
echo "GA4_SERVICE_ACCOUNT_JSON=/secrets/ga4-sa.json" >> .env
```

### 3. Plan de pentest pre-SAT

Documento operativo en [`docs/security/plan-pentest-sat.md`](docs/security/plan-pentest-sat.md):

- Metodología OWASP WSTG + API Top 10:2023 + PTES.
- Alcance: API REST, frontends, broker MQTT, workers, infraestructura.
- 14 días laborables (preparación + reconocimiento + análisis + pruebas manuales + informe + re-test).
- Bloqueante para SAT del H4: cero hallazgos críticos abiertos.
- Pipeline CI con `pip-audit`, `osv-scanner`, `semgrep`, `trivy`, `bandit`, `axe-core` en cada PR.
- Revisiones anuales durante los 48 meses del C.1.

---

## Novedades del Hito 2

### 1. Subscriber MQTT real (ingesta IoT en tiempo real)

Worker autónomo que se suscribe al broker MQTT y persiste cada observación en BBDD.

- **Topics escuchados:** `nijar/sensors/+/+` (cualquier sensor + cualquier magnitud).
- **Validación:** payload JSON parseado y validado contra el schema `ObservacionIn`.
- **Resiliencia:** reconexión exponencial gestionada por paho-mqtt, idempotencia.
- **TLS:** soporta certificados de cliente para producción (ENS Medio).
- **Bridging async:** loop asyncio dedicado para que el callback MQTT no bloquee la persistencia.
- **Métricas:** mensajes recibidos / válidos / inválidos / sensores no encontrados / errores / reconexiones.

```bash
# Levantar el subscriber junto con la API
docker compose --profile workers up -d mqtt-subscriber

# Publicar lecturas de prueba
python scripts/mqtt_publish_test.py --count 20 --interval 1
```

### 2. Conectores Social Listening (X, Facebook, Instagram)

Worker que ejecuta polling periódico (15 min por defecto) sobre las tres plataformas.

- **X / Twitter API v2** — Recent Search filtrando por términos del destino.
- **Facebook Graph API** — feed de la página oficial del Ayuntamiento.
- **Instagram Graph API** — Hashtag Search por `#cabodegata`, `#nijar`, etc.
- **Modo `dry-run`:** datos sintéticos realistas en 4 idiomas para desarrollo y demos sin tokens.
- **Pipeline NLP integrado:** detección de idioma, sentimiento por lexicón con negación, extracción de temas y mapeo de entidades a URNs FIWARE.
- **Idempotencia:** deduplicación por `(fuente, fuente_id_externo)` antes de persistir.

```bash
# Habilitar y levantar el worker
echo "SOCIAL_LISTENING_ENABLED=true" >> .env
echo "SOCIAL_DRY_RUN=true" >> .env  # cambiar a false cuando haya tokens
docker compose --profile workers up -d social-worker
```

### 3. Integración Rasa Open Source (chatbot avanzado)

Servidor Rasa con modelo entrenado a partir de las FAQs del seed (una única fuente de verdad).

- **Generador automático** `python -m nijar_dti.workers.rasa_generator` produce `domain.yml`, `nlu.yml`, `rules.yml` y `stories.yml` desde `nijar_dti.data.seeds.faqs.FAQS_SEED`. Cuando se añade una FAQ, basta con re-generar y re-entrenar.
- **Pipeline DIET** + ResponseSelector + FallbackClassifier con umbral 0.55.
- **Adapter** `chatbot_rasa_adapter.py` consume `/model/parse` y `/webhooks/rest/webhook`.
- **Selector de motor:** variable `CHATBOT_ENGINE` permite alternar `lexical` ↔ `rasa` sin tocar los endpoints.
- **Failover automático:** si Rasa no responde y `RASA_FALLBACK_TO_LEXICAL=true`, el chatbot sigue respondiendo con el motor de Hito 1.

```bash
# Generar artefactos, entrenar y levantar Rasa
./scripts/dev_up.sh --rasa

# O por separado:
python -m nijar_dti.workers.rasa_generator
docker compose --profile rasa-train run --rm rasa-trainer
docker compose --profile rasa up -d rasa
```

---

## Stack técnico

- **Backend:** Python 3.11+ · FastAPI · SQLAlchemy 2.0 async · Pydantic v2
- **BBDD:** PostgreSQL 16 · PostGIS 3 · `pg_trgm`
- **Mensajería:** MQTT (Eclipse Mosquitto) · Redis (cache + pub/sub)
- **NLP:** motor lexical propio (Hito 1) + Rasa Open Source 3.6 (Hito 2)
- **Migraciones:** Alembic
- **Seguridad:** OAuth2 + JWT (HS256) · bcrypt cost 12 · RBAC con 5 roles
- **Observabilidad:** structlog (logs JSON) · health/readiness probes
- **Calidad:** ruff · mypy estricto · pytest + pytest-cov · pre-commit
- **Despliegue:** Docker · docker-compose · GitHub Actions

Decisiones técnicas en [`docs/architecture/decisiones-tecnicas.md`](docs/architecture/decisiones-tecnicas.md).

---

## Arranque rápido (Docker, recomendado)

```bash
git clone <repo-url>
cd nijar-dti-platform
cp .env.example .env

# Solo la API (sin workers ni Rasa)
./scripts/dev_up.sh
docker compose up api

# Con workers MQTT y Social Listening
./scripts/dev_up.sh --workers
docker compose up api

# Con todo: workers + Rasa entrenado
./scripts/dev_up.sh --workers --rasa
docker compose up api
```

Una vez activa:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
- **Health:** http://localhost:8000/api/v1/health
- **Rasa server:** http://localhost:5005 (si `--rasa`)

### Credenciales por defecto del usuario administrador

```
email: admin@nijar.es
pass:  CambiarEnPrimerArranque#2026
```

> Cambiar tras el primer arranque mediante `INITIAL_ADMIN_EMAIL` y `INITIAL_ADMIN_PASSWORD`.

### Datos cargados automáticamente

- **1 usuario administrador** con 2FA obligatorio.
- **14 recursos turísticos** con coordenadas GPS reales y descripciones en 4 idiomas.
- **9 sensores** del Smart Office y los 2 tótems.
- **105 FAQs base del chatbot** en ES/EN/DE/FR (≥100 contractual) cubriendo todas las categorías obligatorias.

---

## Variables de entorno relevantes

### MQTT subscriber

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `MQTT_BROKER_HOST` | `mqtt` | Host del broker |
| `MQTT_BROKER_PORT` | `1883` | Puerto |
| `MQTT_TOPIC_PATTERN` | `nijar/sensors/+/+` | Patrón de topics suscritos |
| `MQTT_USE_TLS` | `false` | TLS para producción |
| `MQTT_TLS_CA_CERT` | — | Path al CA certificate |
| `MQTT_TLS_CLIENT_CERT` | — | Path al certificado de cliente |
| `MQTT_TLS_CLIENT_KEY` | — | Path a la clave privada |

### Social Listening

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `SOCIAL_LISTENING_ENABLED` | `false` | Activa el worker |
| `SOCIAL_DRY_RUN` | `true` | Modo síntetico sin llamar a APIs externas |
| `SOCIAL_POLLING_INTERVAL_MINUTES` | `15` | Cadencia entre polls |
| `TWITTER_BEARER_TOKEN` | — | Bearer Token del developer portal |
| `TWITTER_SEARCH_QUERY` | `Cabo de Gata OR Níjar OR "Playa de Mónsul"` | Query Recent Search v2 |
| `FACEBOOK_ACCESS_TOKEN` | — | Page Access Token de larga duración |
| `FACEBOOK_PAGE_ID` | — | ID de la página oficial |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | — | IG Business Account vinculada |
| `INSTAGRAM_HASHTAGS` | `cabodegata,nijar,playamonsul` | Lista separada por comas |

### Chatbot

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `CHATBOT_ENGINE` | `lexical` | `lexical` o `rasa` |
| `RASA_URL` | `http://rasa:5005` | URL del servidor Rasa |
| `RASA_TIMEOUT_SECONDS` | `8` | Timeout de cada llamada |
| `RASA_FALLBACK_TO_LEXICAL` | `true` | Fallback si Rasa falla |

---

## Tests

```bash
# Todos los tests unitarios
pytest tests/

# Con cobertura HTML
pytest tests/ --cov=nijar_dti --cov-report=html

# Solo bloques nuevos del Hito 2
pytest tests/test_mqtt_parser.py tests/test_social_nlp.py tests/test_social_connectors.py tests/test_chatbot_rasa.py
```

La suite (133 tests, ~5 segundos) valida:

- Parser MQTT — topics, payloads JSON, timestamps en distintos formatos, valores únicos vs múltiples, errores de validación.
- NLP de Social Listening — detección de idioma, sentimiento por lexicón con negación, extracción de temas, mapeo a URNs FIWARE.
- Conectores en modo `dry-run` — formato de menciones, idiomas cubiertos, configuración detectada.
- Adapter Rasa — selector de motor, mapeo de confianza, generador de artefactos coherente con FAQs.
- Resto del Hito 1 — schemas Pydantic, JWT/bcrypt, motor lexical, integridad de seeds, rutas montadas, esquema de errores.

---

## Estructura del proyecto

```
nijar-dti-platform/
├── alembic/versions/001_initial.py    # Esquema completo (11 tablas + extensiones)
├── docs/
│   ├── api/openapi.yaml                # OpenAPI 3.1 (30 endpoints)
│   ├── architecture/                   # Arquitectura, ADRs, dependencias
│   ├── data-model/schemas/             # 7 JSON Schemas FIWARE
│   ├── database/schema.sql
│   └── mqtt/mosquitto.conf
├── rasa/                               # Configuración + datos generados
│   ├── config.yml
│   ├── domain.yml                      # auto-generado desde FAQs
│   ├── data/{nlu,rules,stories}.yml    # auto-generados desde FAQs
│   ├── credentials.yml
│   └── endpoints.yml
├── scripts/
│   ├── dev_up.sh                       # Arranque end-to-end
│   └── mqtt_publish_test.py            # Publicador de prueba
├── src/nijar_dti/
│   ├── api/v1/                         # 8 routers REST
│   ├── connectors/social/              # Twitter, Facebook, Instagram + NLP
│   ├── core/                           # database, security, logging
│   ├── data/seeds/                     # Seeds (admin, recursos, sensores, FAQs)
│   ├── models/                         # 11 modelos ORM
│   ├── mqtt/                           # parser + subscriber
│   ├── schemas/                        # 9 módulos Pydantic
│   ├── services/                       # 7 servicios + adapter Rasa
│   ├── workers/                        # mqtt_worker, social_worker, rasa_generator
│   ├── config.py
│   └── main.py
├── tests/                              # 133 tests unitarios
├── docker-compose.yml                  # api + db + redis + mqtt + workers + rasa
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## Roles RBAC

| Rol | Permisos |
|-----|----------|
| `administrador_tic` | Acceso total + gestión de usuarios + 2FA obligatorio |
| `gestor_contenidos` | CRUD recursos turísticos, eventos, servicios y CMS |
| `analista_datos` | Lectura de Big Data, Social Listening y telemetría chatbot |
| `operador_smart_office` | Ingesta IoT y consulta de dashboards Smart Office |
| `auditor` | Lectura de logs, informes mensuales y eventos de seguridad |

---

## Hitos del proyecto

| Hito | Semanas | Entregable | Certificación |
|------|---------|------------|---------------|
| H1 | S1-S2 | Planificación y diseños | — |
| H2 | S3-S5 | Implementación intermedia (workers + Rasa) | 1ª (H1+H2) |
| H3 | S6-S7 | Integración y pruebas | — |
| H4 | S8 | Puesta en producción + SAT | 2ª (H3+H4) |
| C.1 | 48 meses | Mantenimiento + hosting | 3ª-50ª mensuales |

---

## Cumplimiento normativo

| Norma | Aplicación |
|-------|------------|
| **UNE 178104** | Plataforma de ciudad inteligente — interoperabilidad |
| **UNE 178501/178502** | Indicadores DTI |
| **ENS Nivel Medio (RD 311/2022)** | Esquema Nacional de Seguridad |
| **RGPD + LOPDGDD** | Protección de datos |
| **WCAG 2.1 AA** | Accesibilidad digital |
| **DNSH** | Sostenibilidad ambiental PRTR |
| **ISO 9001 / 14001 / 27001 / 42001 / 45001** | SIG IT DIGITTAL |

---

## Contacto

- **Adjudicatario:** IT DIGITTAL
- **Soporte (durante C.1):** SOC 24/7
- **Repositorio:** propiedad del Ayuntamiento de Níjar al final del contrato
