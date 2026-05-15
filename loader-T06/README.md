# Subtarea 6.8 — Cargador del Catálogo Turístico

> **Plataforma DTI Níjar · Expediente 18962/2025 · IT DIGITTAL**

Este paquete cierra la **subtarea 6.8 del Plan de Trabajo Pre-SAT**: script de carga del catálogo de recursos turísticos en el backend del proyecto, listo para ejecutar cuando el Ayuntamiento devuelva la plantilla rellenada (subtarea 6.1).

## Contenido del paquete

```
loader-T06/
├── scripts/
│   ├── load_catalog.py                        Script principal Python (~700 líneas)
│   ├── load-catalog.ps1                       Wrapper PowerShell
│   └── load-catalog.bat                       Wrapper batch (Windows)
│
├── sample-data/
│   └── Plantilla_Catalogo_Recursos_Nijar_EJEMPLO.xlsx
│       └── 10 recursos reales de Níjar para probar el script ya
│
├── docs/
│   └── README.md                              Este archivo
│
└── outputs/                                   Reportes generados (vacío al inicio)
```

## Qué hace el script

`load_catalog.py` toma la plantilla Excel rellenada por el Ayuntamiento (la pestaña **Recursos**) y crea cada fila como un recurso o servicio en el backend del proyecto, llamando a la API REST autenticada con OAuth2 + JWT.

### Flujo completo

```
┌────────────────────┐         ┌─────────────────┐
│ Plantilla Excel    │         │  Backend FastAPI │
│ del Ayuntamiento   │  ──>    │  /api/v1/...     │
│ (rellena T-06.1)   │  ──>    │                  │
└────────────────────┘         └─────────────────┘
        │                              │
        │                              │
        ▼                              ▼
   1. Lee la pestaña "Recursos"   3. Login OAuth2 (admin/gestor)
   2. Valida cada fila            4. POST /resources, /services
        │                         5. publicado=False (revisión Ayto)
        ▼                              ▼
   ┌──────────────────────────────────────┐
   │ Reporte HTML + CSV + JSON            │
   │ reports/catalog-load/                │
   │   reporte-carga-YYYYMMDD.html        │
   └──────────────────────────────────────┘
```

### Categorización automática

La plantilla usa nombres de categoría en lenguaje natural (Playa, Mirador, Restaurante, etc.), pero el backend exige enums estrictos según `schemas/tourism.py`. El script mapea automáticamente:

| Categoría en plantilla | Va a... | Como... |
|---|---|---|
| Playa, Mirador, Ruta senderista, Patrimonio | `RecursoTuristico` | playa, mirador, ruta, monumento... |
| Restaurante, Bar, Cafetería | `Servicio` | gastronomia_restaurante, gastronomia_bar... |
| Alojamiento, Hotel, Casa rural | `Servicio` | alojamiento_hotel, alojamiento_rural... |
| Servicio público, Aparcamiento | `RecursoTuristico` | punto_interes |
| Oficina de turismo | `RecursoTuristico` | oficina_turismo |
| Centro de visitantes | `RecursoTuristico` | centro_visitantes |

Los recursos turísticos van al endpoint `POST /api/v1/tourism/resources` y los servicios privados (negocios) al endpoint `POST /api/v1/tourism/services`, conforme al modelo de datos del proyecto.

### Validaciones aplicadas antes de enviar

1. **Campos obligatorios**: ID interno, nombre, descripción corta, categoría, GPS
2. **Formato de ID**: solo mayúsculas, números y guiones (ej: `R-001`)
3. **Coordenadas dentro del bounding box de Níjar**: detecta errores tipográficos groseros (un recurso fuera de Andalucía es probablemente un fallo de tipeo)
4. **Categoría reconocida**: tiene que mapear a uno de los enums del backend
5. **Generación automática de URN NGSI-LD**: `urn:ngsi-ld:RecursoTuristico:nijar:r-001`
6. **Parser inteligente de contacto**: extrae teléfono, email y web de una celda de texto libre

### Importante — `publicado=False`

**Todos los recursos se crean con `publicado=False`** independientemente de lo que diga la plantilla. Esto es deliberado:

- Los datos llegan al backend pero NO aparecen en los tótems hasta que el Gestor de Contenidos del Ayuntamiento entre al CMS, los revise uno por uno y le dé al toggle "publicar".
- Es un control de calidad necesario, especialmente con datos llegados de fuera del proyecto (autores externos, traducciones automáticas, fotos sin verificar).

Para publicar masivamente, se hará en otra subtarea posterior tras la validación del Ayuntamiento.

## Cómo usarlo — paso a paso

### Antes de empezar (una sola vez)

```powershell
# 1. Asegúrate de tener Python 3.11+
python --version

# 2. Mueve los archivos a su sitio en el repo del proyecto
Copy-Item loader-T06\scripts\* C:\dev\nijar-dti-platform\scripts\
Copy-Item loader-T06\sample-data\* C:\dev\nijar-dti-platform\docs\examples\

# 3. Asegúrate de que el proyecto está arrancado
cd C:\dev\nijar-dti-platform
.\windows\start.bat
```

### Validar la plantilla SIN tocar el backend (modo dry-run)

