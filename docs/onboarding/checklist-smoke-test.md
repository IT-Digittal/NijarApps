# Checklist de smoke test — DTI Níjar (1 página)

**Tester:** ____________________  **Fecha:** __________  **Navegador:** ____________  **Commit/rama:** ____________

> Marca ✓ / ✗. Datos demo cargados en el primer arranque. Para la voz del tótem usa **Chrome/Edge**.

## Arranque
- [ ] `pytest tests/ -m "not integration"` → **264 passed**
- [ ] `GET /api/v1/health` → `ok`
- [ ] Swagger abre (`/docs`) · Panel abre (`/dashboard`) · Tótem abre (`/totem`)
- [ ] Login panel: `admin@nijar.es` / `CambiarEnPrimerArranque#2026`

## Backend (Swagger o curl)
- [ ] `GET /tourism/resources?publicado=true` → ≥14 recursos
- [ ] `GET /tourism/events` → eventos demo
- [ ] `GET /data/iot/sensors` → 9 sensores
- [ ] `GET /data/social/kpis/sentiment` · `/share-of-voice` · `/topics` → datos
- [ ] `GET /data/social/kpis/nps` → NPS con componentes
- [ ] `GET /data/social/kpis/composicion-linguistica` → % por idioma
- [ ] `GET /prediccion/afluencia?metrica=totem` → 14 puntos + banda
- [ ] `GET /prediccion/validacion?metrica=chatbot` → MAPE
- [ ] `GET /data/contexto/factor-expansion` → factor (≈6.7 o calibrado)
- [ ] `POST /rutas/planificar` (lat 36.847, lon -2.041) → itinerario
- [ ] `GET /rutas/recomendaciones?idioma=en` → eventos + recursos (EN)
- [ ] `POST /chatbot/query` ES → respuesta con fuente / confianza
- [ ] `POST /chatbot/query` fuera de dominio → **fallback** (no inventa)
- [ ] `GET /incidencias?desde=2026-05-01T00:00:00Z&hasta=2026-06-01T00:00:00Z` → 8 incidencias
- [ ] `GET /incidencias/ans?desde=...&hasta=...` → cumplimiento por severidad
- [ ] `GET /dashboards/monthly-report?year=2026&month=5` → disponibilidad real

## Panel (secciones)
- [ ] Dashboard (resumen) carga con KPIs
- [ ] Recursos: tabla + alta/edición (CRUD)
- [ ] Eventos: listado/alta
- [ ] Smart Office: sensores y serie ambiental
- [ ] Social Listening: sentimiento, SoV, temas, **NPS**, **composición lingüística**
- [ ] Chatbot: telemetría
- [ ] Mapa: POIs en Leaflet
- [ ] Tótems: uso
- [ ] **Mantenimiento · ANS**: disponibilidad, ANS, incidencias, **descargar informe .md**
- [ ] **Predicción y contexto**: curva + bandas, MAPE/anomalías/factor, cambiar métrica

## Tótem (Chrome/Edge)
- [ ] Idiomas ES/EN/DE/FR cambian toda la UI
- [ ] Accesibilidad: A+ (texto grande) y ◐ (alto contraste)
- [ ] Categorías incl. **Eventos**; detalle de POI (modal)
- [ ] Chatbot (texto) responde en el idioma activo
- [ ] Voz: 🎤 dicta la pregunta · 🔊 lee la respuesta
- [ ] Planificador "Sugerir ruta cercana" → paradas + distancia
- [ ] "¿Qué visitar hoy?" → eventos + lugares
- [ ] Inactividad 60 s → vuelve al inicio

## Valores de referencia (demo)
- [ ] Disponibilidad media ≈ **99,3 %** · ANS "alta" ≈ **66,7 %** · **8** incidencias · **105** FAQs

## Notas / incidencias detectadas
________________________________________________________________________________
________________________________________________________________________________

> Reportar en `POST /api/v1/incidencias` o por el canal del equipo (pasos, sección/endpoint, esperado vs obtenido, navegador).
