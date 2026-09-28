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
2. **Códigos de explotación** (`customerCode` / `siteCode`): son los campos
   «Cliente» y «Sede» del formulario de login. Para Níjar son `10201` y `103`.
   Con `-1` el backend usa los del usuario y los devuelve dentro del JWT.
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
SIGEUS_CUSTOMER_CODE=10201     # «Cliente» del formulario de login (Níjar); -1 = la del usuario
SIGEUS_SITE_CODE=103           # «Sede» del formulario de login (Níjar)
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

## 4. Endpoints de negocio (mapeados del código público del panel)

Los módulos del panel son *chunks* JS estáticos de `web.sigeus.net` que se
descargan sin sesión; de ellos se ha extraído el mapa método → URL (776
entradas, en el bundle de la versión 1.0.7). Todas son `GET` con la sesión
del apartado 3 y devuelven JSON. El resumen del panel («Resumen del estado del
servicio para el día») se construye con estas llamadas, todas con
`dateFrom`/`dateTo` en ISO 8601 (el panel envía el día completo en UTC):

| Bloque del resumen | Endpoint | Respuesta (campos que usa el panel) |
|---|---|---|
| Contenedores (activos/inactivos, con cierre, con volumétrico, por tipo y por fracción) | `api/Das/Summary/ContainersAsync?dateFrom=&dateTo=` | lista: `active`, `hasLock`, `hasVolumetric`, `containerType`, `garbage` |
| Puntos de recogida (activos, por tipo) | `api/Das/Summary/CollectionPointsAsync?dateFrom=&dateTo=` | lista: `active`, `hasLock`, `hasVolumetric`, tipo |
| Recogidas (recogidas, contenedores y puntos recogidos, kg, descargas, lavados, incidencias) | `api/Das/Summary/CollectionsAsync?dateFrom=&dateTo=` | objeto: `numCollections`, `numContainers`, `numColPoints`, `weight`, `numLandfillUnloads`, `kgLandfillUnloads`, `numWashes`, `numIncidents` |
| Recogidas y kg por fracción; lavados por fracción | `api/Das/Summary/EventsAsync?dateFrom=&dateTo=` | lista: `incidenceGroup` (pesaje = recogidas, lavacontenedores = lavados), `garbage`, `numEvents`, `weight` |
| Descargas en vertedero / planta | `api/Das/Summary/UnloadsAsync?dateFrom=&dateTo=` | `numLandfillUnloads`, `kgLandfillUnloads` |
| Papeleras (activas/inactivas, por tipo) | `api/Das/Summary/BinsAsync?dateTo=` | lista por papelera |
| Órdenes de trabajo RSU / limpieza viaria (por estado, avisos, maquinaria, personal, material) | `api/Das/Summary/RsuWorkOrdersAsync`, `api/Das/Summary/LvWorkOrdersAsync`, `api/Das/Summary/RsuFamilyResourcesByDatesAsync`, `api/Das/Summary/LvFamilyResourcesByDatesAsync` (`?dateFrom=&dateTo=`) | lista por OT: `state`, `family`… |
| Incidencias (por estado) | `api/Das/Summary/IncidencesAsync?dateFrom=&dateTo=` | lista: `state` |
| Recursos (maquinaria por estado) | `api/Das/Summary/ResourcesAsync?dateFrom=&dateTo=`, `api/Das/Summary/FamilyResourcesByModuleAsync?module=` | `numResources`, `family` |
| Flota (maquinaria, km, combustible, CO₂) | `api/Das/Summary/GpsAsync?dateFrom=&dateTo=` | `equipment`, `equipmentActive`, `totalKm`, `totalL`, `totalKgCo` |
| Alarmas | `api/Das/Summary/AlarmsAsync?dateFrom=&dateTo=` | lista |
| Series anuales de recogidas | `api/Das/Summary/CollectionsByYearAsync?year=&garbageId=&groupType=` | serie |

Inventarios y maestros (para el gemelo y el mapa):

