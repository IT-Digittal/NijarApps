# Runbook · Series oficiales de turismo (INE, Junta de Andalucía, AENA)

Alimentan los KPIs «Pernoctaciones» y «Pasajeros AENA», el bloque «Indicadores
oficiales frente al año pasado» de la Vista de Gobierno (Turismo y portada) y el
factor de expansión del modelo de afluencia. Son fuentes públicas: **no hace
falta usuario ni clave**.

| Conector (`fuente`) | Serie | Origen | Periodicidad |
|---|---|---|---|
| `ine_eoh` | Pernoctaciones hoteleras, provincia de Almería | INE · EOH, serie `EOT1460` (tabla 2074) | mensual |
| `ine_frontur` | Turistas internacionales, Andalucía | INE · FRONTUR, serie `FREG351` (tabla 10823) | mensual |
| `ine_egatur` | Gasto de los turistas internacionales, Andalucía | INE · EGATUR, serie `FREG537` (tabla 10839), agregada por trimestres completos | trimestral |
| `junta_andalucia` | Viajeros alojados en hoteles, provincia de Almería | IECA (BADEA), consulta `8035`: explotación de la EOH por la Junta | mensual |
| `aena` | Pasajeros del aeropuerto de Almería (LEI), llegadas y salidas | Excel mensual de [aena.es/es/estadisticas/informes-mensuales](https://www.aena.es/es/estadisticas/informes-mensuales.html) | mensual |

Código: `src/nijar_dti/connectors/contexto/oficiales.py` (clientes HTTP y
lectores de formato) y `fuentes.py` (conectores).

## Cómo funciona

- **INE**: API Tempus3 (`servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{serie}`).
  El INE la para a menudo por mantenimiento (503); entonces se descarga el JSON
  de la tabla completa de INEbase (`www.ine.es/jaxiT3/files/t/es/json/{tabla}.json`).
- **Junta (IECA)**: API BADEA (`…/institutodeestadisticaycartografia/intranet/admin/rest/v1.0`).
  Primero se piden los identificadores de los meses (`jerarquia/5`) y luego la
  consulta con `posord` para tener la serie temporal. El servidor corta
  conexiones a menudo: cada petición se reintenta 4 veces.
- **AENA**: no tiene API. Se leen los enlaces de la página de informes mensuales
  de cada año, se descargan los Excel y se toma la fila «ALMERÍA» del bloque de
  pasajeros (admite el formato actual «Ranking mensual» y el anterior a 2024,
  con una hoja por mes).

Los datos reales nunca llevan `metadatos.sintetico`; los provisionales llevan
`metadatos.provisional = true`. Cuando una fuente responde se **borran sus series
sintéticas** de demostración, para no mezclar meses inventados con datos oficiales.

## Cuándo se actualiza

- **Primer arranque** (`seed_loader`): carga series sintéticas (rápido, marcadas
  como «Dato de demostración») y, a los 2 minutos, el refresco las sustituye por
  las oficiales. La fuente que no responda sigue en demostración hasta el siguiente intento.
- **Cada día** a las `CONTEXTO_HORA_ACTUALIZACION`:45 (hora de Madrid, por defecto 9:45)
  se vuelven a descargar (el INE y AENA publican hacia mediados de mes). Si al
  arrancar aún quedan series sintéticas, la primera descarga se hace a los 2 minutos.
- **A mano**:

  ```bash
  docker compose exec api python -m nijar_dti.workers.contexto_backfill --guardar
  ```

## Configuración

```env
CONTEXTO_BACKFILL_DRY_RUN=false     # true = solo series sintéticas (sin red)
CONTEXTO_BACKFILL_ANIOS=3           # años de histórico
CONTEXTO_HORA_ACTUALIZACION=9       # -1 desactiva el refresco diario
```

El servidor necesita salida HTTPS a `servicios.ine.es`, `www.ine.es`,
`www.juntadeandalucia.es` y `www.aena.es`.

## Etiquetado en la Vista de Gobierno

Cada KPI o bloque se etiqueta según **sus** series: «Pernoctaciones» es real en
cuanto `ine_eoh` tiene dato real aunque AENA siga en demostración; un bloque que
mezcla series reales y sintéticas sale como «Real + demo».

## Si algo falla

- `error: INE … no disponible`: Tempus3 e INEbase caídos a la vez; reintentar más tarde.
- `error: AENA sin datos`: AENA cambió el formato del Excel o la página; revisar
  `leer_excel_aena()` con un Excel reciente.
- `error: IECA no disponible`: cortes del servidor de la Junta; el refresco del
  día siguiente lo recupera. Si devuelve `NO_DATA`, revisar los ids de la consulta 8035.
