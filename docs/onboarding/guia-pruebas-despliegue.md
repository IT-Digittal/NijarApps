# Guía de pruebas de despliegue y trabajo pendiente (frontend)

| | |
|---|---|
| **Expediente** | 18962/2025 — Plataforma DTI Níjar |
| **Dirigido a** | Equipo de desarrollo |
| **Objetivo** | Qué comprobar al desplegar y qué queda por rematar en el panel y el tótem |

> Resumen rápido: el **backend está completo y probado** (264 tests). El **tótem** incorpora ya chatbot, voz, eventos y planificador. En el **panel (dashboard)** hay varios endpoints nuevos del backend que **todavía no están cableados en la interfaz** (ver §4). Esto es lo principal que queda visible por hacer.

---

## 1. Arranque local (Docker)

```bash
cp .env.example .env
./scripts/dev_up.sh            # api + db + redis + mqtt
docker compose up api
# Con workers y Rasa:
./scripts/dev_up.sh --workers --rasa
```

`docker compose up` ejecuta automáticamente `alembic upgrade head` (3 migraciones: esquema inicial, contexto, incidencias) y, en primer arranque, los seeds.

**Verifica el arranque:**
- API: <http://localhost:8000/api/v1/health> → `{"status":"ok"...}`
- Swagger: <http://localhost:8000/docs> (deben verse ~45 endpoints)
- Dashboard: <http://localhost:8000/dashboard>
- Tótem: <http://localhost:8000/totem>
- Credenciales admin: `admin@nijar.es` / `CambiarEnPrimerArranque#2026`

**Seeds que deben cargar** (logs del contenedor):
- 1 admin, 14 recursos, 9 sensores, **105 FAQs**, eventos/observaciones/opiniones/visitas/chatbot demo y **8 incidencias demo** (mes anterior).

---

## 2. Smoke test del backend

```bash
# Tests (sin BBDD)
pytest tests/ -m "not integration"          # 264 en verde

# Login y token
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -d 'username=admin@nijar.es&password=CambiarEnPrimerArranque#2026' | jq -r .access_token)

# Endpoints nuevos (deben responder 200 con datos demo)
curl -s "localhost:8000/api/v1/data/social/kpis/nps" -H "Authorization: Bearer $TOKEN"
curl -s "localhost:8000/api/v1/data/social/kpis/composicion-linguistica" -H "Authorization: Bearer $TOKEN"
curl -s "localhost:8000/api/v1/prediccion/afluencia?metrica=totem" -H "Authorization: Bearer $TOKEN"
curl -s "localhost:8000/api/v1/prediccion/validacion?metrica=chatbot" -H "Authorization: Bearer $TOKEN"
curl -s "localhost:8000/api/v1/data/contexto/factor-expansion" -H "Authorization: Bearer $TOKEN"
curl -s "localhost:8000/api/v1/incidencias/ans?desde=2026-05-01T00:00:00Z&hasta=2026-06-01T00:00:00Z" -H "Authorization: Bearer $TOKEN"
curl -s "localhost:8000/api/v1/dashboards/monthly-report?year=2026&month=5" -H "Authorization: Bearer $TOKEN"

# Canal público (sin token): tótem
curl -s -X POST localhost:8000/api/v1/chatbot/query -H 'Content-Type: application/json' \
  -d '{"sesion_id":"t1","canal":"totem","idioma":"es","pregunta":"¿qué playas hay cerca?"}'
curl -s -X POST localhost:8000/api/v1/rutas/planificar -H 'Content-Type: application/json' \
  -d '{"lat":36.847,"lon":-2.041,"max_paradas":5,"modo":"bici","idioma":"es"}'
curl -s "localhost:8000/api/v1/rutas/recomendaciones?idioma=en"
```

Si falta cargar contexto histórico, ejecútalo: `python -m nijar_dti.workers.contexto_backfill --dry-run --output /tmp/ctx.json` y `POST /data/contexto/ingest`.

---

## 3. Pruebas del panel (dashboard) — qué ya funciona

Login OAuth2 y navega por las secciones (`data-section` en `frontend/dashboard/index.html`):

| Sección | Qué comprobar | Endpoint | Estado UI |
|---------|---------------|----------|-----------|
| Resumen | KPIs generales, refresco | varios | ✅ |
| Catálogo | CRUD de recursos | `/tourism/resources` | ✅ |
| Eventos | Listado/alta de eventos | `/tourism/events` | ✅ |
| Smart Office | Sensores, ambiental, series | `/dashboards/smart-office/*` | ✅ |
| Big Data | Sentimiento, share-of-voice, temas | `/data/social/*` | ✅ |
| Chatbot | Telemetría | `/chatbot/telemetry` | ✅ |
| Mapa | POIs en Leaflet | `/tourism/resources` | ✅ |
| Tótems | Uso e interacciones | `/dashboards/totems/usage` | ✅ |
| Usuarios / Config | Gestión | auth | ✅ |

---

## 4. Endpoints nuevos en el PANEL — todos cableados

Todos los endpoints nuevos del backend están ya integrados en el dashboard:

