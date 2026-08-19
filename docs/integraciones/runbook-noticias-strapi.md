# Runbook · Integración de noticias del Ayuntamiento (Strapi)

| | |
|---|---|
| **Objeto** | Consumir las **noticias municipales** publicadas en Strapi (JSON público) |
| **Aplica a** | Web del Ayuntamiento de Níjar (migrada de WordPress a Strapi) |
| **Expediente** | 18962/2025 · Hito 3 (integración de fuentes) · FD-101/FD-110 |
| **Componentes** | `connectors/noticias.py`, `services/noticias_service.py`, `api/v1/noticias.py` |

> **Estado:** integración **implementada y verificada en producción del origen**.
> El API de noticias es **público y sin autenticación**, por lo que funciona con
> la configuración por defecto (no requiere credenciales del Ayuntamiento). Este
> runbook documenta el acceso, los endpoints propios y cómo verificarlo.

---

## 1. Origen de datos (facilitado por el Ayuntamiento)

- **Base URL:** `https://api.nijaraldia.es`
- **Endpoint:** `/api/articles` (Strapi 5)
- **Project Document ID:** `bs261ckcuumnj68xcjncw7rf`
- **Categoría «Turismo»:** documentId `lj6bv606bqnpvf1u1bovf2m8`
  (las noticias de la app de Turismo son las de esta categoría).

Notas de la API (ya contempladas en el conector):
- El filtro por proyecto es obligatorio:
  `filters[projects][documentId][$eq]=<PROJECT_ID>`.
- `populate` debe indicarse con índices (`populate[0]=cover&populate[1]=categories`);
  Strapi 5 rechaza `populate=cover,categories`.
- Las URLs de imagen (`cover.url`) son **relativas**; el conector las convierte a
  absolutas con la base del API.

## 2. Configuración (por defecto ya operativa)

En el `.env` (valores por defecto = los facilitados por el Ayuntamiento):

```dotenv
NOTICIAS_STRAPI_BASE_URL=https://api.nijaraldia.es
NOTICIAS_STRAPI_PROJECT_ID=bs261ckcuumnj68xcjncw7rf
NOTICIAS_CATEGORIA_TURISMO_ID=lj6bv606bqnpvf1u1bovf2m8
NOTICIAS_TIMEOUT_SECONDS=12
```

No hay tokens ni secretos que gestionar.

## 3. Endpoints que expone la plataforma

Bajo `/api/v1/noticias` (información pública, sin autenticación; si la fuente no
está configurada responden 503):

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/noticias/estado` | Estado de configuración de la fuente |
| GET | `/noticias` | Listado paginado (`page`, `page_size`, `categoria`, `buscar`) |
| GET | `/noticias/turismo` | Atajo: noticias de la categoría Turismo |
| GET | `/noticias/categorias` | Listado de categorías (documentId, nombre, slug) |
| GET | `/noticias/{slug}` | Detalle de una noticia (con el contenido completo) |

Cada noticia se normaliza a: `id`, `document_id`, `titulo`, `descripcion`,
`slug`, `contenido` (solo en el detalle), `fecha`, `publicado_en`, `imagen_url`
(absoluta) y `categorias`.

## 4. Verificación

```bash
python -m scripts.verificar_noticias_strapi
# o
python scripts/verificar_noticias_strapi.py
```

Comprueba el listado general, el filtro por Turismo y el detalle por slug contra
el API real. Salida `✔ / ▲ / ✘` y código 0/1.

## 5. Consumidores en la plataforma

- **Tótem** y **panel**: sección de noticias del destino / municipales.
- **Chatbot**: puede fundamentar respuestas sobre actualidad municipal.

## 6. Webhooks (opcional, a futuro)

El Ayuntamiento ofrece crear un **webhook** de notificación ante nuevas noticias.
Hoy la plataforma consulta bajo demanda (pull), que es suficiente. Si en el
futuro se quiere refresco inmediato (push), se puede añadir un endpoint receptor
`POST /noticias/webhook` que invalide una caché; **no es necesario para la
integración actual**.

---

## Notas

- **Noticias de Turismo:** proceden del mismo Strapi filtrando por la categoría
  Turismo (endpoint `/noticias/turismo`), tal como recomienda el Ayuntamiento
  (mejor consumir Strapi directamente que la app de Turismo).
- **Sin credenciales:** al ser un origen público, no aplica rotación de tokens ni
  cuentas de servicio.
- **Robustez:** ante un fallo del origen, los endpoints devuelven 502 y la
  plataforma no cachea datos ficticios.

## Checklist rápido

- [x] Conector, servicio y router implementados y con tests.
- [x] `python -m scripts.verificar_noticias_strapi` pasa en verde.
- [ ] Noticias visibles en el tótem/panel (integración de front-end).
- [ ] (Opcional) Webhook de nuevas noticias, si se desea refresco inmediato.
