# Manual técnico del Backend — Plataforma DTI Níjar

| | |
|---|---|
| **Expediente** | 18962/2025 |
| **Versión** | 1.0 (consolidado tras Hito 4) |
| **Audiencia** | Equipo técnico del Ayuntamiento, integradores, auditores ENS |

Este manual describe en detalle el backend de la plataforma: estructura del código, capas, contratos, mecanismos transversales y cómo extender el sistema con nuevos verticales Smart City sin tocar el núcleo.

---

## 1. Visión general del backend

El backend está diseñado en **capas claramente separadas** siguiendo el principio de responsabilidad única:

```
src/nijar_dti/
├── main.py              ← Bootstrap FastAPI (lifespan, middleware, CORS, /metrics)
├── config.py            ← Settings Pydantic (variables de entorno)
├── core/
│   ├── database.py      ← Engine async, AsyncSessionLocal, get_db
│   ├── security.py      ← bcrypt, JWT (access+refresh)
│   ├── logging.py       ← structlog con salida JSON
│   └── metrics.py       ← Prometheus (Counter, Histogram, Gauges)
├── models/              ← SQLAlchemy 2.0 ORM (dataclass-style)
├── schemas/             ← Pydantic v2 (request/response, validaciones)
├── services/            ← Lógica de negocio (capa transaccional)
├── api/v1/              ← Routers FastAPI (HTTP layer)
├── connectors/          ← Integraciones externas (MQTT, RRSS, GA4)
├── data/seeds/          ← Seeds de inicialización
├── mqtt/                ← Parser y subscriber MQTT
├── workers/             ← Procesos de background (subscribers, schedulers)
└── ...
```

### Principios arquitectónicos

1. **Layered architecture estricta**: la capa HTTP solo conoce `services`, `services` solo conoce `models` y `schemas`, y los `connectors` no acceden nunca directamente a los `services`.
2. **Async-first**: toda operación de I/O (BBDD, HTTP, MQTT) es asíncrona.
3. **Stateless**: la API no mantiene estado en memoria entre peticiones; el estado vive en BBDD/Redis.
4. **Idempotencia**: las ingestas (MQTT, Social Listening) son idempotentes por clave natural.
5. **Failure isolation**: un fallo en un conector externo (Rasa, GA4, X) no debe tumbar la API.

---

## 2. Capa de modelos (`src/nijar_dti/models/`)

Modelos SQLAlchemy 2.0 con `MappedAsDataclass`, herencia del `AuditMixin` para trazabilidad ENS.

### Mixin de auditoría

```python
class AuditMixin(TimestampMixin):
    created_by: Mapped[UUID | None] = mapped_column(..., kw_only=True)
    updated_by: Mapped[UUID | None] = mapped_column(..., kw_only=True)
    deleted_at: Mapped[datetime | None] = mapped_column(..., kw_only=True)
```

`kw_only=True` evita conflictos del orden de campos en los dataclasses heredados.

### Catálogo de entidades

| Tabla | Modelo | Clave natural | URN FIWARE |
|-------|--------|---------------|------------|
| `usuario` | `Usuario` | email | — |
| `recurso_turistico` | `RecursoTuristico` | urn | `urn:ngsi-ld:RecursoTuristico:nijar:<slug>` |
| `evento_turistico` | `EventoTuristico` | urn | `urn:ngsi-ld:EventoTuristico:nijar:<slug>` |
| `servicio` | `Servicio` | urn | `urn:ngsi-ld:Servicio:nijar:<slug>` |
| `sensor` | `Sensor` | urn | `urn:ngsi-ld:Device:nijar:<measure>:<slug>` |
| `observacion` | `Observacion` | (sensor_id, observado_en) | — |
| `opinion` | `Opinion` | (fuente, fuente_id_externo) | — |
| `faq` | `FAQ` | intent | — |
| `interaccion_chatbot` | `InteraccionChatbot` | id | — |
| `contenido` | `Contenido` | id | — |
| `visita` | `Visita` | id | — |

### Soft delete y auditoría

Todas las tablas soportan **soft delete** vía `deleted_at`. Las queries usan filtros explícitos:

```python
stmt = select(RecursoTuristico).where(RecursoTuristico.deleted_at.is_(None))
```

---

## 3. Capa de schemas (`src/nijar_dti/schemas/`)

Pydantic v2 con validaciones estrictas. Cada módulo cubre un área funcional:

