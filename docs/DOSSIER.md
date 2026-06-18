# Dossier Pre-SAT — Exp. 18962/2025 (DTI Níjar)

| | |
|---|---|
| **Proyecto** | Implantación de soluciones de transformación digital del sector turístico de Níjar |
| **Adjudicatario** | IT DIGITTAL |
| **Marco** | PSTD Andalucía 2021 · PRTR · NextGenerationEU · Componente 14 |
| **Estándares** | UNE 178104 · FIWARE · ENS Nivel Medio · WCAG 2.1 AA · DNSH |

Índice maestro de la documentación del proyecto, ordenado para su **presentación,
verificación y firma**. Cada documento es un entregable o una evidencia de los
trabajos realizados.

---

## 0. Cómo leer este dossier

| Si necesitas… | Ve a |
|---------------|------|
| Ver el estado para **justificar la subvención** | [§1 Justificación por hitos](#1-justificación-de-la-subvención-prioritario) |
| Saber **qué pedir al Ayuntamiento** | [§2 Solicitud de accesos](#2-solicitud-al-ayuntamiento) |
| **Verificar** la plataforma (SAT) | [§3 Verificación y SAT](#3-verificación-técnica-y-sat) |
| Entender **qué hace** la solución | [§4 Documentación técnica](#4-documentación-técnica) |
| Los **entregables del Plan/observatorio** | [§5 Entregables B.2 / A.3](#5-entregables-plan-director-y-observatorio) |
| **Operar y mantener** (C.1) | [§6 Operación y C.1](#6-operación-mantenimiento-c1) |
| Las **actas** a firmar | [§7 Actas de gobernanza](#7-actas-de-gobernanza) |

---

## 1. Justificación de la subvención (prioritario)

- **[Checklist de justificación por hitos](operations/checklist-justificacion-subvencion.md)** — estado de cada entregable exigido por el PPT y la Memoria Técnica, por hitos (1.ª cert. = H1+H2, 2.ª = H3+H4, C.1 mensual). **Punto de partida.**
- [Mapa funcional consolidado](MAPA-FUNCIONAL.md) — actuaciones A.1/A.2/A.3/B.2/C.1 ↔ funcionalidades, endpoints y entregables.

## 2. Solicitud al Ayuntamiento

- **[Correo de solicitud de accesos e información](operations/correo-solicitud-ayuntamiento.md)** — todo lo que depende del Ayuntamiento (integraciones, tokens RRSS/GA4, contenidos, autorizaciones del Parque, hosting, DPD, formularios, interlocución).

## 3. Verificación técnica y SAT

- **[Checklist de evidencias para el SAT](operations/checklist-evidencias-sat.md)** — guion de verificación conjunta, requisito a requisito, con comandos.
- [Guía de pruebas de despliegue (equipo de desarrollo)](onboarding/guia-pruebas-despliegue.md) — qué probar al desplegar (panel y tótem) y notas de lint/tests.
- [Cumplimiento WCAG 2.1 AA](accessibility/wcag-2.1-AA-compliance.md) — accesibilidad.
- [Plan de pentest pre-SAT](security/plan-pentest-sat.md) — seguridad (a ejecutar).

## 4. Documentación técnica

- [Arquitectura global](architecture/arquitectura-global.md) · [Diagramas técnicos](architecture/diagramas-tecnicos.md) · [Decisiones técnicas (ADRs)](architecture/decisiones-tecnicas.md) · [Dependencias de terceros](architecture/dependencias-terceros.md)
- [API REST — OpenAPI](api/openapi.yaml) ([guía](api/README.md))
- [Modelo de datos (FIWARE)](data-model/README.md) · [Esquema SQL](database/schema.sql)
- [Manual técnico del backend](backend/manual-tecnico-backend.md) · [Manual técnico del chatbot](chatbot/manual-tecnico-chatbot.md)
- [Configuración MQTT](mqtt/mosquitto.conf)

## 5. Entregables Plan Director y observatorio

- **[Plan Director de Transformación Digital](plan-director/plan-transformacion-digital.md)** (B.2) — diagnóstico, hoja de ruta, infraestructura Smart City, CAPEX/OPEX, gobernanza.
- [Metodología y limitaciones del observatorio](big-data/metodologia-y-limitaciones.md) (A.3) — factor de expansión, IC 95 %, validación (P/R/F1 y MAPE), k-anonimato.
- [Plan de Mejora Continua del observatorio](big-data/plan-mejora-continua.md) (A.3) — catálogo M1–M8 y hoja de ruta.
- [DPIA del observatorio de movilidad](security/dpia-observatorio-movilidad.md) — RGPD.

## 6. Operación, mantenimiento (C.1)

- [Informe mensual de servicio — ejemplo cumplimentado](operations/ejemplo-informe-mensual.md) — disponibilidad, ANS, incidencias, KPIs.
- [Runbook operativo](operations/runbook.md) · [Plan de recuperación ante desastres (DR)](operations/disaster-recovery.md) · [SLA y monitorización](operations/sla-monitoring.md) · [Plan de continuidad de negocio](operations/business-continuity.md)

## 7. Actas de gobernanza

Plantillas listas para rellenar y firmar — ver **[índice de actas](actas/README.md)**:

| # | Acta | Hito |
|---|------|------|
| 01 | [Kick-off](actas/01-acta-kickoff.md) | H1 |
| 02 | [Seguimiento bisemanal](actas/02-acta-seguimiento-bisemanal.md) | H1–H4 |
| 03 | [Comité Go/No-Go](actas/03-acta-go-no-go.md) | H1–H4 |
| 04 | [Demostración funcional](actas/04-acta-demostracion-funcional.md) | H2 |
| 05 | [Formación (≥10 h)](actas/05-acta-formacion.md) | H3 |
| 06 | [Recepción provisional / SAT](actas/06-acta-recepcion-sat.md) | H4 |
| 07 | [Validación del modelo analítico](actas/07-acta-validacion-modelo-analitico.md) | H3 / C.1 |

---

## Estado global (resumen)

| Ámbito | Estado |
|--------|--------|
| Software (plataforma, chatbot, tótem, observatorio, panel, C.1) | ✅ Completo y probado (264 tests) |
| Documentación técnica y entregables (Plan Director, metodología, DPIA…) | ✅ Disponible |
| Documentación de justificación y plantillas de actas | ✅ Disponible |
| Instalación física de tótems / obra civil / autorizaciones Parque | 🏗️ Pendiente |
| Integraciones reales (DTI externo, RRSS, GA4) | ⬜ Dependen de accesos del Ayuntamiento |
| Pentest, formación, SAT, despliegue en producción | 🗂️ A ejecutar |

> Detalle accionable en el [checklist de justificación](operations/checklist-justificacion-subvencion.md) y el [correo de solicitud](operations/correo-solicitud-ayuntamiento.md).
