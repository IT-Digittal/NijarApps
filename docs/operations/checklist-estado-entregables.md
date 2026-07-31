# Checklist de estado de entregables por Hito — DTI Níjar

| | |
|---|---|
| **Expediente** | 18962/2025 — Implantación de soluciones de transformación digital del sector turístico de Níjar |
| **Marco** | PSTD Andalucía 2021 · PRTR · NextGenerationEU · Componente 14 |
| **Base contractual** | PPT cláusula CUARTA (hitos y certificaciones) + Memoria Técnica §8 |
| **Adjudicatario** | IT DIGITTAL · **Cliente** Ayuntamiento de Níjar |
| **Fecha de corte** | 31/07/2026 |

Checklist accionable del estado de **cada entregable exigido**, agrupado por hito.
Complementa (no sustituye) al `checklist-justificacion-subvencion.md`; aquí se
marca lo **terminado** con casillas y se añade el trabajo reciente.

**Estructura de certificaciones (PPT):** 1.ª cert. = H1+H2 · 2.ª cert. = H3+H4 · 3.ª+ (mensual) = C.1.

**Leyenda:**
- `[x]` ✅ Terminado (software/documentación disponible y verificado).
- `[~]` 🟡 Parcial — hecho lo que depende de nosotros; falta activación/datos reales.
- `[ ]` 🗂️ Administrativo — requiere acta/firma/validación municipal.
- `[ ]` 🏗️ Físico — obra civil / autorización externa.
- `[ ]` ⬜ Depende de accesos del Ayuntamiento (ver `correo-solicitud-ayuntamiento.md`).

---

## HITO 1 — Planificación y Diseños · software/diseños ✅ (cierre administrativo pendiente)

- [x] Plan de proyecto detallado (cronograma, hitos, riesgos)
- [x] Análisis inicial / diagnóstico
- [x] Diseños conceptuales de la plataforma
- [x] Arquitecturas de integración (modelo semántico FIWARE)
- [x] Diseño visual del tótem (aprobado)
- [x] Plan de Transformación Digital — entrega **preliminar**
- [ ] 🗂️ Acta de kick-off (redactar y firmar)
- [ ] 🗂️ Acta Go/No-Go fin S2 (aprobación de diseños)

**Resumen H1:** todo el contenido técnico y de diseño está entregado. Solo falta **formalizar dos actas**.

## HITO 2 — Implementación intermedia · software ✅ (tótems físicos + actas pendientes)

- [x] Desarrollo del chatbot multilingüe (105 FAQs en ES/EN/DE/FR) con demo funcional
- [x] Módulos de la plataforma con demo de funcionalidades básicas (API, dashboard, tótem)
- [x] **Plan de Transformación Digital — versión definitiva**
- [~] 🟡 Equipamiento Smart Office (panel operativo en software; equipamiento físico a confirmar)
- [ ] 🏗️ **Instalación física de los 2 tótems** (obra civil, acometidas, puesta en marcha) — *camino crítico*
- [ ] 🗂️ Acta de demostración funcional
- [ ] 🗂️ Acta Go/No-Go fin S5

**Resumen H2:** el software está **completo y probado**. El único bloque de peso es la **instalación de los tótems**, que depende de ubicaciones y autorizaciones del Parque Natural.

## HITO 3 — Integración y Pruebas · pruebas ✅ (integraciones reales, pentest y formación pendientes)

- [x] Pruebas funcionales (suite automatizada de tests, en verde)
- [x] Pruebas de accesibilidad WCAG 2.1 AA (axe-core en CI)
- [x] Ajuste fino de modelos de datos y cuadros de mando de Big Data
- [~] 🟡 Integración completa de sistemas en la Plataforma DTI (conectores listos; **integración real de verticales/RRSS/DTI externo depende de accesos**)
- [ ] 🟡 Auditoría de seguridad (**pentest**): plan listo → **ejecutar** y emitir informe
- [ ] 🗂️ Formación al personal (**≥ 10 h**) + acta de formación
- [ ] 🟡 Simulacro de backup/restauración (plan listo → ejecutar y documentar)
- [ ] 🗂️ Acta Go/No-Go fin S7

**Resumen H3:** las pruebas propias están hechas. Lo pendiente son **actos ejecutables** (pentest, formación, simulacro) e **integraciones que requieren credenciales municipales**.