| Módulo | Cubre |
|--------|-------|
| `common.py` | `APIError`, paginación, respuestas comunes |
| `auth.py` | Login, refresh, tokens, perfil de usuario |
| `tourism.py` | Recursos, eventos, servicios + GeoJSON |
| `iot.py` | Sensores, observaciones, ingesta, queries históricas |
| `social.py` | Opiniones, KPIs sentimiento, share-of-voice |
| `cms.py` | Contenidos multicanal, plantillas, publicación |
| `chatbot.py` | Query, respuesta, feedback, telemetría |
| `dashboards.py` | KPIs Smart Office, Big Data, informe mensual C.1 |

### Validaciones destacables

```python
URN_PATTERN = r"^urn:ngsi-ld:[A-Za-z]+:nijar:[a-z0-9-]+(?::[a-z0-9-]+)?$"

class RecursoBase(BaseModel):
    urn: str = Field(..., pattern=URN_PATTERN)
    nombre: str = Field(..., min_length=2, max_length=255)
    nombre_i18n: dict[str, str] | None = None  # ES/EN/DE/FR
    ubicacion: GeoJSONPoint | None = None
```

`GeoJSONPoint` valida `[lon, lat]` con bounds plausibles para el término municipal de Níjar. Las fechas de eventos validan `fecha_inicio < fecha_fin`. Los enums están tipados (no strings sueltos).

---

## 4. Capa de servicios (`src/nijar_dti/services/`)

Cada servicio agrupa la lógica de un dominio funcional. Todas las funciones son `async`. Los services **siempre reciben una sesión** explícita y **nunca hacen commit por sí mismos** salvo en flujos batch (worker, ingesta masiva); el commit se delega al caller (router) para preservar la atomicidad.

| Servicio | Responsabilidad |
|----------|-----------------|
| `auth_service` | Login (bcrypt), emisión y refresco de JWT, gestión de usuarios |
| `tourism_service` | CRUD recursos, eventos y servicios con filtros geoespaciales `ST_DWithin` |
| `iot_service` | Catálogo sensores, ingesta validada, histórico paginado |
| `social_service` | KPIs sentimiento, share-of-voice, top temas, series temporales |
| `cms_service` | Publicación multicanal con cálculo automático de estado |
| `chatbot_service` | Motor lexical: tokenización, similitud Jaccard, grounding 3 niveles |
| `chatbot_rasa_adapter` | Cliente HTTP del servidor Rasa con failover al lexical |
| `dashboards_service` | Agregaciones SQL para los dashboards y el informe mensual |

### Patrón de servicio

```python
async def crear_recurso(db: AsyncSession, payload: RecursoIn) -> RecursoOut:
    if await _existe_urn(db, payload.urn):
        raise HTTPException(status_code=409, detail="URN ya existe")
    recurso = RecursoTuristico(**payload.model_dump())
    db.add(recurso)
    await db.flush()
    await db.refresh(recurso)
    return RecursoOut.model_validate(recurso)
```

El router luego hace `await db.commit()` solo si el handler completa sin excepciones.

---

## 5. Capa HTTP (`src/nijar_dti/api/v1/`)

Cada router declara explícitamente los roles que pueden invocar cada endpoint:

```python
@router.post("/resources", response_model=RecursoOut, status_code=201)
async def crear_recurso(
    payload: RecursoIn,
    db: AsyncSession = Depends(get_db),
    user: Usuario = Depends(require_role(["gestor_contenidos", "administrador_tic"])),
):
    recurso = await tourism_service.crear_recurso(db, payload)
    await db.commit()
    return recurso
```

### Manejo global de errores

`main.py` registra handlers que producen siempre el schema `APIError` uniforme:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "El campo 'urn' no cumple el patrón requerido",
  "details": { "field": "urn", ... },
  "request_id": "uuid"
}
```

Esto facilita el consumo desde cualquier cliente y deja una traza única para el SOC.

---

## 6. Mecanismos transversales

### Logging estructurado

```python
from nijar_dti.core.logging import get_logger
log = get_logger(__name__)
log.info("Recurso creado", urn=recurso.urn, user_id=user.id)
```

Salida JSON apta para Loki/CloudWatch:

```json
{"timestamp": "2026-05-05T14:23:11Z", "level": "info", "logger": "nijar_dti.services.tourism_service", "event": "Recurso creado", "urn": "urn:ngsi-ld:RecursoTuristico:nijar:playa-monsul", "user_id": "..."}
```

### Métricas Prometheus

Definidas en `core/metrics.py` (registry propio, evita interferir con tests):

- `nijar_http_requests_total{method, path, status}` (Counter)
- `nijar_http_request_duration_seconds_bucket{method, path}` (Histogram)
- `nijar_sensores_total{estado}` (Gauge)
- `nijar_observaciones_ultima_hora_total`, `nijar_observaciones_invalidas_ultima_hora_total`
- `nijar_chatbot_interacciones_ultimas_24h_total{nivel_confianza}`
- `nijar_opiniones_ultimas_24h_total{fuente, sentimiento}`
- `nijar_db_up`, `nijar_metrics_last_refresh_timestamp`

El refresco de los gauges de dominio se hace en un task `metrics_loop()` lanzado en el `lifespan` de FastAPI cada 60 segundos.

### Configuración (`config.py`)

`Settings` Pydantic con `env_file=".env"` y `case_sensitive=False`. Acceso vía `get_settings()` cacheado. Validación al arranque: si falta `SECRET_KEY` o `DATABASE_URL`, la app no arranca.

---

## 7. Conectores externos (`src/nijar_dti/connectors/`)

### Patrón común

Cada conector implementa una interfaz mínima:

```python
class ExternalConnector(ABC):
    @property
    def is_configured(self) -> bool: ...
    async def fetch(self, since: datetime | None = None) -> list[Item]: ...
