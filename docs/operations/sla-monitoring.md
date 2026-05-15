# SLA, SLOs y monitoring del servicio

| | |
|---|---|
| **Expediente** | 18962/2025 |
| **Hito** | H4 — Puesta en producción + 48 meses C.1 |
| **Versión** | 1.0 |

---

## 1. SLA contractual

El pliego del Expediente 18962/2025 establece como **SLA mínimo el 99% de disponibilidad mensual**. La oferta de IT DIGITTAL incluye una mejora opcional al **99.5%**, aplicable si se acepta dicha mejora en el contrato definitivo.

### Cómputo

`Disponibilidad = (minutos del mes − minutos de downtime no programado) / minutos del mes`

Excluido del cómputo:
- Mantenimiento programado anunciado con ≥ 5 días.
- Causas externas no imputables (fuerza mayor, fallo de proveedor cloud confirmado, ataques DDoS si se han activado salvaguardas razonables).

### Penalizaciones por incumplimiento

| Disponibilidad mensual | Acción |
|------------------------|--------|
| ≥ 99% (o ≥ 99.5% si oferta de mejora) | Cumple — facturación íntegra |
| 98% – 99% | Reducción del 5% sobre la cuota mensual del C.1 |
| 95% – 98% | Reducción del 15% |
| < 95% | Reducción del 30% + plan de acción correctivo formal |

## 2. SLOs operativos por componente

Los SLOs (más exigentes que el SLA) protegen el cumplimiento del SLA mensual. Si un SLO se incumple, las alertas disparan al SOC antes de que se materialice un incumplimiento de SLA.

| Componente | Indicador (SLI) | Objetivo (SLO) | Alerta |
|------------|----------------|----------------|--------|
| API REST | `up` global | 99.9% mensual | API down >2 min |
| API REST | Tasa errores 5xx | < 1% | > 5% durante 5 min |
| API REST | Latencia p95 | < 500 ms | > 1 s durante 10 min |
| BBDD | `nijar_db_up` | 99.95% mensual | down >2 min |
| Smart Office | Sensores operativos | ≥ 90% del catálogo | < 50% durante 10 min |
| Tótems | Disponibilidad cada uno | 99% mensual cada uno | down >5 min |
| Chatbot | Resolución autónoma | ≥ 80% diario | < 70% durante 6 h |
| Big Data | Polling Social Listening | 1 ciclo / 15 min | sin datos en 30 min |

## 3. Error budget

Con SLA del 99% (mejora 99.5%), el error budget mensual es:

- **99%:** 7h 26m de downtime admisibles al mes.
- **99.5%:** 3h 43m de downtime admisibles al mes.

**Política:** si en cualquier mes se ha consumido > 50% del error budget durante la primera quincena, se congelan los despliegues no urgentes hasta el siguiente mes natural.

## 4. Métricas que se reportan en el informe mensual del C.1

| Métrica | Cálculo |
|---------|---------|
| Disponibilidad por componente | `1 - (downtime / total_minutos)` por cada SLI principal |
| Latencia p95 / p99 | Histograma `nijar_http_request_duration_seconds_bucket` |
| Tasa de error 5xx | `sum(rate(5xx)) / sum(rate(all))` |
| Interacciones del chatbot | total + por idioma + resolución autónoma |
| Interacciones tótems | total + sesiones únicas + duración media |
| Sentimiento medio | promedio mensual de Social Listening |
| Visitas web | GA4 sesiones del mes |
| Incidencias | críticas / altas / resueltas |
| Eventos de seguridad | volumen + clasificación |

El informe es generable desde la API mediante `GET /api/v1/dashboards/monthly-report?year=YYYY&month=MM` y se exporta a PDF/Excel para entrega oficial.

## 5. Escalado y on-call

Durante el C.1 IT DIGITTAL mantiene un SOC 24/7 con los siguientes niveles de escalado:

| Nivel | Personal | SLA respuesta |
|-------|----------|---------------|
| L1 | Operador SOC | 15 min para críticas, 1 h para altas |
| L2 | Especialista plataforma | 30 min tras escalado L1 |
| L3 | Arquitecto / DBA | 1 h tras escalado L2 |
| Coordinación con Ayuntamiento | Responsable de cuenta | Comunicación según matriz del runbook |

Las alertas críticas de Prometheus ruta directa a L1 vía PagerDuty/Slack/email.

## 6. Mejora continua

Cada trimestre se revisan los SLOs en función de:

- Tendencia de la latencia p95.
- Tasa de error y causas raíz recurrentes.
- Hallazgos del pentest anual.
- Evolución de la carga (sesiones, ingesta IoT, menciones).

Los ajustes se documentan con nueva versión de este documento y se acuerdan con el Ayuntamiento antes de aplicarse.
