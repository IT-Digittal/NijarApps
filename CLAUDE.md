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
pytest tests/                                    # all 133 tests (~5s)
pytest tests/test_mqtt_parser.py                 # single test file
pytest tests/ --cov=nijar_dti --cov-report=html  # with coverage (fail_under=50)
```

Tests use `asyncio_mode = "auto"` — async test functions are handled automatically.

Test suite has two groups:
- **Unit tests** (default): no DB required — schemas, chatbot logic, helpers, health endpoints. These run in CI.
- **Integration tests** (`pytest -m integration`): require PostgreSQL+PostGIS running (`docker compose up -d db`).

`conftest.py` sets env defaults (`SECRET_KEY`, `DATABASE_URL`, `APP_ENV`) so the app can be imported without `.env`.

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

Loads admin user, tourism resources, sensors, FAQs, and demo data (events, observations, visits, opinions, chatbot interactions). Runs after `alembic upgrade head` on first boot.

## Architecture

### Backend structure (`src/nijar_dti/`)

The app follows a layered architecture: **routers → services → models/ORM**, all async.

- **`main.py`** — FastAPI app, lifespan (metrics refresh loop), CORS, global exception handlers, static file mounts for `/dashboard` and `/totem`
- **`config.py`** — Single `Settings` class using pydantic-settings, loaded from `.env`. Cached via `get_settings()`
- **`api/v1/`** — 8 routers mounted under `/api/v1`. Route prefixes differ from module names: `/auth`, `/tourism`, `/data/iot`, `/data/social`, `/cms`, `/chatbot`, `/dashboards`, plus health (no prefix). Auth dependency chain: `get_current_user` → `require_roles(...)` in `dependencies.py`
- **`services/`** — Business logic layer. Each router has a corresponding service. `chatbot_rasa_adapter.py` bridges the Rasa server
- **`models/`** — 11 SQLAlchemy 2.0 async ORM models (PostGIS-enabled via GeoAlchemy2). `_mixins.py` has shared columns
- **`schemas/`** — Pydantic v2 request/response schemas. `common.py` has the standard `APIError` envelope
- **`core/`** — Cross-cutting: `database.py` (async engine/session), `security.py` (JWT + bcrypt + RBAC), `logging.py` (structlog JSON), `metrics.py` (Prometheus counters/histograms + domain metrics)
- **`workers/`** — Standalone processes: `mqtt_worker` (MQTT subscriber), `social_worker` (social media polling), `rasa_generator` (generates Rasa training files from FAQ seed)
- **`connectors/social/`** — Twitter/Facebook/Instagram API clients + NLP pipeline (language detection, sentiment, topic extraction)
- **`data/seeds/`** — Initial data loaded on first boot: admin user, 14 tourism resources, 9 sensors, 22 FAQs in 4 languages

### Key patterns

- **Chatbot engine selector**: `CHATBOT_ENGINE` env var switches between `lexical` and `rasa` engines. Rasa has automatic fallback to lexical if unavailable (`RASA_FALLBACK_TO_LEXICAL=true`)
- **Social Listening dry-run**: `SOCIAL_DRY_RUN=true` generates synthetic data without calling external APIs — useful for dev
- **RBAC**: 5 roles (`administrador_tic`, `gestor_contenidos`, `analista_datos`, `operador_smart_office`, `auditor`) enforced via JWT claims
- **Static frontends**: Dashboard and totem UI are plain HTML/JS in `frontend/`, served by FastAPI's StaticFiles — no build step. Shared design tokens in `frontend/shared/design-tokens.css` and `.json`
- **Pre-commit hooks**: trailing-whitespace, end-of-file-fixer, check-yaml/toml, detect-private-key, ruff (with --fix), ruff-format, mypy (on `src/` only)

### Infrastructure

- **`docker-compose.yml`** — Local dev: api, db (PostGIS), redis, mqtt (Mosquitto). Workers and Rasa behind Docker profiles (`workers`, `rasa`, `rasa-train`)
- **`infra/terraform/`** — AWS production (EKS, RDS PostgreSQL, ElastiCache Redis, ECR, WAF, KMS)
- **`infra/k8s/`** — Kubernetes manifests with External Secrets Operator, HPA, NetworkPolicy
- **`infra/observability/`** — Prometheus + Grafana + Loki stack, 5 Grafana dashboards, 9 alert rules
- **`.github/workflows/`** — CI (tests + ruff + mypy + security scanners), CD (OIDC → ECR → EKS with rollback), nightly security scan

### Database

PostgreSQL 16 + PostGIS 3. Single Alembic migration in `alembic/versions/001_initial.py` creates 11 tables + PostGIS/pg_trgm extensions. The migration runs automatically on `docker compose up`.
