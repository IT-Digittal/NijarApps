# Subtarea 5.8 — Validación de Accesibilidad WCAG 2.1 AA

> **Plataforma DTI Níjar · Expediente 18962/2025 · IT DIGITTAL**

Este paquete cierra la **subtarea 5.8 del Plan de Trabajo Pre-SAT**: validación automática del cumplimiento WCAG 2.1 nivel AA sobre los frontales del proyecto (tótem y dashboard).

## Contenido del paquete

```
accessibility-5.8/
├── scripts/
│   ├── audit-accessibility.js       Script principal (Node.js + Playwright + axe-core + Lighthouse)
│   ├── audit-accessibility.ps1      Wrapper PowerShell (Windows)
│   ├── audit-accessibility.bat      Wrapper batch (Windows, doble clic)
│   └── package.json                 Dependencias
│
├── workflows/
│   └── accessibility.yml            Workflow GitHub Actions BLOQUEANTE
│
├── docs/
│   ├── Plan_Auditoria_Accesibilidad_5.8.docx    Plan auditoría documentado
│   └── Plan_Auditoria_Accesibilidad_5.8.pdf
│
├── templates/
│   └── Plantilla_Hallazgos_Accesibilidad.xlsx   Tablero de seguimiento
│
└── README.md                                     Este archivo
```

## Cómo aplicarlo al proyecto

### 1. Mueve los archivos a su sitio definitivo en el repo

```powershell
# Desde la raíz del proyecto C:\dev\nijar-dti-platform
Copy-Item accessibility-5.8\scripts\* scripts\
Copy-Item accessibility-5.8\workflows\accessibility.yml .github\workflows\
Copy-Item accessibility-5.8\docs\* docs\security\
Copy-Item accessibility-5.8\templates\* docs\templates\
```

Estructura resultante en el proyecto:

```
nijar-dti-platform/
├── scripts/
│   ├── audit-accessibility.js
│   ├── audit-accessibility.ps1
│   ├── audit-accessibility.bat
│   └── package.json
├── .github/workflows/
│   └── accessibility.yml          ← se ejecuta automáticamente en cada PR
├── docs/security/
│   ├── Plan_Auditoria_Accesibilidad_5.8.docx
│   └── Plan_Auditoria_Accesibilidad_5.8.pdf
└── docs/templates/
    └── Plantilla_Hallazgos_Accesibilidad.xlsx
```

### 2. Asegúrate de que el proyecto está arrancado en local

```powershell
.\windows\start.bat
```

Espera a que `http://localhost:8000` responda.

### 3. Ejecuta tu primera auditoría

```powershell
.\scripts\audit-accessibility.bat
```

La primera ejecución tarda **2-5 minutos** (instala Playwright + Chromium + dependencias). Las siguientes serán de **30-60 segundos**.

## Salida que vas a ver

Tras la auditoría se genera:

```
reports/accessibility/audit-2026-05-08/
├── index.html              ← informe HTML navegable (este es el principal)
├── findings.json           ← datos crudos
├── findings.xlsx           ← plantilla de seguimiento generada automáticamente
└── lighthouse/
    ├── totem-home.html
    ├── totem-high-contrast.html
    ├── totem-text-large.html
    ├── dashboard-home.html
    └── dashboard-environment.html
```

Abre `index.html` en el navegador y verás un informe consolidado:

- **Banda superior con el veredicto**: ✅ AUDITORÍA SUPERADA o ❌ AUDITORÍA FALLIDA
- **4 KPIs**: bloqueantes / informativas / páginas auditadas / reglas OK acumuladas
- **Resultados por página**: cada una con su score Lighthouse, número de violaciones por severidad, y detalle de cada hallazgo (descripción, regla axe, link a documentación, fragmento HTML problemático)

## Cómo interpretar el resultado

### Si dice "AUDITORÍA SUPERADA" ✅

- 0 violaciones críticas
- 0 violaciones serias
- Lighthouse ≥ 90/100 en todas las páginas

→ El proyecto cumple WCAG 2.1 AA. Adjunta este informe como evidencia para el SAT.

### Si dice "AUDITORÍA FALLIDA" ❌

Mira el bloque rojo de cada página y aplica el ciclo de corrección:

1. **Identifica** qué regla axe se viola (ej: `color-contrast`)
2. **Localiza el elemento** en el código (selector CSS dado en el informe)
3. **Aplica el fix**:
   - Si es paleta o tipografía → editar `frontend/shared/design-tokens.css`
   - Si es del componente → editar el CSS o HTML del componente
4. **Reauditar** (`.\scripts\audit-accessibility.bat`)
5. **Si está cerrado** → marca la fila correspondiente en `findings.xlsx` con estado "Cerrado"
6. **Si persiste** → vuelve al paso 3

## Variantes de ejecución

