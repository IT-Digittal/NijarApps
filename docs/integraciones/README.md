# Integraciones de datos externos · Plataforma DTI Níjar

Índice del estado de cada integración con fuentes externas, cómo **activarla** y
cómo **verificarla**. El catálogo completo de fuentes está en
[`fuentes-de-datos.md`](fuentes-de-datos.md).

**Leyenda de estado**
- ✅ **Operativo** — integrado y funcionando con datos reales.
- 🟢 **Listo (sin credenciales)** — fuente pública; funciona por defecto.
- 🟡 **Listo, pendiente de credenciales** — conector hecho; falta que el
  Ayuntamiento/tercero facilite tokens o accesos.
- ⏳ **Pendiente de terceros** — depende de un sistema aún no disponible.

---

## Resumen

| Integración | Estado | Endpoint(s) de la plataforma | Runbook | Verificación |
|---|---|---|---|---|
| **Noticias del Ayuntamiento** (Strapi) | 🟢 | `/api/v1/noticias`, `/noticias/turismo`, `/noticias/{slug}` | [runbook](runbook-noticias-strapi.md) | `python -m scripts.verificar_noticias_strapi` |
| **Meteorología pública** (Open-Meteo) | 🟢 | `/api/v1/gemelo/meteo` | — (sin configuración) | `python -m scripts.verificar_openmeteo` |
| **Banderas de playa / aforo** (ThingsBoard IoT municipal) | ✅ | `/api/v1/gemelo/playas/banderas`, `/gemelo/parque/aforo` | — | Requiere `THINGSBOARD_*` (configurado en producción) |
| **Social Listening** (Facebook + Instagram) | 🟡 | `/api/v1/data/social` (worker) | [runbook](runbook-social-listening-meta.md) | `python -m scripts.verificar_social_meta` |
| **Social Listening** (X / Twitter) | 🟡 | `/api/v1/data/social` (worker) | [runbook](runbook-social-listening-meta.md) | (parte de social) |
| **Analítica web** (Google Analytics 4) | 🟡 | Dashboard «Eficacia digital»; informe mensual | [runbook](runbook-ga4.md) | `python -m scripts.verificar_ga4` |
| **Calidad del aire y meteo** (Bettair) | 🟡 | `/api/v1/gemelo/aire/resumen`, `/gemelo/aire/estaciones` | — | Requiere `BETTAIR_CLIENT_ID/SECRET` (los gestiona Bettair) |

---

## Detalle por integración

### Noticias del Ayuntamiento (Strapi) · 🟢
La web municipal publica sus noticias en Strapi (JSON público, sin auth). La
plataforma las reexpone normalizadas (listado, filtro por categoría, Turismo,
detalle por slug) para tótem, panel y chatbot. Operativa por defecto.
→ [runbook-noticias-strapi.md](runbook-noticias-strapi.md)

### Meteorología pública (Open-Meteo) · 🟢
Condiciones actuales y previsión a 3 días, sin clave. `/gemelo/meteo` admite
`lat`/`lon` (cada tótem muestra el tiempo de su ubicación). Códigos WMO
traducidos (es/en/de/fr). La consume el pill del tótem y una tarjeta del panel.

### Banderas de playa y aforo del parque (ThingsBoard) · ✅
Lectura en tiempo real de la plataforma IoT municipal (34 banderas + aforo del
P.N. Cabo de Gata). Operativo en producción; el mapa del «Gemelo vivo» y el
tótem muestran el estado. Cuando el Ayuntamiento reestructure el sistema de
banderas (próxima temporada, con histórico), se repunta el conector a la nueva
fuente.

### Social Listening — Facebook + Instagram · 🟡
Conectores hechos y verificables. Falta el **token de la app de Meta** y los IDs.
El acceso a Facebook/Instagram ya está facilitado por el Ayuntamiento.
→ [runbook-social-listening-meta.md](runbook-social-listening-meta.md)
Renovación del token de 60 días: `scripts/renovar_token_facebook.py`.

### Google Analytics 4 · 🟡
Conector hecho. Falta la **cuenta de servicio** (JSON) con rol Visualizador en la
propiedad GA4 y el **Property ID**.
→ [runbook-ga4.md](runbook-ga4.md)

### Bettair (calidad del aire) · 🟡
Conector OAuth2 hecho. Requiere `BETTAIR_CLIENT_ID/SECRET`, que gestiona Bettair
(hay que coordinarlo con ellos). Sin credenciales, los endpoints `/gemelo/aire/*`
responden 503 y la meteo pública la cubre Open-Meteo.

---

## Comportamiento ante fuentes no configuradas

Todas las integraciones **degradan con seguridad**: si falta una credencial o la
fuente cae, el endpoint responde 503/502 y la plataforma **no inventa datos**
(salvo el Social Listening, que puede operar en `SOCIAL_DRY_RUN=true` con datos
sintéticos para desarrollo). Los verificadores (`scripts/verificar_*.py`) permiten
comprobar cada fuente antes de darla por activa.
