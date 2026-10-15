# Integraciones de datos externos · Plataforma DTI Níjar

Índice del estado de cada integración con fuentes externas, cómo **activarla** y
cómo **verificarla**. El catálogo completo de fuentes está en
[`fuentes-de-datos.md`](fuentes-de-datos.md).

> **Comprobación global:** `python -m scripts.verificar_integraciones` ejecuta
> todos los verificadores de una vez y muestra un resumen OK/FALLA por
> integración (añade `--detalle` para el informe completo de cada uno).

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
| **Banderas de playa / aforo** (ThingsBoard IoT municipal) | ✅ | `/api/v1/gemelo/playas/banderas`, `/gemelo/parque/aforo` | — | `python -m scripts.verificar_thingsboard` (requiere `THINGSBOARD_*`, configurado en producción) |
| **Social Listening** (Facebook + Instagram) | 🟡 | `/api/v1/data/social` (worker) | [runbook](runbook-social-listening-meta.md) | `python -m scripts.verificar_social_meta` |
| **Social Listening** (X / Twitter) | 🟡 | `/api/v1/data/social` (worker) | [runbook](runbook-social-listening-meta.md) | (parte de social) |
| **Analítica web** (Google Analytics 4) | 🟡 | Dashboard «Eficacia digital»; informe mensual | [runbook](runbook-ga4.md) | `python -m scripts.verificar_ga4` |
| **Calidad del aire y meteo** (Bettair) | 🟡 | `/api/v1/gemelo/aire/resumen`, `/gemelo/aire/estaciones` | — | Requiere `BETTAIR_CLIENT_ID/SECRET` (los gestiona Bettair) |
| **RSU y limpieza viaria** (siGEUS · Distromel) | 🟡 | `/api/v1/gemelo/estado` (`sigeus_configurado`); KPIs en `/verticales/residuos/*` al conectar | [runbook](runbook-sigeus-distromel.md) | `python -m scripts.verificar_sigeus` (requiere `SIGEUS_USUARIO/PASSWORD`) |
| **Consumo eléctrico** (Datadis) | 🟡 público · ⏳ privado | `/api/v1/verticales/energia/municipio`, `/energia/suministros/{cups}/curva`, `/energia/datadis/estado` | [runbook](runbook-datadis.md) | `python -m scripts.verificar_datadis` (datos públicos sin usuario; privada con `DATADIS_USUARIO/PASSWORD`) |
| **Contenidos abiertos del tótem** (OpenStreetMap + Wikipedia/Commons) | 🟢 | `/api/v1/tourism/services` (gastronomía), `/tourism/resources` (artesanía, fotos) | ver detalle abajo | `python -m nijar_dti.workers.contenidos_abiertos --dry-run` |

---

## Detalle por integración

### Contenidos abiertos del tótem (OpenStreetMap + Wikipedia/Commons) · 🟢
Worker `workers/contenidos_abiertos.py` (conector `connectors/contenidos_abiertos.py`),
sin claves. Se lanza a mano en producción y es idempotente:

```bash
docker exec nijar-dti-api python -m nijar_dti.workers.contenidos_abiertos --dry-run  # solo consulta
docker exec nijar-dti-api python -m nijar_dti.workers.contenidos_abiertos            # guarda
```

- **OpenStreetMap** (Overpass, `OVERPASS_URL`): restaurantes, bares y cafeterías
  del término municipal → servicios publicados (sección Gastronomía); alfarerías
  y talleres/tiendas de jarapas → recursos con etiquetas `ceramica`/`jarapas`.
  URN `…:osm-<tipo>-<id>`. Al repetirlo refresca los datos de OSM, respeta
  `publicado` e imágenes del CMS y despublica lo que ya no está en OSM.
  Licencia ODbL (© colaboradores de OpenStreetMap).
- **Imágenes**: a cada recurso publicado sin foto le asigna la del artículo de
  Wikipedia del lugar o la foto de Wikimedia Commons más cercana (≥ 800 px), y
  guarda el crédito (autor · licencia) en `enlaces_externos.imagen_credito`; el
  tótem lo muestra sobre la foto. No pisa imágenes puestas desde el CMS. Si una
  foto no convence, basta con sustituirla en el CMS.
- **Límites de las APIs**: Wikimedia exige un User-Agent con contacto
  (`CONTENIDOS_CONTACTO`) y limita con 429; el worker reintenta respetando
  `Retry-After` y espera 1,5 s entre recursos. Overpass se reintenta y, si sigue
  caído, se usa un espejo. Se descartan fotos que no son del lugar (fotos desde
  el espacio, mapas, escudos, PNG…); `--solo imagenes --rehacer` vuelve a buscar
  todas las fotos automáticas.

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

### siGEUS · Distromel (RSU y limpieza viaria) · 🟡
Plataforma de gestión de la contrata de residuos (contenedores, puntos de
recogida, recogidas por fracción, lavados, papeleras, órdenes de trabajo y
flota). Conector hecho: login contra `api.sigeus.net`, sesión con renovación
y llamadas genéricas, siguiendo exactamente el flujo del panel. Falta el
**usuario técnico de solo lectura (sin 2FA)** que nos facilita el cliente. Con
él se capturan los endpoints de negocio y se vuelcan a la vertical Residuos.
→ [runbook-sigeus-distromel.md](runbook-sigeus-distromel.md)

---

## Comportamiento ante fuentes no configuradas

Todas las integraciones **degradan con seguridad**: si falta una credencial o la
fuente cae, el endpoint responde 503/502 y la plataforma **no inventa datos**
(salvo el Social Listening, que puede operar en `SOCIAL_DRY_RUN=true` con datos
sintéticos para desarrollo). Los verificadores (`scripts/verificar_*.py`) permiten
comprobar cada fuente antes de darla por activa.