Útil para que el equipo del Ayuntamiento valide su plantilla antes de la carga real:

```powershell
.\scripts\load-catalog.bat -Plantilla "C:\path\a\plantilla_rellena.xlsx" -DryRun
```

Esto:
- Lee la plantilla
- Valida cada fila contra los esquemas del backend
- NO envía nada a la API
- Genera un reporte HTML con los problemas detectados

### Carga real contra backend

```powershell
# Opción 1: pasar credenciales por parámetro
.\scripts\load-catalog.bat `
  -Plantilla "C:\path\a\plantilla_rellena.xlsx" `
  -Usuario admin@nijar.es `
  -Password "CambiarEnPrimerArranque#2026"

# Opción 2: usar variables de entorno (más seguro)
$env:NIJAR_USER = "admin@nijar.es"
$env:NIJAR_PASS = "CambiarEnPrimerArranque#2026"
.\scripts\load-catalog.bat -Plantilla "C:\path\a\plantilla_rellena.xlsx"
```

### Probar YA con datos reales (sin esperar al Ayuntamiento)

```powershell
# Dry-run con la plantilla de ejemplo de 10 recursos reales de Níjar
.\scripts\load-catalog.bat `
  -Plantilla "C:\dev\nijar-dti-platform\docs\examples\Plantilla_Catalogo_Recursos_Nijar_EJEMPLO.xlsx" `
  -DryRun

# Si funciona el dry-run, lanza la carga real
.\scripts\load-catalog.bat `
  -Plantilla "C:\dev\nijar-dti-platform\docs\examples\Plantilla_Catalogo_Recursos_Nijar_EJEMPLO.xlsx" `
  -Usuario admin@nijar.es `
  -Password "CambiarEnPrimerArranque#2026"
```

Tras esto, los 10 recursos aparecerán en el dashboard del CMS (en `/dashboard`, pestaña Contenidos) con `publicado=False` listos para revisión.

## Salida que vas a ver

Tras cada ejecución se genera:

```
reports/catalog-load/
├── reporte-carga-YYYYMMDD-HHMMSS.html      ← informe principal navegable
├── reporte-carga-YYYYMMDD-HHMMSS.csv       ← datos para Excel/análisis
└── reporte-carga-YYYYMMDD-HHMMSS.json      ← datos para automatizaciones
```

El **HTML** muestra:

- **Banda superior** con el veredicto (verde si todo OK, rojo si hay errores)
- **4 KPIs**: filas procesadas / cargadas con éxito / con errores / saltadas (ya existían)
- **Tabla detalle** con una fila por recurso, su estado, errores y avisos

## Variantes y modos avanzados

```powershell
# Modo verbose (logging detallado de cada paso)
.\scripts\load-catalog.bat -Plantilla x.xlsx -DryRun -Verbose

# Contra un backend remoto en lugar del local
.\scripts\load-catalog.bat -Plantilla x.xlsx -BaseUrl https://staging.dti.nijar.es

# Sin wrapper, llamando directamente al Python
python scripts/load_catalog.py --plantilla x.xlsx --dry-run
python scripts/load_catalog.py --plantilla x.xlsx --base-url http://localhost:8000 --usuario admin@nijar.es --password ***
```

## Comportamiento ante recursos duplicados (idempotencia)

Si una fila tiene un URN que **ya existe en el backend** (porque ya se cargó en una ejecución anterior), el script:

- **No lanza error**
- **Marca esa fila como "skipped"** en el reporte
- Continúa con el resto

Esto permite **re-ejecutar el script con seguridad** sobre la misma plantilla varias veces sin generar duplicados. Útil cuando el Ayuntamiento entrega la plantilla en oleadas y queremos cargar incrementalmente.

> **Limitación actual**: si una fila YA EXISTE pero ha cambiado su contenido (descripción, foto), el script NO la actualiza. Es solo INSERT, no UPSERT. Si necesitas actualizar, hay que borrarla en el dashboard primero o usar el endpoint PUT directamente. Esto se puede ampliar en una subtarea posterior si el flujo del Ayuntamiento lo requiere.

## Códigos de salida

- `0` → carga completa sin errores
- `1` → al menos una fila falló (ver reporte HTML para detalles)
- `2` → error de configuración (plantilla no encontrada, credenciales faltantes, dependencias)

Esto permite encadenar el script en CI/CD si en el futuro se quiere automatizar la carga desde una carpeta drop-off.

## Estado del Plan de Trabajo

| Tarea | Estado |
|---|---|
| ✅ T-05 — Diseño visual | En pausa al 86% (auditoría 5.8 documentada, ejecución pendiente) |
| 🔄 **T-06 — Catálogo turístico** | 6.1 cerrada, **6.8 cerrada con este paquete** |
| ⏳ T-06.4 a 6.7 — Llenado real | En espera de respuesta del Ayuntamiento (15-20 días) |
| ⏳ T-07 — FAQs ampliadas | Pendiente |
| ⏳ T-08 — Localización 4 idiomas | Pendiente |
| ⏳ T-09 — Tests E2E Playwright | Pendiente |

---

**Plataforma DTI Níjar · Subtarea 6.8 del Plan de Trabajo Pre-SAT · Versión 1.0**
