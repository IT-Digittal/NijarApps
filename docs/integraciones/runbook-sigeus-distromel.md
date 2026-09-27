# Runbook · siGEUS (Plataforma Distromel) — RSU y limpieza viaria

Integración de la plataforma de gestión de la contrata de residuos y limpieza
viaria del municipio con la vertical **Residuos** del DTI. Fuente **FD-116**
del catálogo (`GET /api/v1/integraciones/fuentes?categoria=residuos`).

| | |
|---|---|
| Panel del cliente | https://web.sigeus.net (Angular + DevExtreme) |
| Backend REST | https://api.sigeus.net/api/ (.NET; listados vía `.../GetListAsync`) |
| Conector | `src/nijar_dti/connectors/sigeus.py` (`ClienteSigeus`) |
| Servicio | `src/nijar_dti/services/sigeus_service.py` (`sigeus_configurado`, `comprobar_acceso`) |
| Estado en API | `GET /api/v1/gemelo/estado` → `sigeus_configurado` |
| Verificador | `python -m scripts.verificar_sigeus` |
| Tests | `tests/test_sigeus.py` (parseo puro, sin red) |

## 1. Qué necesitamos del cliente

1. **Usuario técnico de solo lectura, sin segundo factor (OTP).** El login con
   OTP (`api/session/loginOtp`) no es automatizable; si la cuenta facilitada
   pide código, el verificador lo indica y hay que pedir a Distromel un usuario
   de integración.
2. **Códigos de explotación** (`customerCode` / `siteCode`) solo si el usuario
   tiene acceso a varias explotaciones. Por defecto se envía `-1` (los del
   usuario) y el backend los devuelve dentro del JWT.
3. Confirmación del **alcance de datos** a integrar (ver §4).

Las credenciales viajan por el canal seguro acordado y se guardan únicamente en
el `.env` de producción (OVH). Nunca en el repositorio ni en tickets.

## 2. Activación

```bash
# infra/ovh/.env (producción) o .env (local)
SIGEUS_BASE_URL=https://api.sigeus.net
SIGEUS_USUARIO=<usuario técnico>
SIGEUS_PASSWORD=<contraseña>
SIGEUS_APPLICATION_CODE=0005   # el del panel web.sigeus.net; no cambiar salvo indicación
SIGEUS_CUSTOMER_CODE=-1        # -1 = explotación del usuario
SIGEUS_SITE_CODE=-1
SIGEUS_TIMEOUT_SECONDS=12
```

Reiniciar la API y verificar:

```bash
python -m scripts.verificar_sigeus
```

Salida esperada: configuración presente, login correcto con el nombre del
usuario, explotación asignada (`customerCode`/`siteCode` del token) y sesión
validada por `checkAuthAsync`. Si el catálogo de producción ya estaba sembrado,
`python -m nijar_dti.data.seed_loader` añade la fuente FD-116 sin tocar el
resto (el seed de fuentes es incremental por código).

Cuando la integración esté volcando datos reales, cambiar el estado de FD-116
a `operativa` en la tabla `fuentes_datos`.

## 3. Cómo funciona el conector

Reproduce el flujo del propio panel (obtenido de su configuración pública
`assets/config/environment.config.json` y de su bundle, sin credenciales):

| Paso | Llamada | Detalle |
|---|---|---|
| Login | `POST api/session/login` | `{username, password, applicationCode, customerCode, siteCode}` → `{token}` (JWT) |
| Cabeceras | todas las llamadas | `Authorization: Bearer <token>`, `customerCode`, `siteCode` (reclamaciones `customercode`/`sitecode` del JWT) |
| Renovación | `GET Api/Session/RenewToken` | `{isAuthenticated, token}`; se intenta antes de caducar (`exp` del JWT menos 60 s) y, si falla, se relogea |
| Comprobación | `GET Api/Session/checkAuthAsync` | usada por el verificador |
| Perfil | `GET api/session/user/current` | usada por el verificador |
| 401 | cualquiera | se descarta la sesión, se relogea y se reintenta una vez |

`ClienteSigeus.get(ruta)` y `.post(ruta, json_body)` permiten llamar a
cualquier endpoint relativo del backend con la sesión gestionada. Los errores se
elevan como `SigeusError` (o `SigeusRequiere2FAError`), nunca se inventan datos.

## 4. Siguiente fase (con acceso): endpoints de negocio

Los módulos del panel (R.S.U., Limpieza vial, Comunes, Genéricos) se cargan tras
el login, por lo que sus endpoints no se pueden mapear sin credenciales. Plan:

1. Entrar en el panel con el usuario técnico y capturar las llamadas de red de
   la pantalla «Resumen del estado del servicio» y de cada módulo (DevTools →
   Network, filtro `api.sigeus.net`). Anotar ruta, método, cuerpo y respuesta.
2. Añadir en `connectors/sigeus.py` un método por listado y una función de
   parseo pura por entidad, con tests a partir de respuestas reales
   anonimizadas (mismo patrón que `thingsboard.py` / `bettair.py`).
3. Ampliar la vertical Residuos (`models/verticales.py`, migración `008`) con
   lo que siGEUS aporta y hoy no existe: recogidas y kg por fracción, lavados,
   papeleras, órdenes de trabajo y flota. `Contenedor` ya cubre contenedores.
4. Sincronización periódica (worker o tarea programada) que vuelque los KPIs y
   marque FD-116 como `operativa`.

Datos visibles en el resumen del panel del cliente, a confirmar como alcance:
contenedores activos/inactivos por tipo y fracción, puntos de recogida,
recogidas (contenedores y puntos recogidos, kg, descargas en vertedero/planta),
lavados e incidencias, papeleras, órdenes de trabajo (con avisos, maquinaria,
personal, material) y flota (maquinaria, km, combustible, kg CO₂).
