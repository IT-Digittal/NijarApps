# Runbook · Activación del Social Listening real (Facebook + Instagram)

| | |
|---|---|
| **Objeto** | Pasar el Social Listening de `dry-run` (datos sintéticos) a **datos reales** de Meta |
| **Aplica a** | Perfiles oficiales de **Facebook** e **Instagram** del Ayuntamiento de Níjar |
| **Expediente** | 18962/2025 · Hito 3 (integración de fuentes) |
| **Componentes** | `connectors/social/facebook.py`, `connectors/social/instagram.py`, `workers/social_worker.py` |

> **Idea clave:** tener acceso a las cuentas (usuario/contraseña) **no basta**. La
> plataforma lee las redes por la **Graph API de Meta**, así que hay que convertir
> ese acceso en **credenciales de API**: una app de Meta, un **token** y dos **IDs**.
> Este runbook cubre solo lo que se hace *desde el lado de Meta*; el resto (código,
> worker, dashboards) ya está listo en la plataforma.

---

## 0. Requisitos previos

- La cuenta de **Instagram** debe ser **Business** (o Creator) — no personal — y
  estar **vinculada a la página de Facebook** del Ayuntamiento. Se comprueba/ajusta
  desde la app de Instagram: *Configuración → Cuenta → Cambiar a cuenta profesional*
  y luego vincular la página en *Meta Business Suite*.
- Tener rol de **administrador** de la página en **Meta Business Suite**
  (business.facebook.com).

## 1. Valores a obtener (los 3 que faltan)

| Variable de entorno | Qué es |
|---|---|
| `FACEBOOK_ACCESS_TOKEN` | Page Access Token de larga duración (idealmente de *System User*, que **no caduca**) |
| `FACEBOOK_PAGE_ID` | ID numérico de la página oficial |
| `INSTAGRAM_BUSINESS_ACCOUNT_ID` | ID de la cuenta de Instagram Business |

`INSTAGRAM_HASHTAGS`, `FACEBOOK_PAGE_HANDLE` e `INSTAGRAM_HANDLE` ya vienen con
valores por defecto razonables y son opcionales.

## 2. Permisos (scopes) que necesita la app de Meta

| Scope | Para qué |
|---|---|
| `pages_read_engagement` | Leer el feed/publicaciones de la página de Facebook |
| `pages_read_user_content` | Leer contenido y comentarios de la página |
| `instagram_basic` | Acceso básico a la cuenta de Instagram Business |
| `instagram_manage_insights` | Búsqueda de menciones por **hashtag** en Instagram |

## 3. Procedimiento paso a paso

### 3.1 Crear/usar una app de Meta
1. Entra en **developers.facebook.com → Mis apps**.
2. Crea una app de tipo **Business** (o usa una existente del Ayuntamiento).
3. Añade los productos **Facebook Login** y **Instagram Graph API**.
4. En *App Review → Permissions and Features*, solicita/activa los 4 scopes de la §2.

### 3.2 Obtener un token y los IDs (con el Graph API Explorer)
1. Abre **developers.facebook.com/tools/explorer**.
2. Selecciona tu app y pulsa **Generate Access Token**; acepta los permisos de la §2
   para la página del Ayuntamiento.
3. **Page ID + Page Token** → ejecuta:
   ```
   GET /me/accounts
   ```
   Localiza la página del Ayuntamiento: `id` → `FACEBOOK_PAGE_ID`; `access_token` de
   esa página → base para `FACEBOOK_ACCESS_TOKEN`.
4. **Instagram Business Account ID** → ejecuta (con el PAGE_ID del paso anterior):
   ```
   GET /{FACEBOOK_PAGE_ID}?fields=instagram_business_account
   ```
   El `id` devuelto → `INSTAGRAM_BUSINESS_ACCOUNT_ID`.

### 3.3 Convertir el token en uno de larga duración (recomendado)
El token del Explorer caduca en ~1 h. Para producción:
- **Opción A (sencilla, ~60 días):** intercambiar por uno de larga duración:
  ```
  GET /oauth/access_token?grant_type=fb_exchange_token
      &client_id={APP_ID}&client_secret={APP_SECRET}&fb_exchange_token={TOKEN_CORTO}
  ```