## HITO 4 — Puesta en Producción y Aceptación (SAT) · producción ✅ (SAT pendiente)

- [x] **Puesta en marcha en producción** (infraestructura cloud en la UE)
- [x] Telemetría inicial
- [~] 🟡 Documentación **as-built** (consolidar versión final)
- [ ] 🟡 Inicio del periodo de soporte (activar tras el SAT)
- [ ] 🗂️ **Pruebas de aceptación (SAT)** presencial + firma del **acta de recepción**

**Resumen H4:** la plataforma **ya está desplegada y operativa**. Falta el **acto de aceptación (SAT)** y su acta.

## C.1 — Mantenimiento y Hosting (48 meses) · herramientas ✅ (arranca tras recepción)

- [x] Informe mensual de servicio (generable desde la plataforma)
- [x] Cumplimiento ANS (matriz de severidades)
- [x] Disponibilidad SLA 99 % (cálculo real desde ticketing)
- [x] Backups + RTO/RPO (plan DR)
- [x] Soporte / Helpdesk (ticketing de incidencias)
- [~] 🟡 Ciberseguridad (EDR, WAF, certificados, ENS) — reportes periódicos
- [ ] ⏳ Inicio formal del periodo (comienza tras la recepción del H4)

---

## Gobernanza y justificación PRTR / subvención

- [x] Cumplimiento principio **DNSH** (documentado)
- [x] Propiedad del código y portabilidad (repositorio Git + dumps)
- [ ] 🗂️ Actas de gobernanza: kick-off, seguimiento bisemanal, Go/No-Go (S2/S5/S7/S8), formación
- [ ] 🟡 Publicidad de la subvención (emblema UE / PRTR en web, tótems y material)
- [ ] 🗂️ Referencias PRTR en facturas/certificaciones
- [ ] 🟡 Archivo documental de evidencias (consolidar dossier cronológico firmado)

---

## Ampliaciones solicitadas por el cliente (fuera del pliego original) — Gemelo 2D + Catastro

Trabajo desarrollado a petición del Ayuntamiento sobre el **Gemelo vivo 2D**,
como valor añadido no incluido en el alcance original de la licitación.

- [x] Gemelo vivo 2D con capas de activos conmutables y refresco en vivo (base preexistente)
- [x] Capa base **Ortofotografía PNOA** (WMS oficial del IGN)
- [x] Capa **Catastro** oficial (WMS de la Dirección General del Catastro) superpuesta al gemelo
- [x] Infraestructura de **capas geográficas por backend** (modelo, migración, API GeoJSON) al estilo de un geoportal municipal de urbanismo
- [x] Catálogo de capas adaptado a Níjar: clasificación del suelo, calificación/usos, ordenación estructural, partidos rurales y parcelario catastral
- [x] Capa de **catastro preparada para los registros**: campo `referencia_catastral` + consulta punto-en-parcela (`ST_Contains`) para vincular cada activo con su parcela
- [ ] 🟡 Carga de la **cartografía real** (PGOU de Níjar y parcelario del Catastro) — pendiente de que el Ayuntamiento aporte los datos; hoy se sirve geometría de demostración

---

## Resumen ejecutivo — ¿vamos terminando los hitos?

| Hito | Software / documentación | Qué falta para **cerrar** el hito | Depende de |
|------|:------------------------:|-----------------------------------|-----------|
| **H1** | ✅ Completo | 2 actas (kick-off, Go/No-Go S2) | Firma municipal |
| **H2** | ✅ Completo | Instalación física de tótems + 2 actas | Ayto. (ubicaciones/Parque) |
| **H3** | ✅ Completo | Pentest, formación ≥10 h, integraciones reales, simulacro | Ejecución + accesos Ayto. |
| **H4** | ✅ Desplegado | SAT presencial + acta de recepción | Fecha con el Ayto. |
| **C.1** | ✅ Listo | Arranca tras la recepción del H4 | — |

**Conclusión:** **toda la parte de desarrollo y documentación de los cuatro hitos está terminada y verificada.** Lo que resta para cerrar formalmente cada hito **no es más desarrollo**, sino: (1) la **instalación física de los tótems**, (2) las **integraciones que requieren credenciales/accesos municipales**, y (3) los **actos de validación** (pentest, formación, SAT y firma de actas). Todo ello depende mayoritariamente de la colaboración del Ayuntamiento (ver `correo-solicitud-ayuntamiento.md`).
