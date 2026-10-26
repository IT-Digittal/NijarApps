# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Plataforma DTI (Destino Turístico Inteligente) Smart City for the Ayuntamiento de Níjar. A FastAPI backend serving a tourism platform with IoT ingestion, social listening, multilingual chatbot, CMS, and dashboards.

**Language convention**: The entire codebase — variable names, function names, model fields, comments, docstrings, error messages, and docs — is in **Spanish**. Follow this convention in all new code (e.g., `nombre_completo` not `full_name`, `recurso_turistico` not `tourism_resource`).

## Development Commands

### Running locally (Docker — recommended)

```bash
cp .env.example .env

# API only (no workers, no Rasa)
./scripts/dev_up.sh
docker compose up api

# With MQTT + Social Listening workers
./scripts/dev_up.sh --workers

# Everything including Rasa chatbot
./scripts/dev_up.sh --workers --rasa
```

On Windows, use the PowerShell/batch scripts in `windows/` instead (`setup.ps1`, `start.ps1 -Workers -Rasa`).

Services: API on :8000, PostgreSQL on :5432, Redis on :6379, MQTT on :1883, Rasa on :5005.

### Tests

```bash
pytest tests/                                    # ~279 tests across 25 files (~5s)
pytest tests/test_mqtt_parser.py                 # single test file
pytest tests/ -k test_nombre                     # single test by name (--strict-markers is on)
pytest tests/ --cov=nijar_dti --cov-report=html  # with coverage (fail_under=50)
```

Tests use `asyncio_mode = "auto"` — async test functions are handled automatically. Most tests need no DB (schemas, chatbot logic, helpers, health endpoints) and run in CI. `conftest.py` sets env defaults (`SECRET_KEY`, `DATABASE_URL`, `APP_ENV`) so the app can be imported without `.env`.

> Note: an `integration` marker is mentioned in `conftest.py` docstrings but is **not actually wired** — no test is decorated with `@pytest.mark.integration`, and with `--strict-markers` on, `pytest -m integration` selects zero tests. Don't rely on it.

### Linting & type checking

```bash
ruff check src/ tests/         # lint (includes isort, bandit, bugbear)
ruff format src/ tests/        # format
ruff check --fix src/ tests/   # lint + autofix
mypy src/                      # strict mode, excludes alembic/ and tests/
```

Ruff config: line-length 100, target Python 3.11. Pre-commit hooks run ruff + ruff-format + mypy on `src/`.

### Database migrations

```bash
alembic upgrade head           # apply all migrations (runs automatically on docker compose up)
alembic revision --autogenerate -m "description"  # create new migration
```

### Rasa chatbot retraining

```bash
python -m nijar_dti.workers.rasa_generator           # regenerate domain/nlu/rules/stories from FAQs seed
docker compose --profile rasa-train run --rm rasa-trainer  # train model
docker compose --profile rasa up -d rasa              # start server
```

Rasa artifacts in `rasa/` are auto-generated from `src/nijar_dti/data/seeds/faqs.py` — edit the seed, not the YAML files directly.

### Seed data loading

```bash
python -m nijar_dti.data.seed_loader   # idempotent — safe to re-run
```

Loads admin user, 14 tourism resources, 9 sensors, ~105 FAQs, data sources, clients, campaigns, Smart City verticals (lighting, containers, cameras, mobility, water, energy), and demo data (events, observations, visits, opinions, chatbot interactions, content, incidents). Runs after `alembic upgrade head` on first boot.

Default admin (from README, overridable via `INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_PASSWORD`): `admin@nijar.es` / `CambiarEnPrimerArranque#2026` (2FA required). Frontends: `http://localhost:8000/dashboard` and `/totem`.

## Architecture

### Backend structure (`src/nijar_dti/`)

The app follows a layered architecture: **routers → services → models/ORM**, all async.