- **Opción B (recomendada, no caduca):** crear un **System User** en *Business
  Settings → Users → System Users*, asignarle la página con permiso de lectura y
  **generar un token** con los scopes de la §2. Este token **no expira** y es el
  ideal para un servicio desatendido.

> El verificador (§5) avisa de la caducidad del token y, si detecta `expires_at=0`,
> confirma que **no caduca**.

## 4. Configurar la plataforma

Edita el `.env` de producción (`infra/ovh/.env.production`) y rellena:

```dotenv
FACEBOOK_ACCESS_TOKEN=EAAG...        # token de larga duración / System User
FACEBOOK_PAGE_ID=1234567890
INSTAGRAM_BUSINESS_ACCOUNT_ID=1784xxxxxxxxxxx
# INSTAGRAM_HANDLE y FACEBOOK_PAGE_HANDLE son informativos/opcionales
SOCIAL_LISTENING_ENABLED=true
SOCIAL_DRY_RUN=true                  # se deja en true hasta verificar (paso 5)
```

> **Seguridad:** el token es una credencial sensible. **No se envía por email en
> texto plano** (usar el canal seguro acordado). No se commitea el `.env` real —
> solo el `.env.production.example`.

## 5. Verificar ANTES de activar

Con el `.env` relleno, ejecuta el verificador (no modifica nada, solo lee):

```bash
# en el servidor / dentro del contenedor de la API
python -m scripts.verificar_social_meta
# o
python scripts/verificar_social_meta.py
```

Comprueba: validez y caducidad del token, permisos, lectura del feed de Facebook,
acceso a la cuenta de Instagram y búsqueda de hashtags. Muestra un informe con
`✔ / ▲ / ✘` y devuelve código de salida 0 (OK) o 1 (fallo).

## 6. Activar el modo real

Cuando la verificación pase en verde:

1. Poner en el `.env`:
   ```dotenv
   SOCIAL_DRY_RUN=false
   ```
2. Reiniciar el worker de Social Listening:
   ```bash
   docker compose --profile workers up -d --force-recreate social-worker
   ```
   (hace polling cada `SOCIAL_POLLING_INTERVAL_MINUTES`, 15 min por defecto).
3. **Comprobar que entran datos reales:**
   - `GET /api/v1/data/social` (menciones recientes).
   - Panel de **Social Listening** en el dashboard (sentimiento, idiomas, temas).
   - Logs del worker: `docker compose logs -f social-worker`.

## 7. Rollback

Si algo falla, volver a `SOCIAL_DRY_RUN=true` y reiniciar el worker: la plataforma
sigue operando con datos sintéticos sin errores mientras se resuelve.

---

## Notas y límites de la API (importante)

- **Instagram · hashtags:** la Graph API permite un máximo de **30 hashtags únicos
  por cuenta cada 7 días** y **no devuelve el autor** de los posts (limitación de
  Meta, ya contemplada en el conector). Ajustar `INSTAGRAM_HASHTAGS` con criterio.
- **Facebook:** el conector lee el **feed de la página oficial** (publicaciones y
  métricas de interacción), no menciones de terceros por palabra clave (eso es X).
- **Caducidad:** si se usa un token de ~60 días (Opción A), programar su renovación
  antes de que expire; con System User (Opción B) no aplica.
- **X / Twitter:** es independiente (`TWITTER_BEARER_TOKEN`); este runbook cubre
  solo Meta (Facebook + Instagram).

## Checklist rápido

- [ ] Instagram es cuenta **Business** y está vinculada a la página de Facebook.
- [ ] App de Meta con los 4 scopes de la §2.
- [ ] `FACEBOOK_ACCESS_TOKEN` (de larga duración / System User) obtenido.
- [ ] `FACEBOOK_PAGE_ID` e `INSTAGRAM_BUSINESS_ACCOUNT_ID` obtenidos.
- [ ] Valores puestos en `infra/ovh/.env.production`.
- [ ] `python -m scripts.verificar_social_meta` pasa en verde.
- [ ] `SOCIAL_DRY_RUN=false` y worker reiniciado.
- [ ] Datos reales visibles en `/api/v1/data/social` y en el dashboard.