| Funcionalidad | Endpoint | Dónde en el panel |
|---------------|----------|-------------------|
| Incidencias / ANS + Informe mensual (C.1) | `/incidencias`, `/incidencias/ans`, `/dashboards/monthly-report` | Sección «Mantenimiento · ANS» |
| Índice tipo NPS | `/data/social/kpis/nps` | KPI en sección Social Listening |
| Composición lingüística de visitantes | `/data/social/kpis/composicion-linguistica` | Gráfico donut en Social Listening |
| Predicción de afluencia | `/prediccion/afluencia` | Sección «Predicción y contexto» (línea + bandas) |
| Validación MAPE / anomalías | `/prediccion/validacion`, `/prediccion/anomalias` | KPIs en «Predicción y contexto» |
| Contexto histórico (INE/Junta/AENA) | `/data/contexto/series`, `/factor-expansion` | Sección «Predicción y contexto» |

**Patrón usado** (replicable para futuras secciones):
1. **api-client.js** → método por endpoint (`monthlyReport`, `nps`, `prediccionAfluencia`, `contextoSerie`…).
2. **index.html** → ítem de nav `data-section="..."` + `<section data-section-content="...">` con KPIs (`data-kpi`), `<canvas>`, tablas (`.data-table`), botones (`.btn`).
3. **dashboard.js** → función `loadX()` registrada en el mapa `loaders` de `switchSection`; usa `setKPI`, `renderChart` (Chart.js), `escapeHtml`, `setBanner`.

**A verificar al desplegar** (con datos demo cargados):
- *Social Listening*: aparece el KPI **NPS** y el donut de **composición lingüística**.
- *Predicción y contexto*: la curva de afluencia con bandas, el **MAPE**, el nº de **anomalías** y el **factor de expansión**; la serie de **pernoctaciones INE** requiere haber ejecutado el backfill (`POST /data/contexto/ingest`; si está vacía, el gráfico queda en blanco sin error).
- *Mantenimiento · ANS*: disponibilidad por componente, cumplimiento ANS, incidencias y descarga del informe `.md`.

> Respeta los design tokens (`frontend/shared/design-tokens.css`) y la accesibilidad (roles ARIA, contraste).

---

## 5. Pruebas del TÓTEM — qué ya funciona y qué confirmar

Abre <http://localhost:8000/totem>. Comprueba:

| Función | Cómo probar | Estado |
|---------|-------------|--------|
| i18n ES/EN/DE/FR | Botones de idioma; recarga contenidos | ✅ |
| Accesibilidad | Botón A+ (texto grande) y ◐ (alto contraste) | ✅ |
| Categorías | Rutas / Playas / Patrimonio / Servicios / **Eventos** / Emergencias | ✅ |
| Detalle POI | Click en tarjeta → modal | ✅ |
| Chatbot (texto) | Escribir pregunta → respuesta (usa `/chatbot/query`) | ✅ |
| **Voz — entrada (STT)** | Botón 🎤; **requiere Chrome/Edge** (Web Speech API) y permiso de micrófono | ✅* |
| **Voz — lectura (TTS)** | Botón 🔊 lee la respuesta | ✅* |
| Planificador de ruta | Botón "Sugerir ruta cercana" | ✅ |
| Recomendaciones | Botón "¿Qué visitar hoy?" | ✅ |
| Inactividad | A los 60 s vuelve al estado inicial | ✅ |

`*` La voz es **mejora progresiva**: si el navegador no soporta Web Speech API (p. ej. Firefox), los botones 🎤/🔊 se ocultan automáticamente y el resto funciona igual. En el **hardware real del tótem** hay que verificar el navegador en modo kiosco y el micrófono/altavoz físicos.

### Pendiente en el tótem
- Confirmar **STT/TTS en el navegador real del kiosco** (no todos soportan Web Speech API; valorar motor alternativo si el del tótem no lo trae).
- **Meteo en vivo**: hoy muestra etiqueta estática (el endpoint meteo requiere auth y el tótem es canal público). Si se quiere meteo real, exponer un endpoint público de solo lectura.
- **Banderas/aforo en tiempo real** (A.2 "ejecución de acciones"): el flujo de actuación está documentado pero no hay aún panel de control de banderas/aforo en vivo.

---

## 6. Pendiente fuera del frontend (recordatorio)

- **Conectores RRSS reales**: hoy en `SOCIAL_DRY_RUN=true`. Requiere tokens del Ayuntamiento (ver `.env.example`).
- **DTI externo** (`plataforma.nijardti.com`): integración bloqueada a la espera de URL/API.
- **Reviews** (TripAdvisor/Google/HolidayCheck) y **visualizaciones de flujo**: planificadas para C.1.
- **Tótems físicos / obra civil / autorizaciones del Parque** y **SAT/pentest/formación**: parte física y administrativa.

---

## 7. Notas para el equipo (no son errores)

- `ruff check` muestra avisos preexistentes y aceptados: `UP017` (`timezone.utc`), `N818` (`NotFound`/`Conflict`), `S311` (random en datos demo) y `E501` en `data/seeds/*` (textos largos, exento en `pyproject`). No bloquean.
- En este entorno los tests se ejecutan con `-o addopts=""` si no está `pytest-cov`. En CI usan la config completa.
- Mapa de funcionalidades y endpoints: `docs/MAPA-FUNCIONAL.md`. Checklist de SAT: `docs/operations/checklist-evidencias-sat.md`.