- **`main.py`** — FastAPI app, lifespan (metrics refresh loop), CORS, global exception handlers, static file mounts for `/dashboard` and `/totem`
- **`config.py`** — Single `Settings` class using pydantic-settings, loaded from `.env`. Cached via `get_settings()`
- **`api/v1/`** — **17 routers** mounted under `/api/v1` (see `api/v1/router.py`). Route prefixes differ from module names: `/auth`, `/tourism`, `/data/iot`, `/data/social`, `/data/contexto`, `/prediccion`, `/rutas`, `/incidencias`, `/cms`, `/chatbot`, `/dashboards`, `/cliente`, `/campanas`, `/verticales`, `/integraciones` (from `fuentes.py`), `/usuarios`, plus health (no prefix). Auth dependency chain: `get_current_user` → `require_roles(...)` in `dependencies.py`
- **`services/`** — Business logic layer (~21 modules). Each router has a corresponding service, plus cross-cutting ones (`analitica_service.py`, `informe_render.py`, `consumo_ia_service.py`). Chatbot has three engine adapters — see Key patterns
- **`models/`** — **18 model files defining ~25 SQLAlchemy 2.0 async ORM classes** (some files hold several tables, e.g. `verticales.py`, `alumbrado.py`, `faq.py`). Base is `MappedAsDataclass, DeclarativeBase`; `_mixins.py` has `TimestampMixin` and `AuditMixin` (soft-delete `deleted_at`, `created_by`/`updated_by`)
- **`schemas/`** — Pydantic v2 request/response schemas. `common.py` has the standard `APIError` envelope
- **`core/`** — Cross-cutting (8 files): `database.py` (async engine/session), `security.py` (JWT + bcrypt + RBAC), `logging.py` (structlog JSON), `metrics.py` (Prometheus counters/histograms + domain metrics), plus `anonimizacion.py`, `ans.py` (SLA/ANS), `export.py`, `geo.py`
- **`workers/`** — Standalone processes: `mqtt_worker` (MQTT subscriber), `social_worker` (social media polling), `rasa_generator` (generates Rasa training files from FAQ seed), `contexto_backfill` (context/GA4 backfill), `informe_mensual_render` (monthly report rendering)
- **`connectors/`** — `social/` (Twitter/Facebook/Instagram API clients + NLP pipeline: language detection, sentiment, topic extraction), plus `analytics/` (GA4, forecasting), `contexto/`, and read-only REST clients for external platforms: `thingsboard.py` (IoT municipal), `bettair.py` (air quality), `openmeteo.py`, `noticias.py` (Strapi), `sigeus.py` (Distromel RSU/limpieza viaria — login + session, business endpoints pending client access). Each has `<X>_configurado()` in its service, a `scripts/verificar_<x>.py` checker and an entry in `docs/integraciones/README.md`
- **`data/seeds/`** — Initial data loaded on first boot: admin user, 14 tourism resources, 9 sensors, ~105 FAQs in 4 languages (split across `faqs.py` + `faqs_ampliacion.py` + `faqs_ampliacion2.py`, combined into `FAQS_SEED`), data sources, clients, campaigns, Smart City verticals, demo data

### Key patterns

