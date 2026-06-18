# Plan de Mejora Continua del Observatorio — DTI Níjar

| | |
|---|---|
| **Expediente** | 18962/2025 |
| **Actuación** | A.3 — Social Listening y Big Data turístico |
| **Naturaleza** | Entregable del Pliego (*«Plan de mejora continua: recomendar cómo el Ayuntamiento podría en el futuro ampliar o afinar este sistema»*) |
| **Horizontes** | Pre-SAT (antes de certificación) · C.1 (48 meses de mantenimiento) |

---

## 1. Encaje contractual

El PPT exige que el observatorio sea ampliable y que se recomiende su evolución futura. Este plan formaliza esa recomendación: un catálogo de mejoras priorizadas por impacto y esfuerzo, con su horizonte de ejecución, distinguiendo lo que refuerza la valoración técnica del SAT de lo que corresponde al Plan de Mejora Continua del C.1.

## 2. Estado actual del observatorio

Implementado y operativo:

- Social Listening multi-plataforma (X, Facebook, Instagram) con pipeline NLP (idioma, sentimiento con negación, temas, entidades FIWARE).
- KPIs: sentimiento (serie temporal), share of voice, top temas.
- **NPS proxy** (`GET /data/social/kpis/nps`) y **composición lingüística de visitantes** (`GET /data/social/kpis/composicion-linguistica`).
- **Backfill de contexto histórico** (INE Frontur/Egatur/EOH, Junta de Andalucía, AENA) con modelo semántico propio y **factor de expansión** calibrable.
- **k-anonimato ≥ 5** aplicado a los agregados; metodología y limitaciones documentadas.
- Conector GA4 para eficacia digital.

## 3. Límites estructurales reconocidos

1. **Sin señal directa de origen del visitante** por red móvil (lo que vende la telefonía tipo Nommon). Se aproxima por convergencia lingüística, declarado como aproximación.
2. **Histórico propio corto**: el sistema arranca en el mes 1. Se cubre con backfill de fuentes públicas oficiales (histórico largo de contexto).
3. **Sesgo de muestra** de las señales propias (WiFi/beacons): mitigado con factor de expansión y comunicación honesta.

## 4. Benchmarking — telefonía móvil (tipo Nommon)

| Dimensión | Telefonía móvil (Nommon) | Observatorio DTI Níjar |
|-----------|--------------------------|------------------------|
| Origen del visitante | Directo (red móvil) | Aproximado (convergencia lingüística) |
| Histórico | Años | Backfill público + serie propia creciente |
| Coste | Servicio recurrente de pago | Incluido, sin coste recurrente |
| Soberanía del dato | Proveedor externo | Municipal (datos abiertos + señales propias) |
| RGPD | Agregados de operadora | Anonimización propia + k-anonimato |

**Conclusión**: la telefonía móvil es una opción de *enriquecimiento* para C.1, no una necesidad contractual. Puede incorporarse sin rediseño (nuevo conector + entidad en el modelo semántico).

## 5. Catálogo de mejoras priorizadas

| ID | Mejora | Impacto | Esfuerzo | Horizonte | Estado |
|----|--------|---------|----------|-----------|--------|
| **M1** | Composición lingüística multiseñal | Alto | Medio | Pre-SAT | ✅ Implementada (KPI + API) |
| **M2** | Backfill de fuentes públicas (INE/Junta/AENA) | Alto | Medio | Pre-SAT | ✅ Implementada (conector + ingesta) |
| **M3** | Validación predictiva con MAPE / holdout | Medio | Medio | Pre-SAT | ◑ Documentada; falta ejecutar backtesting sobre modelo real |
| **M4** | k-anonimato ≥ 5 + DPIA reforzada | Alto | Bajo | Pre-SAT | ◑ Regla implementada en código; falta sección DPIA |
| **M5** | Índice NPS proxy | Medio | Medio | Pre-SAT | ✅ Implementada (KPI + API) |
| **M6** | Metodología y limitaciones documentada | Alto | Bajo | Pre-SAT | ✅ Implementada (documento) |
| **M7** | Conectores de reviews (TripAdvisor, Google, HolidayCheck) | Medio | Medio | C.1 | ☐ Pendiente (requiere claves API) |
| **M8** | Visualizaciones de flujo (heatmap horario, flow map, Sankey) | Medio | Alto | C.1 | ☐ Pendiente (requiere datos WiFi/beacons reales) |

Leyenda: ✅ completa · ◑ parcial · ☐ pendiente

## 6. Hoja de ruta

### 6.1 Pre-SAT (refuerzan la valoración técnica B.3 del PCAP)

- **M3**: ejecutar el backtesting MAPE en cuanto exista serie propia suficiente; documentar resultado y umbral de recalibración.
- **M4**: añadir a la DPIA la sección específica de movilidad (k-anonimato, minimización, retención).
- **M1, M2, M5, M6**: ya entregadas; verificar en el SAT con datos cargados.

### 6.2 C.1 (Plan de Mejora Continua, 48 meses)

- **M7**: incorporar reviews de portales de viaje (HolidayCheck es clave por el peso del turismo alemán en Cabo de Gata).
- **M8**: visualizaciones de flujo cuando haya volumen de WiFi/beacons.
- **Opcional**: enriquecimiento con telefonía móvil tipo Nommon si el Ayuntamiento lo decide.

## 7. Gobernanza de la mejora continua

- Revisión trimestral del observatorio (revalidación de modelos, recalibración del factor de expansión, detección de deriva) documentada en acta.
- Las nuevas mejoras se incorporan a este catálogo con el mismo nivel de análisis (impacto/esfuerzo/horizonte).
- El responsable municipal aprueba la priorización en el comité de seguimiento.
