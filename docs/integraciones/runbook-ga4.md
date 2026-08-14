# Runbook · Activación de la analítica web real (Google Analytics 4)

| | |
|---|---|
| **Objeto** | Conectar la plataforma a la **propiedad GA4** del destino para datos reales |
| **Aplica a** | Google Analytics 4 de la web/app turística del Ayuntamiento de Níjar |
| **Expediente** | 18962/2025 · Hito 3 (integración de fuentes) · FD-102 |
| **Componentes** | `connectors/analytics/ga4.py`, `services/dashboards_service.py`, `services/informe_render.py` |

> **Idea clave:** GA4 **no se conecta con usuario/contraseña** ni con un token
> personal. Se usa una **cuenta de servicio de Google Cloud** (un fichero JSON de
> credenciales) a la que se da permiso de **Visualizador** sobre la propiedad GA4.
> El resto (conector, dashboard, informe mensual) ya está listo en la plataforma;
> si no hay credenciales, la analítica muestra datos sintéticos automáticamente.

---

## 0. Requisitos previos

- Que exista una **propiedad GA4** (no Universal Analytics, que está descontinuada)
  midiendo la web/app del destino.
- Acceso de **Administrador** a esa propiedad en Google Analytics.
- Un proyecto de **Google Cloud** (se puede crear uno gratuito) para alojar la
  cuenta de servicio y habilitar la API.

## 1. Valores a obtener (los 2 que faltan)

| Variable de entorno | Qué es |
|---|---|
| `GA4_PROPERTY_ID` | ID **numérico** de la propiedad GA4 (p. ej. `123456789`) |
| `GA4_SERVICE_ACCOUNT_JSON` | Ruta al fichero JSON de la cuenta de servicio (o el JSON inline) |

## 2. Procedimiento paso a paso

### 2.1 Crear la cuenta de servicio en Google Cloud
1. Entra en **console.cloud.google.com** y selecciona (o crea) un proyecto.
2. **APIs y servicios → Biblioteca** → busca y **habilita** la
   **Google Analytics Data API**.
3. **APIs y servicios → Credenciales → Crear credenciales → Cuenta de servicio**.
   Dale un nombre (p. ej. `dti-nijar-ga4-lector`). No hacen falta roles del proyecto.
4. Abre la cuenta creada → pestaña **Claves → Agregar clave → Crear clave nueva →
   JSON**. Se descarga el fichero `*.json` (esta es la credencial; guárdala segura).
5. Copia el **email** de la cuenta de servicio (algo como
   `dti-nijar-ga4-lector@<proyecto>.iam.gserviceaccount.com`).

### 2.2 Dar acceso a la propiedad en GA4
1. En **analytics.google.com** → **Administrar** (rueda dentada) → **Gestión del
   acceso a la propiedad**.
2. **+ → Agregar usuarios**, pega el **email de la cuenta de servicio** y asígnale
   el rol **Visualizador** (solo lectura). Guardar.

### 2.3 Obtener el Property ID
En **Administrar → Configuración de la propiedad**, copia el **ID de la propiedad**
(número, arriba a la derecha) → `GA4_PROPERTY_ID`.

## 3. Configurar la plataforma

Coloca el fichero JSON en el servidor (montado como *secret*, fuera del repo) y
edita el `.env` de producción (`infra/ovh/.env.production`):

```dotenv
GA4_PROPERTY_ID=123456789
# Ruta al fichero de credenciales (recomendado). También admite el JSON inline.
GA4_SERVICE_ACCOUNT_JSON=/run/secrets/ga4_service_account.json
```

> **Seguridad:** el JSON es una credencial sensible. **No se commitea** al repo ni
> se envía por email en texto plano; usar el canal seguro y montarlo como secreto.
> La cuenta de servicio es de **solo lectura** (Visualizador), lo mínimo necesario.

> **Dependencia:** la autenticación usa `google-auth` (ya incluida en
> `pyproject.toml`). Si se despliega una imagen antigua, reconstruir para que la
> instale.

## 4. Verificar ANTES de dar por integrado

Con el `.env` relleno y el JSON accesible, ejecuta el verificador (solo lee):

```bash
python -m scripts.verificar_ga4
# o
python scripts/verificar_ga4.py
```

Comprueba: presencia de la config, dependencia `google-auth`, carga del service
account, obtención del token OAuth2 y una consulta real `runReport` de los últimos
7 días. Informe `✔ / ▲ / ✘` y código de salida 0 (OK) / 1 (fallo). Si GA4 responde
**403**, casi siempre es que **falta dar acceso de Visualizador** a la cuenta de
servicio en la propiedad (paso 2.2).

## 5. Comprobar en la plataforma

No hay que reiniciar workers (GA4 se consulta bajo demanda). Verifica:

- **Dashboard →** sección **«Eficacia digital»** (sesiones, usuarios, canales).
- **Informe mensual** → apartado **«6. Eficacia digital (GA4)»**
  (`services/informe_render.py`).
- Si las credenciales fallan o faltan, la plataforma **cae a datos sintéticos** sin
  romper el informe (comportamiento seguro por diseño).

## 6. Rollback

Si algo falla, basta con **vaciar** `GA4_PROPERTY_ID` / `GA4_SERVICE_ACCOUNT_JSON`
(o dejar el JSON inaccesible): la analítica vuelve automáticamente a datos
sintéticos mientras se resuelve, sin errores en el dashboard ni en el informe.

---

## Notas

- **Sin renovación periódica:** a diferencia del token de Facebook, la clave de la
  cuenta de servicio **no caduca**. Buena práctica: rotarla ~cada 12 meses
  (crear clave nueva, actualizar el fichero, borrar la antigua).
- **Métricas que consume la plataforma:** `sessions`, `totalUsers`, `newUsers`,
  `screenPageViews`, `averageSessionDuration`, `bounceRate` y desglose por canal.
- **Property ID, no Measurement ID:** ojo, `GA4_PROPERTY_ID` es el número de la
  propiedad (Admin → Configuración), **no** el `G-XXXXXXX` del tag web.

## Checklist rápido

- [ ] Propiedad **GA4** activa (no Universal Analytics).
- [ ] **Google Analytics Data API** habilitada en el proyecto de Google Cloud.
- [ ] **Cuenta de servicio** creada y **clave JSON** descargada.
- [ ] Cuenta de servicio con rol **Visualizador** en la propiedad GA4.
- [ ] `GA4_PROPERTY_ID` (numérico) obtenido.
- [ ] JSON montado como secreto y `GA4_SERVICE_ACCOUNT_JSON` apuntando a él.
- [ ] `python -m scripts.verificar_ga4` pasa en verde.
- [ ] «Eficacia digital» con datos reales en dashboard e informe mensual.
