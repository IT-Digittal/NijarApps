# DPIA — Tratamiento de datos de movilidad del Observatorio Big Data

| | |
|---|---|
| **Expediente** | 18962/2025 |
| **Actuación** | A.3 — Social Listening y Big Data turístico |
| **Tipo** | Evaluación de Impacto en la Protección de Datos (art. 35 RGPD) — módulo de movilidad |
| **Responsable del tratamiento** | Ayuntamiento de Níjar |
| **Encargado del tratamiento** | IT DIGITTAL (administrador delegado durante el contrato) |
| **DPD/DPO** | Delegado de Protección de Datos del Ayuntamiento |

> Sección específica de movilidad del observatorio, requerida por el Plan de Mejora Continua (M4) y por la metodología del observatorio. Complementa la documentación de seguridad ENS Nivel Medio.

---

## 1. Necesidad y proporcionalidad

El observatorio estima flujos turísticos para redistribuir la demanda y reducir la saturación estacional (interés público del PSTD/PRTR). El tratamiento se limita a **agregados estadísticos**; no se persigue identificar ni perfilar a personas concretas. Se aplica **minimización**: solo se procesan los campos imprescindibles para el KPI.

## 2. Descripción del tratamiento

| Elemento | Detalle |
|----------|---------|
| **Fuentes de movilidad** | Conexiones a WiFi público (MAC), proximidad BLE de beacons, interacciones en tótem/web/app |
| **Datos de partida** | Identificador técnico de dispositivo (MAC), timestamp, ubicación aproximada, idioma |
| **Finalidad** | Estimación agregada de afluencia, estacionalidad y composición de visitantes |
| **Base jurídica** | Misión de interés público (art. 6.1.e RGPD); datos disueltos en agregados anónimos |
| **Categorías especiales** | Ninguna (no se tratan datos sensibles del art. 9) |

## 3. Medidas de minimización y anonimización

1. **Seudonimización en origen**: la MAC se transforma con **hash SHA-256** (con sal rotada) antes de cualquier persistencia. No se almacena la MAC en claro.
2. **No reidentificación**: no se cruza el hash con otras fuentes que permitan reidentificar; no se construyen trayectorias individuales nominativas.
3. **k-anonimato ≥ 5**: ningún agregado se publica si una celda agrupa a menos de 5 individuos (`src/nijar_dti/core/anonimizacion.py`). Las celdas suprimidas cuentan para el total pero no se desglosan.
4. **Agregación temporal y espacial**: los datos se exponen agregados por día y por zona, nunca a nivel de evento individual en los dashboards.
5. **Minimización de campos**: los identificadores técnicos no se propagan a las capas analíticas; solo viajan los agregados.

## 4. Conservación (retención)

| Dato | Retención | Justificación |
|------|-----------|---------------|
| Hash de dispositivo (eventos crudos) | ≤ 30 días | Tiempo necesario para deduplicar y agregar |
| Agregados anónimos (KPIs) | Indefinida | Ya no son datos personales |
| Logs operativos | 6 meses | Operación |
| Logs de auditoría/seguridad | 12 meses | ENS Nivel Medio |

Transcurrido el plazo, los eventos crudos se eliminan de forma irreversible.

## 5. Análisis de riesgos y mitigación

| Riesgo | Prob. | Impacto | Mitigación |
|--------|-------|---------|------------|
| Reidentificación por combinación de atributos | Baja | Alto | k-anonimato ≥ 5 + supresión de celdas + agregación |
| Persistencia accidental de MAC en claro | Baja | Alto | Hash en origen; revisión de código; sin campo MAC en el modelo |
| Acceso no autorizado a eventos crudos | Baja | Medio | RBAC, cifrado en reposo (AES-256), segmento IoT aislado |
| Inferencia de patrones individuales | Baja | Medio | Prohibición de trayectorias nominativas; solo agregados |
| Deriva del factor de expansión que distorsione cifras | Media | Bajo | Recalibración trimestral documentada |

Riesgo residual: **bajo y asumible** dadas las medidas técnicas y organizativas.

## 6. Derechos de los interesados

Dado que el resultado es anónimo y no se mantiene identificación, no es posible (ni necesario) el ejercicio individualizado sobre los agregados. Para la fase de eventos crudos seudonimizados se atienden los derechos a través del canal del DPD del Ayuntamiento. La información del tratamiento se publica en la política de privacidad municipal y se señaliza en los puntos de captación WiFi.

## 7. Gobernanza y revisión

- Revisión de esta DPIA **anual** o ante cualesquiera cambios sustanciales del tratamiento (nuevas fuentes, p. ej. telefonía móvil en C.1).
- Toda nueva fuente de movilidad exige actualizar esta sección antes de su puesta en producción.
- Las decisiones se documentan en acta y se trasladan al DPD.

## 8. Conclusión

El tratamiento de movilidad del observatorio es **proporcionado, minimizado y anonimizado**, con k-anonimato formalizado y retención acotada. Cumple RGPD/LOPDGDD y ENS Nivel Medio, y es defendible ante una auditoría de la AEPD.