```

Todos soportan **modo `dry-run`** que devuelve datos sintéticos coherentes cuando faltan credenciales. Esto permite:

- Desarrollo sin tokens.
- Demos al Ayuntamiento sin necesidad de cuentas reales.
- Tests deterministas.

### Inventario

| Conector | Plataforma | Variables clave |
|----------|------------|-----------------|
| `social/twitter.py` | X (Twitter API v2 Recent Search) | `TWITTER_BEARER_TOKEN`, `TWITTER_SEARCH_QUERY` |
| `social/facebook.py` | Facebook Graph API | `FACEBOOK_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID` |
| `social/instagram.py` | Instagram Hashtag Search | `INSTAGRAM_BUSINESS_ACCOUNT_ID`, `INSTAGRAM_HASHTAGS` |
| `analytics/ga4.py` | Google Analytics 4 Reporting v1beta | `GA4_PROPERTY_ID`, `GA4_SERVICE_ACCOUNT_JSON` |

### Pipeline NLP propio (`social/nlp.py`)

Funciones puras (sin estado), aptas para tests deterministas:

- `detectar_idioma(texto, default="es")` — heurística por marcadores frecuentes.
- `analizar_sentimiento(texto, idioma)` — lexicón pos/neg con manejo de negación.
- `extraer_temas(texto, max_temas=5)` — vocabulario controlado de 10 temas.
- `detectar_entidades(texto)` — mapeo a URNs FIWARE.

---

## 8. Subscriber MQTT (`src/nijar_dti/mqtt/`)

### Componentes

- **`parser.py`** — Convierte `(topic, payload)` en `ObservacionIn` validado. No tiene dependencias de BBDD ni de paho-mqtt; eso lo hace 100% testable en unit tests.
- **`subscriber.py`** — Cliente paho-mqtt con bridging async. Patrón:
  - paho ejecuta callbacks síncronos.
  - Cada callback envía la coroutine de persistencia con `asyncio.run_coroutine_threadsafe()` a un loop asyncio que gira en un hilo dedicado.
  - El callback retorna inmediatamente; las métricas se contabilizan vía `future.add_done_callback()`.

### Topics aceptados

```
nijar/sensors/<slug>/<measurement>
```

Ejemplos:
- `nijar/sensors/smartoffice-01/co2`
- `nijar/sensors/totem-rodalquilar/aforo`

### Payload aceptado

Dos formatos válidos:

```json
{ "valor": 825.5, "unidades": "ppm", "observado_en": "2026-05-05T10:23:45Z" }
```

```json
{ "valores": { "temp_c": 24.5, "hum_%": 62 }, "observado_en": 1714900425 }
```

El parser acepta timestamps ISO con o sin Z, epoch en segundos o milisegundos, y omitir el campo (usa `now()` UTC).

---

## 9. Workers (`src/nijar_dti/workers/`)

Procesos autónomos que se despliegan como Deployments separados en Kubernetes:

| Worker | Función | Despliegue |
|--------|---------|------------|
| `mqtt_worker.py` | Subscriber MQTT (singleton) | Deployment 1 réplica + estrategia Recreate |
| `social_worker.py` | Polling RRSS cada 15 min | Deployment 1 réplica |
| `rasa_generator.py` | Genera artefactos Rasa desde FAQs | Job manual o pre-deploy |

Todos manejan SIGINT/SIGTERM para shutdown limpio (Kubernetes graceful shutdown).

---

## 10. Tests (`tests/`)

142 tests unitarios pasando, cobertura 56%. Estructura:

| Archivo | Cubre |
|---------|-------|
| `test_schemas.py` | Patrones URN FIWARE, GeoJSON, fechas, enums |
| `test_security.py` | bcrypt + JWT (access + refresh) |
| `test_chatbot.py` | Motor lexical: tokenización, Jaccard, niveles |
| `test_chatbot_rasa.py` | Adapter Rasa, mapeo de confianza, generador de artefactos |
| `test_seeds.py` | Coordenadas, URNs únicas, cobertura EN >80%, FAQs emergencias |
| `test_api_endpoints.py` | Todas las rutas en OpenAPI, esquema APIError |
| `test_health.py` | Endpoints de salud y readiness |
| `test_mqtt_parser.py` | Topics, payloads JSON, timestamps en formatos varios |
| `test_social_nlp.py` | Detección idioma, sentimiento, temas, entidades |
| `test_social_connectors.py` | Conectores en dry-run, idiomas cubiertos |
| `test_ga4.py` | Conector GA4 dry-run, carga de service-account |

### Ejecución

```bash
pytest tests/                       # todos
pytest tests/test_schemas.py -v     # uno
pytest tests/ --cov=nijar_dti       # con cobertura
pytest tests/ -k "chatbot"          # filtro por nombre
```

---

## 11. Cómo añadir un nuevo vertical Smart City

El sistema está pensado para que los siguientes verticales (residuos, alumbrado, aforo en parking, calidad del aire perimetral...) se añadan **sin tocar el núcleo**. Pasos típicos:

1. **Modelar la entidad** en `models/` heredando de `AuditMixin`. Si es un dato GIS, añadir campo `Geometry`.
2. **Definir schemas** en `schemas/<area>.py`.
3. **Crear migración Alembic** con `alembic revision --autogenerate`.
4. **Añadir servicio** en `services/<area>_service.py` (CRUD, queries, agregaciones).
5. **Definir router** en `api/v1/<area>.py` con sus dependencias de RBAC.
6. **Registrar router** en `api/v1/router.py`.
7. **Si hay nuevos sensores**, añadirlos al seed `data/seeds/sensores.py` y al patrón MQTT (no requiere cambios de código si siguen `nijar/sensors/<slug>/<measure>`).
8. **Tests** en `tests/test_<area>.py`.

No hace falta modificar `main.py`, ni la observabilidad, ni el chatbot — el dashboard puede consumir el nuevo endpoint añadiendo una pestaña.

---

## 12. Comandos útiles

```bash
# Desarrollo local
./scripts/dev_up.sh --workers --rasa
docker compose up api