```powershell
# Solo el tótem (más rápido)
.\scripts\audit-accessibility.ps1 -Only totem

# Solo el dashboard
.\scripts\audit-accessibility.ps1 -Only dashboard

# Modo estricto (incluye violaciones moderate y minor en el informe,
# pero NO falla la auditoría por ellas)
.\scripts\audit-accessibility.ps1 -Strict

# Contra otra URL base (si pruebas en pre-producción)
.\scripts\audit-accessibility.ps1 -BaseUrl https://staging.dti.nijar.es
```

## CI bloqueante en GitHub Actions

El workflow `accessibility.yml` se ejecuta automáticamente en:

- **Cada Pull Request** que toque `frontend/` o el script de auditoría
- **Cada push a main** que afecte el frontend
- **Manualmente** desde la pestaña "Actions" de GitHub

### Qué hace el CI

1. Levanta PostgreSQL + Redis + FastAPI en el runner
2. Instala dependencias y ejecuta la auditoría
3. **Sube el informe HTML como artifact** descargable durante 30 días
4. **Comenta el resultado en el PR automáticamente**
5. **Falla el merge** si hay violaciones bloqueantes

Ejemplo de comentario que aparece en el PR:

> ## Auditoría de Accesibilidad WCAG 2.1 AA
>
> ✅ **AUDITORÍA SUPERADA**
>
> **Total:** 0 bloqueantes · 3 informativas
>
> ### Por página
> ✅ **Tótem — pantalla principal** — 0 bloqueantes · 1 info · Lighthouse 96/100
> ✅ **Tótem — modo alto contraste activo** — 0 bloqueantes · 0 info · Lighthouse 98/100
> ✅ **Dashboard — pestaña Resumen** — 0 bloqueantes · 2 info · Lighthouse 92/100

## Plantilla de hallazgos (Excel)

`Plantilla_Hallazgos_Accesibilidad.xlsx` tiene 3 pestañas:

- **Dashboard** — KPIs auto-calculados (totales por severidad, abiertos vs cerrados, veredicto)
- **Hallazgos** — registro individual de cada hallazgo con flujo de corrección. Listas desplegables para Severidad y Estado. Formato condicional (filas verdes cuando se cierran).
- **Reglas comunes** — referencia rápida de las 12 reglas axe-core que más aparecen, con descripción y fix típico.

Esta plantilla se rellena manualmente por el equipo. La auditoría automática también genera una plantilla por ejecución (`findings.xlsx` dentro de `reports/`), pero la plantilla maestra del proyecto debería ser la que viva en `docs/templates/` y mantenga el histórico completo.

## Plan de auditoría documentado

`Plan_Auditoria_Accesibilidad_5.8.docx/pdf` (231 párrafos) es el documento formal de evidencia. Contiene:

1. **Contexto y marco normativo** — RD 1112/2018, WCAG 2.1, UNE 139803, ENS, Pliego
2. **Metodología** — herramientas, tags evaluados, criterios de aceptación, severidades axe
3. **Páginas auditadas** — las 5 páginas tipo cubiertas
4. **Procedimiento de ejecución** — manual local + CI automático
5. **Gestión de hallazgos** — plantilla, procedimiento de corrección, no bloqueantes
6. **Evidencia para el SAT** — qué se aporta y declaración de accesibilidad
7. **Responsabilidades** — quién hace qué en el equipo

Este documento se incorpora al expediente administrativo del proyecto.

## Estado de la tarea T-05

- ✅ 5.1-5.4 — Recopilación + 3 propuestas
- ✅ 5.5 — Reunión validación
- ✅ 5.6 — Iteración hasta aprobación final
- ✅ 5.7 — Implementación en código
- ✅ 5.8 — **Validación accesibilidad WCAG 2.1 AA (este paquete)**
- ✅ 5.9 — Acta de aprobación visual firmada

**T-05 cerrada al 100 %** una vez se ejecute esta auditoría sobre el código real con resultado superado.

## Próximos pasos del Plan

Con T-05 cerrada, las siguientes prioridades del Plan Pre-SAT son:

| Tarea | Descripción | Cuándo |
|---|---|---|
| **T-13** | Manuales con capturas reales del nuevo diseño | Tras T-05 cerrada |
| **T-09** | Suite de tests E2E con Playwright (parte del flujo ya está montado por esta tarea) | Semanas 1-4 |
| **T-06** | Catálogo turístico real | Semanas 1-6 (paralelo) |
| **T-07** | FAQs ampliadas chatbot | Semanas 2-7 (paralelo) |

---

**Dudas o problemas técnicos**: contactar con Frontend / UX (responsable principal de accesibilidad) o DevOps / SRE (responsable del workflow CI).

_Plataforma DTI Níjar · Subtarea 5.8 del Plan de Trabajo Pre-SAT · Versión 1.0_
