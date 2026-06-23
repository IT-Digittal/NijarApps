# Checklist de justificación de la subvención por Hitos y entregables

| | |
|---|---|
| **Expediente** | 18962/2025 — DTI Níjar |
| **Marco** | PSTD Andalucía 2021 · PRTR · NextGenerationEU · Componente 14 |
| **Objeto** | Justificar ante el Ayuntamiento / Junta de Andalucía / PRTR los trabajos realizados por hito |
| **Base** | PPT cláusula CUARTA (hitos y certificaciones) + Memoria Técnica §8 |

**Estructura de certificaciones (PPT, pagos al contratista):**
- **1.ª certificación** → justifica **Hitos 1 y 2**.
- **2.ª certificación** → justifica **Hitos 3 y 4**.
- **3.ª y siguientes (mensuales)** → mantenimiento y hosting **C.1** (48 meses).

**Leyenda de estado:**
- ✅ Entregable disponible (en repo / generable).
- 🟡 Parcial / pendiente de datos reales o de activación.
- 🗂️ Administrativo: requiere acta, firma o validación municipal.
- 🏗️ Físico / obra civil / autorización externa.
- ⬜ Depende del Ayuntamiento (acceso/decisión) — ver correo de solicitud.

---

## HITO 1 — Planificación y Diseños (1.ª certificación)

| Entregable exigido | Estado | Evidencia / documento | Acción para justificar |
|--------------------|--------|-----------------------|------------------------|
| Plan de proyecto detallado | ✅ | `docs/architecture/` + Memoria Técnica §8 (cronograma, hitos, riesgos) | Consolidar en PDF firmado |
| Análisis inicial / diagnóstico | ✅ | Memoria Técnica §5; Plan Director §3-4 (`docs/plan-director/`) | — |
| Diseños conceptuales de la plataforma | ✅ | `docs/architecture/arquitectura-global.md`, `diagramas-tecnicos.md`, Anexos A3 | — |
| Arquitecturas de integración | ✅ | `docs/architecture/` + `docs/data-model/` (modelo semántico) | — |
| Diseño visual del tótem (aprobado) | ✅ | `Acta_Aprobacion_Diseno_Visual_Totem.docx`, SVGs de pantallas | Verificar firma del acta |
| Plan de Transformación Digital (entrega **preliminar**) | ✅ | `docs/plan-director/plan-transformacion-digital.md` | Presentar versión preliminar |
| Acta de kick-off | 🗂️ | — | Redactar y firmar (Dir. Proyecto + responsable municipal) |
| Acta Go/No-Go fin S2 (aprobación diseños) | 🗂️ | — | Emitir acta de aprobación de diseños |

## HITO 2 — Implementación intermedia (1.ª certificación)

| Entregable exigido | Estado | Evidencia / documento | Acción para justificar |
|--------------------|--------|-----------------------|------------------------|
| Instalación física de los tótems (obra civil) | 🏗️ | — | Ejecutar instalación; albaranes + fotos + acta |
| Equipamiento Smart Office | 🟡 | Panel Smart Office operativo (software) | Confirmar equipamiento físico si aplica |
| Desarrollo inicial del chatbot | ✅ | `services/chatbot_service.py` + Rasa; 105 FAQs; demo en `/totem` | Demo funcional grabada/presencial |
| Módulos de plataforma con demo de funcionalidades básicas | ✅ | API (45 endpoints), dashboard, tótem; `docs/MAPA-FUNCIONAL.md` | Demostración funcional |
| **Plan de Transformación Digital definitivo** | ✅ | `docs/plan-director/plan-transformacion-digital.md` | Entregar versión definitiva |
| Demostración de funcionalidades (acta) | 🗂️ | — | Acta de demo / inspección |
| Acta Go/No-Go fin S5 | 🗂️ | — | Emitir acta |

> **Nota:** el software del Hito 2 está completo y probado (264 tests). El elemento de mayor riesgo para esta certificación es la **instalación física de los tótems** (camino crítico) — depende de ubicaciones, autorizaciones del Parque y acometidas (ver correo de solicitud §4).

## HITO 3 — Integración y Pruebas (2.ª certificación)

| Entregable exigido | Estado | Evidencia / documento | Acción para justificar |
|--------------------|--------|-----------------------|------------------------|
| Integración completa de sistemas en la Plataforma DTI | 🟡 | Plataforma + conectores; **integración real de verticales pendiente** (DTI externo, RRSS reales) | Conectar verticales (depende del Ayto.) |
| Pruebas funcionales | ✅ | Suite de 264 tests; `pytest` | Informe de pruebas |
| Pruebas de seguridad (pentest) | 🟡 | `docs/security/plan-pentest-sat.md` (plan); CI con escáneres | **Ejecutar pentest** y emitir informe |
| Pruebas de accesibilidad (WCAG 2.1 AA) | ✅ | `docs/accessibility/wcag-2.1-AA-compliance.md`; axe-core en CI | Informe de accesibilidad |
| Ajuste fino de modelos de datos y dashboards Big Data | ✅ | Observatorio, KPIs, predicción/MAPE, panel cableado | — |
| Formación inicial al personal (≥ 10 h) | 🗂️ | `docs/onboarding/`, manuales | Impartir formación + **acta de formación** |
| Simulacro de backup/restauración | 🟡 | `docs/operations/disaster-recovery.md` | Ejecutar simulacro y documentar |
| Acta Go/No-Go fin S7 | 🗂️ | — | Emitir acta |

## HITO 4 — Puesta en Producción (2.ª certificación)

