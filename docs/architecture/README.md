# Documentación de arquitectura

Documentos técnicos de referencia entregables al Ayuntamiento de Níjar como parte de los hitos de proyecto.

| Documento | Propósito | Hito |
|-----------|-----------|------|
| [`arquitectura-global.md`](arquitectura-global.md) | Descripción de las 3 capas, principios de diseño, flujos de datos, integraciones | H1 (preliminar) → H4 (definitivo) |
| [`decisiones-tecnicas.md`](decisiones-tecnicas.md) | ADRs — registro de decisiones arquitectónicas con contexto y alternativas | H1 |
| [`dependencias-terceros.md`](dependencias-terceros.md) | Inventario de COTS y librerías con licencias (PCAP Anexo XIII) | H1 → actualización mensual |

## Diagramas

Los diagramas formales de la Memoria Técnica (Anexos A3-1 a A3-5) se mantienen en formato fuente editable y se actualizan en cada hito:

- A3-1 — Arquitectura global de la Plataforma Smart City DTI
- A3-2 — Flujo de datos e integración global (diagrama de cajas)
- A3-3 — Mapa de integraciones y modelo semántico
- A3-4 — Cronograma Gantt con camino crítico e hitos
- A3-5 — Matriz de riesgos y medidas de mitigación

## Convención de actualización de ADRs

- **Nuevo ADR:** crear entrada al final de `decisiones-tecnicas.md` con número correlativo.
- **Cambio de decisión:** marcar el ADR original como **Reemplazado por ADR-XXX** y crear el nuevo.
- **Anulación:** marcar como **Anulado** con justificación; no eliminar nunca un ADR del histórico.
