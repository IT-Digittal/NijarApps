# Estado del proyecto y plan de pruebas para el equipo (Dev & QA)

| | |
|---|---|
| **Proyecto** | DTI Níjar — Exp. 18962/2025 |
| **Dirigido a** | Equipo de desarrollo y test |
| **Supuesto** | Tenéis ya desplegados en local los últimos cambios |
| **Rama integrada** | `Hugo` (última) |

> Objetivo: que sepáis **en qué estado está el proyecto** y **qué se puede probar ya en local**, con pasos concretos y el resultado esperado (los datos demo se cargan en el primer arranque).

---

## 1. Estado actual (resumen)

- **Backend completo y probado**: API REST (~45 endpoints), **264 tests unitarios en verde**.
- **Panel (dashboard)**: todas las secciones cableadas, incluidas las nuevas (NPS, composición lingüística, predicción, contexto, mantenimiento/ANS).
- **Tótem**: chatbot, **voz (STT/TTS)**, eventos y planificador de rutas.
- **Datos demo** cargados al arrancar: 14 recursos, 9 sensores, **105 FAQs**, eventos/observaciones/opiniones/visitas/chatbot e **incidencias del mes anterior**.

### Qué NO se puede probar en local todavía (depende de terceros)
- **RRSS reales** (X/Facebook/Instagram): funcionan en **modo dry-run** (datos sintéticos) hasta tener tokens del Ayuntamiento.
- **GA4 real**: dry-run hasta tener credenciales.
- **DTI externo** (`plataforma.nijardti.com`): integración pendiente de acceso.
- **Tótem físico** y **voz** en navegadores sin Web Speech API (usar **Chrome/Edge**).

---

## 2. Arranque y verificación rápida

```bash
docker compose up api          # ya desplegado en vuestras máquinas
pytest tests/ -m "not integration"   # debe dar 264 passed
```

| Recurso | URL |
|---------|-----|
| Health | http://localhost:8000/api/v1/health |
| Swagger (probar API) | http://localhost:8000/docs |
| Panel | http://localhost:8000/dashboard |
| Tótem | http://localhost:8000/totem |
| Métricas Prometheus | http://localhost:8000/metrics |

Credenciales panel: `admin@nijar.es` / `CambiarEnPrimerArranque#2026`.

> Si una sección del panel sale vacía, revisad que los **seeds** se cargaron (logs del contenedor) o ejecutad `python -m nijar_dti.data.seed_loader`.

---

## 3. Plan de pruebas — Backend (API)

Probar desde **Swagger** (`/docs`) o con `curl`. Obtener token:

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/v1/auth/login \
  -d 'username=admin@nijar.es&password=CambiarEnPrimerArranque#2026' | jq -r .access_token)
```

| ID | Área | Endpoint | Resultado esperado |
|----|------|----------|--------------------|
| B01 | Auth | `POST /auth/login`, `GET /auth/me` | Token válido; datos del admin |
| B02 | Turismo | `GET /tourism/resources?publicado=true` | ≥14 recursos con coordenadas |
| B03 | Turismo | `GET /tourism/events` | Eventos demo |
| B04 | IoT | `GET /data/iot/sensors` | 9 sensores |
| B05 | IoT | `GET /data/iot/observations` | Observaciones demo (48 h) |
| B06 | Social | `GET /data/social/kpis/sentiment` | Serie de sentimiento |
| B07 | Social | `GET /data/social/kpis/share-of-voice` | % por fuente |
| B08 | Social | `GET /data/social/topics` | Top temas |
| B09 | Social | `GET /data/social/kpis/nps` | NPS (proxy) con componentes |
| B10 | Social | `GET /data/social/kpis/composicion-linguistica` | % por idioma + k-anonimato |
| B11 | Contexto | `GET /data/contexto/factor-expansion` | factor ≈ 6.7 (preliminar) o calibrado |
| B12 | Contexto | `GET /data/contexto/series?fuente=ine_eoh&indicador=pernoctaciones` | Serie (si se hizo backfill) |
| B13 | Predicción | `GET /prediccion/afluencia?metrica=totem` | 14 puntos con banda de confianza |
| B14 | Predicción | `GET /prediccion/validacion?metrica=chatbot` | MAPE + cumple_umbral |
| B15 | Predicción | `GET /prediccion/anomalias?metrica=totem` | Lista de anomalías (puede ser vacía) |
| B16 | Rutas | `POST /rutas/planificar` (lat 36.847, lon -2.041) | Itinerario ordenado + distancia/duración |
| B17 | Rutas | `GET /rutas/recomendaciones?idioma=en` | Eventos + recursos en inglés |
| B18 | Chatbot | `POST /chatbot/query` (4 idiomas) | Respuesta + `nivel_confianza` + sugerencias |
| B19 | Chatbot | `GET /chatbot/telemetry` | Sesiones, resolución, idiomas, top intents |
| B20 | CMS | `GET /cms/content?canal=totem` | Contenidos del canal |
| B21 | Incidencias | `GET /incidencias?desde=2026-05-01T00:00:00Z&hasta=2026-06-01T00:00:00Z` | 8 incidencias demo |
| B22 | Incidencias | `GET /incidencias/ans?desde=...&hasta=...` | Cumplimiento ANS por severidad |
| B23 | C.1 | `GET /dashboards/monthly-report?year=2026&month=5` | Disponibilidad real + incidencias |

### Casos concretos a verificar en el chatbot (grounding)
```bash
# Alta confianza (FAQ oficial)
curl -s -X POST localhost:8000/api/v1/chatbot/query -H 'Content-Type: application/json' \
 -d '{"sesion_id":"q1","canal":"totem","idioma":"es","pregunta":"¿qué playas hay cerca?"}'
