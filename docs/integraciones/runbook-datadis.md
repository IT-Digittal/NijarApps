# Runbook · Integración Datadis (consumo eléctrico)

| | |
|---|---|
| **Objeto** | Consumo eléctrico del municipio y de los suministros municipales |
| **Fuente** | [Datadis](https://datadis.es), plataforma oficial de las distribuidoras eléctricas |
| **Componentes** | `connectors/datadis.py`, `services/datadis_service.py`, `workers/datadis_carga.py`, migración `016_energia_datadis` |
| **Consumidores** | Vertical **Energía** del panel (sección «Consumo del municipio» y edificios/CUPS) |

## 1. Qué se integra

| Parte | Endpoint Datadis | Credenciales | Dónde se guarda |
|---|---|---|---|
| **Datos públicos agregados** (lo de datadis.es → Datos públicos → Consultas) | `GET /api-public/api-search` | Se intentan **sin usuario**; si Datadis lo exige, se usa el de abajo | `energia_municipio_diario` (día · sector · tensión · contratos · kWh) |
| **Suministros municipales** | `GET /api-private/api/get-supplies-v2` | Usuario de Datadis | `energia_suministros` (`metadatos.fuente = "datadis"`) |
| **Potencia contratada** | `GET /api-private/api/get-contract-detail-v2` | Usuario de Datadis | `energia_suministros.potencia_contratada_kw` |
| **Curva horaria** | `GET /api-private/api/get-consumption-data-v2` | Usuario de Datadis | `energia_consumos_horarios` (inicio de hora en UTC) |

Login: `POST /nikola-auth/tokens/login` (formulario `username`, `password`) → token
JWT en texto (≈24 h). Datadis **rechaza repetir la misma consulta privada en 24 h**,
por eso la carga es diaria y no se lanza al arrancar la API.

Cuando hay suministros reales de Datadis, la vertical de Energía **deja de mostrar
los suministros de demostración**.

## 2. Configuración (`.env`)

```dotenv
DATADIS_USUARIO=            # NIF/CIF del usuario de datadis.es (API privada)
DATADIS_PASSWORD=
DATADIS_NIF_AUTORIZADO=     # CIF del Ayuntamiento si el usuario es un tercero autorizado
DATADIS_PUBLICO_ACTIVO=true
DATADIS_COMUNIDAD=01        # Andalucía
DATADIS_MUNICIPIO_CODIGO=04066   # INE provincia+municipio (Níjar); el verificador confirma el formato
DATADIS_MUNICIPIO_NOMBRE=Níjar   # las filas se validan además por nombre
DATADIS_HORA_CARGA=7        # carga diaria, hora de Madrid (-1 = desactivada)
```

### Qué pedir al Ayuntamiento (API privada)
1. Alta del Ayuntamiento en datadis.es con su CIF (o confirmación de que ya existe).
2. Preferible: que el Ayuntamiento **autorice** en Datadis a un usuario técnico
   (p. ej. de IT Digittal) a consultar sus suministros. Ese usuario va en
   `DATADIS_USUARIO/PASSWORD` y el CIF del Ayuntamiento en `DATADIS_NIF_AUTORIZADO`.
3. Confirmar si hay suministros municipales a nombre de otros titulares
   (concesionarias de agua, alumbrado…).

> **Importante:** deja estas variables **vacías** hasta tener el usuario real. Los
> valores de plantilla tipo `<NIF/CIF del usuario>` se ignoran, pero no los dejes.

### Resultado en producción (15/10/2026)
El verificador confirmó que **Datadis exige usuario también para la API pública**
(401 en `/api-public/api-search`). Hasta tenerlo, los datos públicos se cargan
importando el fichero de la web (apartado 4 bis).

## 3. Verificación

```bash
docker exec -i nijar-dti-api python - < scripts/verificar_datadis.py
```

- Prueba la consulta pública de una semana reciente con varios formatos del
  código de municipio y dice cuál devuelve **solo filas de Níjar** (si no es el
  configurado, cambia `DATADIS_MUNICIPIO_CODIGO`). Muestra una fila de ejemplo tal
  como la envía Datadis: si el conector no la reconoce, lo indica.
- Si hay credenciales: login y listado de suministros (CUPS) accesibles.

## 4. Cargas

```bash
# Histórico de datos públicos (por meses; idempotente)
docker exec nijar-dti-api python -m nijar_dti.workers.datadis_carga --solo publico --desde 2025-01-01
# Curva privada desde un mes (cuidado con el límite de 24 h por consulta)
docker exec nijar-dti-api python -m nijar_dti.workers.datadis_carga --solo privado --mes-desde 2026/01
# Consultar sin guardar
docker exec nijar-dti-api python -m nijar_dti.workers.datadis_carga --dry-run
```

## 4 bis. Importar el fichero de la web (sin usuario de Datadis)

1. En <https://datadis.es/queries> → **Consumos y contratos**: rango de fechas dentro
   de un mes, Localización = Níjar, todos los sectores y tensiones → **Consultar** →
   **Descargar** (CSV o Excel).
2. Panel → Energía municipal → **Consumo del municipio** → «Importar fichero de
   Datadis» (roles `administrador_tic` y `analista_datos`). Admite varios ficheros
   a la vez; volver a subir un mes lo actualiza.

Por consola:
```bash
docker exec -i nijar-dti-api python -m nijar_dti.workers.datadis_importar - < julio.csv
```
Endpoint: `POST /api/v1/verticales/energia/datadis/importar` (multipart `archivo`).
El lector acepta CSV («;», «,», tabulador; UTF-8/Latin-1) y Excel, con líneas de
texto antes de la cabecera y números con formato español.

La carga automática corre cada día a las `DATADIS_HORA_CARGA` (un solo worker,
con cerrojo de PostgreSQL) y deja en los logs `Carga diaria de Datadis`.

## 5. Endpoints de la plataforma (permiso `ver_energia`)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/v1/verticales/energia/municipio?dias=90` | Serie diaria del municipio (total y por sector) |
| GET | `/api/v1/verticales/energia/suministros/{cups}/curva?dias=7` | Curva horaria de un suministro |
| GET | `/api/v1/verticales/energia/datadis/estado` | Estado de la integración |
| POST | `/api/v1/verticales/energia/datadis/importar` | Importar el fichero descargado de datadis.es |

## Notas
- Datadis **oculta los registros con pocos contratos** por protección de datos:
  el total municipal puede ser algo inferior al real.
- Las horas de la curva vienen como 1..24 (hora de fin); se guardan como inicio de
  hora en UTC.

## Histórico mensual de la Vista de Gobierno

Con la curva horaria privada cargada, la API guarda cada día (a las
`CAPTURA_METRICAS_HORA`:30, hora de Madrid) el último mes **cerrado y completo**
en `metricas_historicas`, sustituyendo el dato de ejemplo de la instalación:

- `energia.consumo_kwh` (CUPS municipales salvo alumbrado) y `energia.coste_eur`
  (consumo × €/kWh medio de los suministros, marcado como estimado).
- `alumbrado.consumo_kwh` (CUPS con tipo `alumbrado`).

Tras la primera carga privada, rellenar hacia atrás y comprobar:

```bash
docker exec nijar-dti-api python -m nijar_dti.workers.captura_metricas --desde 2025-01
docker exec nijar-dti-api python -m nijar_dti.workers.captura_metricas --estado
```

Hasta tener 15 meses reales seguidos, el panel no muestra previsión para esas
series (no mezcla dato real con histórico de ejemplo).

## Descarga en el formato de los pliegos (Anexos I y II)

Petición del Servicio de Gestión de Infraestructuras: descargar los suministros
y consumos estructurados como los anexos de los pliegos de suministro eléctrico.

- **Dónde**: Verticales → Energía → «Consumo del municipio» → tarjeta «Descargar
  suministros y consumos». Filtros: fechas (por defecto los últimos 12 meses
  completos) y tipo (todos, alumbrado público, edificios y resto).
- **Endpoints** (permiso `ver_energia`):
  `GET /api/v1/verticales/energia/anexos.xlsx?desde=&hasta=&tipo=` y
  `GET /api/v1/verticales/energia/anexos/{i|ii}.csv` (CSV con «;» y coma decimal).
- **Anexo I** (un CUPS por fila): dirección, municipio, provincia, peaje de acceso,
  tensión y potencias P1–P6 del detalle de contrato de Datadis (`get-contract-detail-v2`,
  guardado en `metadatos.contrato` en cada carga privada), distribuidora y su CIF
  (tabla `CIF_DISTRIBUIDORAS`; si no se conoce, en blanco).
- **Anexo II** (por peaje): número de CUPS y kWh en cada periodo T1–T6, calculados
  desde la curva horaria con los periodos de la Circular 3/2020 (Península; fines de
  semana y festivos nacionales de fecha fija en el periodo más barato).
- El Excel añade una hoja «Detalle por CUPS» (kWh por periodo de cada suministro) y
  otra de «Notas» con la metodología.
- **Datos que Datadis no da**: «Esencial (SI/NO)» y el CIF de distribuidoras
  pequeñas: salen en blanco para que los complete el Ayuntamiento.

Los datos de contrato se rellenan en la siguiente carga privada (`datadis_carga
--solo privado`); hasta entonces peaje, tensión y potencias salen vacíos.