# Tests
pytest tests/ --no-cov -q

# Migración nueva
alembic revision --autogenerate -m "add table xyz"
alembic upgrade head

# Seeds
python -m nijar_dti.data.seed_loader

# Generar artefactos Rasa desde FAQs
python -m nijar_dti.workers.rasa_generator

# Publicar mensajes de prueba al broker MQTT
python scripts/mqtt_publish_test.py --count 20

# Lanzar workers manualmente
python -m nijar_dti.workers.mqtt_worker
python -m nijar_dti.workers.social_worker

# Ver métricas Prometheus
curl http://localhost:8000/metrics

# Validar OpenAPI
curl http://localhost:8000/openapi.json | jq .info
```

---

## 13. Cumplimiento ENS por componente del backend

| Medida ENS | Componente backend | Implementación |
|------------|---------------------|------------------|
| `op.acc.5` Mecanismos de autenticación | `core/security.py` + `auth_service` | bcrypt cost 12 + JWT con rotación + 2FA admin |
| `op.acc.6` Acceso local y remoto | Routers + `require_role` | RBAC con 5 roles, scope por endpoint |
| `op.exp.1` Inventario de activos | `models/` | Catálogo declarativo en código |
| `op.exp.2` Configuración de seguridad | `config.py` | Variables explícitas, sin valores hardcoded |
| `op.exp.3` Gestión de la configuración | Git + Terraform | IaC versionado |
| `op.exp.4` Mantenimiento | CI nightly | Escaneo automático de CVE diario |
| `op.exp.6` Protección frente a malware | Trivy + bandit + semgrep | Bloqueante en CI |
| `op.exp.8` Registro de actividad | `core/logging.py` + `AuditMixin` | structlog JSON + columnas auditoría |
| `op.exp.9` Gestión de incidentes | Alertas Prometheus + AlertManager | 9 reglas alineadas con SLAs |
| `op.cont.1` Análisis de impacto | `docs/operations/disaster-recovery.md` | RTO/RPO documentados |
| `op.cont.2` Plan de continuidad | `docs/operations/business-continuity.md` | Escenarios y procedimientos |
| `op.cont.3` Pruebas periódicas | Drills trimestrales | Restore de BBDD + failover Multi-AZ |
| `mp.com.4` Protección de la integridad | TLS 1.2+ obligatorio | ACM + ALB + RDS encrypted |
| `mp.info.5` Limpieza de documentos | Soft delete + retention | Borrado seguro al fin de C.1 |