# Fuera de dominio (debe responder fallback, no inventar)
curl -s -X POST localhost:8000/api/v1/chatbot/query -H 'Content-Type: application/json' \
 -d '{"sesion_id":"q2","canal":"web","idioma":"en","pregunta":"what is the bitcoin price?"}'
```
Esperado: la 1ª responde con fuente y `nivel_confianza` alta/media; la 2ª responde **fuera de dominio** sin fabricar información.

### Backfill de contexto (para que B12 y la serie INE del panel tengan datos)
```bash
python -m nijar_dti.workers.contexto_backfill --dry-run --output /tmp/ctx.json
# y luego POST /data/contexto/ingest con ese JSON (rol administrador_tic o analista_datos)
```

---

## 4. Plan de pruebas — Panel (dashboard)

Login y recorrer el menú lateral. Por cada sección, comprobar que carga sin errores y muestra datos demo:

| ID | Sección | Qué verificar |
|----|---------|---------------|
| P01 | Dashboard (resumen) | KPIs ambientales y contadores; refresco |
| P02 | Recursos turísticos | Tabla, filtros y **alta/edición** (CRUD) |
| P03 | Eventos | Listado y alta de eventos |
| P04 | Smart Office | Sensores, serie ambiental, alertas |
| P05 | Social Listening | Sentimiento, share-of-voice, temas, **KPI NPS** y **donut de composición lingüística** |
| P06 | Chatbot · FAQs | Telemetría: sesiones, resolución, idiomas, top intents |
| P07 | Mapa | POIs publicados sobre Leaflet |
| P08 | Tótems | Uso e interacciones |
| P09 | **Mantenimiento · ANS** | Disponibilidad por componente, tabla ANS, incidencias; **generar y descargar el informe `.md`** |
| P10 | **Predicción y contexto** | Curva de afluencia con bandas, KPIs (MAPE, anomalías, factor); cambiar la **métrica**; serie INE (si hay backfill) |
| P11 | Usuarios y permisos | Gestión de usuarios/roles |
| P12 | Configuración | Parámetros |

> En P09 y P10, con los datos demo: disponibilidad media ≈ **99.3 %**, ANS de "alta" ≈ **66.7 %** (1 incumplimiento), y la predicción debe dibujar la curva + bandas.

---

## 5. Plan de pruebas — Tótem

Abrir `/totem` (mejor en **Chrome/Edge** para la voz):

| ID | Qué probar | Resultado esperado |
|----|-----------|--------------------|
| T01 | Cambio de idioma ES/EN/DE/FR | Toda la UI y los contenidos cambian |
| T02 | Accesibilidad: botón **A+** y **alto contraste ◐** | Texto grande / alto contraste |
| T03 | Categorías (Rutas/Playas/Patrimonio/Servicios/**Eventos**/Emergencias) | Carga tarjetas; Eventos lista eventos |
| T04 | Detalle de un POI | Abre modal con descripción y dirección |
| T05 | Chatbot (texto) | Respuesta correcta en el idioma activo |
| T06 | **Voz — micrófono 🎤** | Dicta la pregunta (pide permiso de micro) |
| T07 | **Voz — altavoz 🔊** | Lee la respuesta en voz alta |
| T08 | **Planificador**: "Sugerir ruta cercana" | Lista ordenada de paradas + distancia/duración |
| T09 | **Recomendaciones**: "¿Qué visitar hoy?" | Eventos próximos + lugares recomendados |
| T10 | Inactividad 60 s | Vuelve al estado inicial |

> Si el navegador no soporta Web Speech API (p. ej. Firefox), los botones 🎤/🔊 **se ocultan** automáticamente: es el comportamiento esperado, no un fallo.

---

## 6. Pruebas automatizadas

```bash
pytest tests/ -m "not integration"      # 264 en verde (rápido, sin BBDD)
pytest -m integration                    # requiere PostgreSQL+PostGIS
ruff check src/ tests/                   # estilo
```

**Avisos de lint esperados (no son errores):** `UP017` (`timezone.utc`), `N818` (`NotFound`/`Conflict`), `S311` (random en datos demo), `E501` en `data/seeds/*` (exento). No bloquean.

---

## 7. Cómo reportar incidencias encontradas

- Preferible: registrarlas en el propio **ticketing** del sistema → `POST /api/v1/incidencias` (severidad, componente, título) para practicar el flujo C.1, o por el canal habitual del equipo.
- Indicar: pasos para reproducir, endpoint/sección, resultado esperado vs obtenido, navegador (si es del tótem/panel).

---

## 8. Referencias

- Mapa de funcionalidades y endpoints: `docs/MAPA-FUNCIONAL.md`
- Guía de despliegue detallada: `docs/onboarding/guia-pruebas-despliegue.md`
- Checklist de evidencias SAT: `docs/operations/checklist-evidencias-sat.md`
- Índice general (dossier): `docs/DOSSIER.md`