- **Chatbot engine selector**: `CHATBOT_ENGINE` env var switches between **three** engines — `lexical`, `rasa`, `openai`. The selector is `chatbot_rasa_adapter.consultar()`, used by the chatbot router. Fallback chain: `openai` (no key/error) → `rasa` → `lexical`; Rasa failures honor `RASA_FALLBACK_TO_LEXICAL=true`. The `openai` engine (`services/chatbot_openai_adapter.py`) grounds answers on FAQs + published resources + upcoming events (config: `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-4o-mini`, `OPENAI_TIMEOUT_SECONDS`, `OPENAI_MAX_TOKENS`)
- **Consumo de IA (token/cost tracking)**: every OpenAI call is logged via `services/consumo_ia_service.py` (`registrar()`, `coste_estimado_usd()` using the `PRECIOS_USD_POR_MILLON` price table, `resumen()`) into the `ConsumoIA` model (table `consumos_ia`, migration `007`). Surfaced at `GET /api/v1/dashboards/ia/consumo` (roles `administrador_tic`, `analista_datos`, `auditor`) → `ConsumoIAResumen`. Note: `ConsumoIA` is imported in `models/__init__.py` but currently missing from `__all__`
- **Traducción automática de contenidos del tótem**: `services/traduccion_service.py` traduce con OpenAI (misma clave del chatbot) los avisos del CMS, las noticias/agenda cultural de Strapi y los eventos sin traducción cuando el tótem los pide con `?lang=en|de|fr` (`/cms/publico/totem`, `/noticias*`, `/tourism/events*`). Caché en la tabla `traducciones` (migración `017`), consumo registrado como servicio `traduccion`, y `precalentar_traducciones_loop` (cada `TRADUCCIONES_REFRESCO_MINUTOS`) deja traducidas de antemano las novedades. Sin clave o ante un fallo se sirve el texto original
- **Vista de Gobierno 2.0 (Dirección)**: `GET /api/v1/direccion/panel/{modulo}` (`resumen`, `turismo`, `alumbrado`, `agua`, `residuos`, `movilidad`, `seguridad`, `energia`; permiso `ver_resumen_municipal`) y `GET /direccion/panel/recomendaciones` (permiso `ver_recomendaciones_ia`) devuelven un `PanelDireccion` (hero, KPIs con serie y origen del dato `real`/`estimado`/`modelo`/`integrar`/`ejemplo`/`demo`/`mixto`, bloques de gráfico/ranking/calor/mapa…). `etiquetar()` corrige el origen según `estado_datos()`: las verticales cuya fuente (FD-008…FD-013 en `fuentes_datos`) no está `operativa` salen como `demo` con un `aviso` en pantalla (energía es real si hay suministros de Datadis); el contexto INE/Junta/AENA con `metadatos.sintetico` y el Social Listening en dry-run, como `demo`; visitas/chatbot/opiniones con filas de demo, como `mixto`; los eventos demo se excluyen de la agenda. Lo compone `services/direccion_panel_service.py` desde la BD (verticales, `metricas_historicas`, visitas, opiniones, contexto, consumo IA) con previsión mensual estacional (`prever_mensual`); nunca inventa datos: si falta una fuente, el bloque sale como `pendiente`. El frontend `frontend/dashboard/assets/panel-direccion.js` lo pinta con Chart.js (cdnjs, carga bajo demanda). Maquetas de diseño en `docs/propuestas/vista-gobierno/`
- **Histórico mensual real (`metricas_historicas`)**: arranca con 2 años de datos de EJEMPLO (`origen="ejemplo"`, seed). `services/metricas_historicas_service.py` captura cada día (`captura_mensual_loop`, `CAPTURA_METRICAS_HORA`, por defecto 8:30 Madrid) el último mes cerrado y completo de las fuentes reales del registro `CAPTURADORES` —hoy Datadis: `energia.consumo_kwh`/`coste_eur` (CUPS salvo alumbrado) y `alumbrado.consumo_kwh`— sustituyendo el punto de ejemplo (`origen="datadis"`/`"estimado"`, migración `018`). Manual/backfill: `python -m nijar_dti.workers.captura_metricas [--periodo AAAA-MM | --desde AAAA-MM | --estado | --dry-run]`. El panel etiqueta "Dato de ejemplo" lo que no es real, no calcula interanuales mezclando ejemplo y real, y solo prevé con 15 meses homogéneos
- **Usuarios y permisos**: admin-only user management — router `api/v1/usuarios.py` (`/usuarios`: list + `POST /invitar` with temp password + `requiere_2fa`), service `usuarios_service.py`, model `models/usuario.py`
- **Social Listening dry-run**: `SOCIAL_DRY_RUN=true` generates synthetic data without calling external APIs — useful for dev
- **RBAC**: 5 roles (`administrador_tic`, `gestor_contenidos`, `analista_datos`, `operador_smart_office`, `auditor`) — the `RolUsuario` StrEnum lives in `models/usuario.py` (not `config.py`), enforced via `require_roles(...)` reading JWT claims
- **Static frontends**: Dashboard and totem UI are plain HTML/JS in `frontend/`, served by FastAPI's StaticFiles — no build step. `frontend/dashboard/` has `index.html` + `gestion.html`, with a unified admin panel (`assets/panel-gestion.js`) hosting the Usuarios/permisos and Consumo de IA views. The totem uses custom vectorial 2D SVG iconography, multilingual `i18n.js`, and the official Ayuntamiento logo. Shared design tokens in `frontend/shared/design-tokens.css` and `.json`
- **Pre-commit hooks**: trailing-whitespace, end-of-file-fixer, check-yaml/toml, detect-private-key, ruff (with --fix), ruff-format, mypy (on `src/` only)

### Infrastructure

- **`docker-compose.yml`** — Local dev: api, db (PostGIS), redis, mqtt (Mosquitto). Workers and Rasa behind Docker profiles (`workers`, `rasa`, `rasa-train`)
- **`infra/terraform/`** — AWS deployment path (EKS, RDS PostgreSQL, ElastiCache Redis, ECR, WAF, KMS)
- **`infra/k8s/`** — Kubernetes manifests with External Secrets Operator, HPA, NetworkPolicy
- **`infra/ovh/`** — **actual production target**: OVH VPS deploy (`docker-compose.prod.yml`, `Caddyfile`, `mosquitto.prod.conf`, `.env.production.example`) — this is where the platform is deployed and operational
- **`infra/observability/`** — Prometheus + Grafana + Loki stack, 5 Grafana dashboards, 13 alert rules (`alerts.yaml`)
- **`.github/workflows/`** — `ci.yml` (tests + ruff + mypy + security scanners), `cd.yml` (OIDC → ECR → EKS with Trivy scan + Alembic migration job), `security-nightly.yml` (nightly scan), `accessibility.yml` (WCAG accessibility CI)

### Database

PostgreSQL 16 + PostGIS 3. **18 Alembic migrations** in `alembic/versions/` (`001_initial` → `018_origen_metricas_historicas`), applied incrementally (initial schema, contexto turístico, incidencias, cliente/campaña/contenidos, Smart City verticals, fuentes de datos, consumo de IA, histórico de verticales, Datadis, traducciones, origen del histórico…). Migrations run automatically on `docker compose up`. When adding tables, create a new numbered migration — don't edit `001_initial`.