| Entidad | Endpoint | Notas |
|---|---|---|
| Contenedores (inventario) | `api/cnt/containers/GetListFilteredAsync?containerTypeId=&garbageId=&active=&code=&tag=&containerData1Id=&containerData2Id=&containerData3Id=&areaId=&provinceId=&municipalityId=&addressId=&volumetricFilter=&startDate=&endDate=&isDoor2Door=&isVolumetric=&isLock=&containerProperty=&containerPropertyValue=` | columnas del panel: `code`, `tag`, `garbage`, `containerType`, `active`, `isContainerLock`, `isContainerVolumetric`, `area`, `municipality`, `address`, `latitude`, `longitude`, `capacity`, `lastCollectionDate`, `lastWashDate`, `volumetricDistancePercent`, `volumetricBatteryPercent`, `collectionPointId`, `routes`… (`active=true` y el resto vacío devuelve el parque activo) |
| Contenedor por id | `api/cnt/containers/GetAsync/{id}` | |
| Puntos de recogida | `api/cnt/colPoints/GetListFilteredAsync?code=&reference=&active=&areaId=&provinceId=&municipalityId=&addressId=&typeId=&startDate=&endDate=&isDoor2Door=&property=&propertyValue=` | columnas: `reference`, `containersNumber`, `collectionPointType`, `active`, `lastCollectionDate`, `lastWashDate`, `latitude`, `longitude`, `routes`… |
| Papeleras | `api/bns/bins/GetFilteredAsync?reference=&binTypeId=&tag=&active=&areaId=&provinceId=&municipalityId=&addressId=&fromDate=&toDate=&startDate=&endDate=&binProperty=&binPropertyValue=` | |
| Tipos de contenedor | `api/cnt/containers/types/getListAsync` | |
| Fracciones (garbages) | `Api/Cmn/Garbages/GetListAsync`, `GetListThinAsync`, `GetListByTypeAsync/{containerTypeId}` | |
| Áreas / zonas | `Api/Cmn/areas/GetListThinAsync`, `Api/Cmn/areas/GetListAsync` (con geometría), `Api/Cmn/Zones/…`, `Api/Cmn/ZoneAreas/GetListAsync/{zoneId}` | |
| Vertederos / plantas | `Api/Cmn/Landfills/GetListAsync`, `GetListThinAsync` | |
| Órdenes de trabajo RSU | `api/rsu/workOrders/today/GetListAsync`, `GetListByServiceIdAndDateAsync?serviceId=&dateFrom=&dateTo=`, `GetAsync/{id}`, `GetIndicatorsAsync/{id}`, `collections/getListByWorkOrderAsync/{id}` | |
| Eventos de sensor de llenado | `api/cnt/containers/SensorEvents/getSensorEventsByContainerAsync?containerId=&startDate=&endDate=`, `Api/Sat/fill/getContainerInfoAsync` | solo los 124 contenedores con volumétrico |

Los listados `GET …/GetListAsync` no llevan cuerpo. Los errores llegan como
`{"errors":[{"errorCode":…,"errorMessage":…}],"exceptionType":"ValidationError"}`
y el conector los traduce a `SigeusError`.

## 5. Siguiente fase: volcado a la vertical Residuos

1. Con el usuario técnico en el entorno, ejecutar el verificador y capturar
   una respuesta real (anonimizada) de cada endpoint de la tabla del resumen y
   del inventario de contenedores para fijar los tests de parseo.
2. Añadir en `connectors/sigeus.py` un método por endpoint y una función de
   parseo pura por entidad (mismo patrón que `thingsboard.py` / `bettair.py`).
3. Ampliar la vertical Residuos (`models/verticales.py`, migración `008`):
   `Contenedor` ya cubre el inventario (código, fracción, llenado, ruta,
   coordenadas); faltan puntos de recogida, recogidas/kg por fracción y día,
   descargas, lavados, papeleras, órdenes de trabajo y flota.
4. Sincronización periódica (worker) que vuelque el resumen diario y el
   inventario, y marque FD-116 como `operativa`.