| Entregable exigido | Estado | Evidencia / documento | Acción para justificar |
|--------------------|--------|-----------------------|------------------------|
| Puesta en marcha en producción | ✅ | **Desplegado y operativo** en producción (cloud UE); `infra/terraform/`, `infra/k8s/` | — |
| **Pruebas de aceptación (SAT) con el Ayuntamiento** | 🗂️ | `docs/operations/checklist-evidencias-sat.md` (guion) | Ejecutar SAT y firmar **acta de recepción** |
| Documentación **as-built** | 🟡 | `docs/` (arquitectura, manuales, operaciones) | Consolidar versión as-built final |
| Inicio del periodo de soporte | 🟡 | Helpdesk/ANS (`/incidencias`), monitorización | Activar soporte tras SAT |
| Telemetría inicial | ✅ | `/chatbot/telemetry`, `/dashboards/*`, `/metrics` | Captura de telemetría inicial |

## C.1 — Mantenimiento y hosting (certificaciones mensuales 3.ª+)

| Entregable exigido | Estado | Evidencia / documento | Acción para justificar |
|--------------------|--------|-----------------------|------------------------|
| Informe mensual de servicio | ✅ | `/dashboards/monthly-report`; ejemplo `docs/operations/ejemplo-informe-mensual.md` | Generar informe del mes |
| Cumplimiento ANS (matriz de severidades) | ✅ | `/incidencias/ans`, `core/ans.py` | Adjuntar al informe mensual |
| Disponibilidad SLA 99 % | ✅ | Cálculo real desde ticketing; `docs/operations/sla-monitoring.md` | Reporte de disponibilidad |
| Backups, RTO/RPO 24 h | ✅ | `docs/operations/disaster-recovery.md` | Evidencia de backups |
| Ciberseguridad (EDR, WAF, certificados, ENS) | 🟡 | `infra/`, planes ENS | Reportes periódicos |
| Soporte/Helpdesk | ✅ | Ticketing `/incidencias` | Registro de tickets |

---

## Documentación de gobernanza (Memoria Técnica §8.5)

> Plantillas listas para rellenar y firmar en **`docs/actas/`**.

| Documento | Frecuencia | Estado |
|-----------|------------|--------|
| Acta de kick-off | Única (S1) | 🗂️ Pendiente |
| Actas de seguimiento bisemanal | Cada 2 sem. | 🗂️ Pendiente (según ejecución) |
| Actas Go/No-Go (fin S2, S5, S7, S8) | Por hito | 🗂️ Pendiente |
| Informes de validación del modelo analítico | Por versión | ✅ Metodología (`docs/big-data/`) + ejecutar validación |
| Informes mensuales de servicio (C.1) | Mensual | ✅ Generable |
| Registro de riesgos | Vivo | ✅ Memoria Técnica §8.4 |
| Actas de formación | Por sesión | 🗂️ Pendiente |

## Documentación de justificación PRTR / subvención

| Requisito | Base | Estado | Acción |
|-----------|------|--------|--------|
| Referencias PRTR en facturas/certificaciones | PPT cláusula CUARTA | 🗂️ | Incluir nº certificación, expediente, «PRTR-NextGenerationEU», Componente 14, Reglamento (UE) 2021/241 |
| Publicidad de la subvención (emblema UE, etc.) | Base Reguladora 14 | 🟡 | Aplicar identidad UE/PRTR en web/tótems/material |
| Cumplimiento principio **DNSH** | Base Reguladora 20 | ✅ | Documentado (eficiencia energética, LoRaWAN, autoscaling); evidenciar |
| Obligaciones del beneficiario | Bases 18 y 19 | 🗂️ | Verificar con el Ayuntamiento |
| Propiedad del código y portabilidad | PPT QUINTA.5 | ✅ | Repositorio Git + dumps; `docs/operations/` |
| Archivo documental de evidencias | Memoria §8.5 | 🟡 | Consolidar dossier cronológico firmado |

---

## Resumen de estado

| Bloque | Listo (software/docs) | Pendiente administrativo (🗂️) | Pendiente físico/externo (🏗️/⬜) |
|--------|----------------------|-------------------------------|----------------------------------|
| H1 | Diseños, arquitectura, Plan TD preliminar | Actas kick-off y Go/No-Go S2 | — |
| H2 | Chatbot, plataforma, Plan TD definitivo | Actas de demo y Go/No-Go S5 | Instalación física de tótems |
| H3 | Pruebas func., accesibilidad, dashboards | Acta formación, Go/No-Go S7 | Pentest, integración verticales reales |
| H4 | Producción desplegada, telemetría, guion SAT, as-built | **Acta de recepción (SAT)** | — |
| C.1 | Informe mensual, ANS, DR, ticketing | — | Reportes recurrentes |

### Acciones prioritarias para cerrar la justificación
1. **Instalar los tótems** (camino crítico del H2) — requiere accesos/autorizaciones del Ayuntamiento.
2. **Ejecutar el pentest** y emitir informe (H3).
3. **Impartir la formación ≥10 h** y firmar acta (H3).
4. **Ejecutar el SAT** y firmar el **acta de recepción** (H4).
5. **Emitir las actas de gobernanza** (kick-off, seguimiento, Go/No-Go).
6. **Facilitar el dominio municipal** para publicar los servicios ya desplegados en producción.
7. **Aplicar la publicidad PRTR/UE** y las referencias en facturas/certificaciones.

> Documentos de apoyo ya disponibles: `checklist-evidencias-sat.md`, `MAPA-FUNCIONAL.md`, `plan-director/`, `big-data/` (metodología + plan de mejora), `security/` (pentest + DPIA), `operations/` (runbook, DR, SLA, continuidad, informe mensual de ejemplo) y `correo-solicitud-ayuntamiento.md`.
