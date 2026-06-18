# Metodología y Limitaciones del Observatorio Big Data — DTI Níjar

| | |
|---|---|
| **Expediente** | 18962/2025 |
| **Actuación** | A.3 — Social Listening y Big Data turístico |
| **Documento** | Anexo metodológico al Catálogo de KPIs |
| **Objeto** | Hacer cada cifra del observatorio interpretable, trazable y defendible ante auditoría PRTR / AEPD |

> Este documento responde a la exigencia del PPT (A.3): *«Se deberá asegurar que todos los indicadores y análisis sean verificables y trazables, documentando la metodología de cálculo de cada KPI para auditoría»*.

---

## 1. Taxonomía de fuentes

El observatorio combina fuentes de naturaleza distinta. Mezclarlas sin distinguir su alcance produce conclusiones erróneas, por lo que cada KPI declara de qué tipo de fuente procede.

| Tipo | Definición | Fuentes en Níjar | Uso |
|------|------------|------------------|-----|
| **Censal / oficial** | Cubre (cuasi) la totalidad de la población o es estadística oficial representativa | INE EOH (pernoctaciones), INE Frontur/Egatur, Junta de Andalucía, AENA | Referencia de calibración y contexto |
| **Muestral propia** | Capta solo una fracción de los visitantes; requiere factor de expansión | WiFi público anonimizado, beacons BLE, interacciones tótem/chatbot | Estimación de volumen y comportamiento |
| **Contextual / cualitativa** | No mide volumen sino percepción o conversación | Menciones RRSS (X/Facebook/Instagram), reseñas, encuestas municipales | Sentimiento, NPS proxy, temas |

---

## 2. Factor de expansión

Las señales muestrales propias (p. ej. conexiones WiFi públicas) solo observan una parte de los visitantes. Para estimar el total se aplica un **factor de expansión** calibrado contra una referencia oficial.

### 2.1 Procedimiento

1. Se toma la referencia censal del periodo: **pernoctaciones INE EOH** (provincia de Almería).
2. Se convierte en visitantes mediante la **estancia media** (referencia litoral almeriense: 3,5 noches):
   `visitantes_oficiales = pernoctaciones / estancia_media`
3. El factor es la razón entre esa estimación oficial y la muestra propia:
   `factor = visitantes_oficiales / muestra_propia`
4. La cobertura de la señal es `1 / factor`.

Implementado en `src/nijar_dti/connectors/contexto/expansion.py` y expuesto en `GET /api/v1/data/contexto/factor-expansion`.

### 2.2 Valor preliminar y calibración

Mientras no haya datos propios suficientes se usa un **factor preliminar de 6,7** (cobertura ≈ 15 % del WiFi público), claramente marcado como `es_preliminar=true` en la API y en el dashboard. La calibración se **revisa trimestralmente** contra la EOH actualizada; una desviación significativa del factor entre trimestres se trata como deriva y obliga a recalibrar.

---

## 3. Intervalos de confianza

Todo porcentaje agregado derivado de muestra se publica con su **banda de confianza al 95 %** (aproximación de Wald):

`IC₉₅ = ±1,96 · √( p·(1−p) / n ) · 100  (puntos porcentuales)`

Implementado en `analitica_service.banda_confianza_pp`. El dashboard muestra la banda junto al KPI para que el lector distinga una diferencia real de ruido muestral. A menor muestra, mayor banda: los KPIs con muestra pequeña se comunican como orientativos.

---

## 4. Validación de modelos

| Modelo | Métricas | Umbral | Procedimiento |
|--------|----------|--------|---------------|
| **Análisis de sentimiento** | Precision / Recall / F1 / Exactitud | ≥ 80 % / ≥ 75 % / ≥ 77 % / ≥ 80 % | Gold standard ≥ 100 menciones reales (ES con modismos almerienses, EN, DE, FR) clasificadas por evaluadores independientes |
| **Modelos predictivos de flujo** | **MAPE** (Mean Absolute Percentage Error) con *holdout* temporal | MAPE ≤ 20 % (objetivo); recalibración si se supera | Se reserva el último tramo temporal como test; se compara predicción vs real; se vigila deriva |

> El PCAP evalúa explícitamente la *«validación del modelo de análisis incluyendo métricas de precisión, recall o equivalentes»*. Para predicción, el equivalente formal es **MAPE con holdout**, ya implementado: el modelo estacional de afluencia y su validación se exponen en `/api/v1/prediccion/{afluencia,validacion,anomalias}` (`connectors/analytics/forecasting.py`). El MAPE se calcula sobre el tramo de test reservado y solo sobre días con afluencia real > 0. Con poca serie propia se reporta como orientativo hasta acumular histórico.

**Criterio de aceptación**: ninguna versión de un modelo se despliega en producción si no supera sus umbrales sobre el conjunto de validación. La primera validación tras la puesta en marcha se presenta al responsable municipal para conformidad.

---

## 5. Privacidad: k-anonimato y minimización (RGPD / DNSH)

- **k-anonimato ≥ 5**: ningún agregado derivado de señales individuales (composición lingüística, flujos) se publica si una celda agrupa a menos de 5 individuos. Implementado en `src/nijar_dti/core/anonimizacion.py` y aplicado en los KPIs analíticos. Las celdas suprimidas siguen contando para el total (coherencia del 100 %) pero no se desglosan.
- **Anonimización en origen**: identificadores de movilidad (MAC WiFi) tratados con hash SHA-256; sin reidentificación.
- **Minimización**: solo se almacenan los campos necesarios para el KPI; los datos personales no se persisten en los agregados.
- **Retención diferenciada**: 6 meses para logs operativos, 12 meses para auditoría/seguridad (ENS).

La sección de movilidad debe incorporarse a la DPIA existente (ver Plan de Mejora Continua, M4).

---

## 6. Limitaciones reconocidas por fuente

| Fuente | Limitación | Mitigación |
|--------|------------|------------|
| WiFi público / beacons | Sesgo de muestra: no todos se conectan (turismo premium con datos en roaming queda infrarrepresentado) | Factor de expansión calibrado + comunicación honesta del sesgo |
| Menciones RRSS | Sesgo de plataforma y de quién publica; no representa al visitante silencioso | Se usa para percepción, no para volumen; multi-plataforma |
| INE Frontur/Egatur | Ámbito autonómico/provincial, no municipal | Se usa como contexto poblacional, no como dato de Níjar |
| AENA Almería | El aeropuerto no capta al visitante que llega por carretera | Indicador complementario, no único |
| Encuestas municipales | Autoselección de respondientes | Tamaño muestral declarado; no se extrapola sin cautela |

---

## 7. Plantilla de ficha de KPI

Cada KPI del catálogo se documenta con:

```
Nombre del KPI:
Definición:
Fórmula de cálculo exacta:
Fuente(s) y tipo (censal / muestral / contextual):
Periodicidad:
Factor de expansión aplicado (sí/no, valor, calibración):
Intervalo de confianza:
Regla de privacidad (k-anonimato):
Limitaciones conocidas:
Procedimiento de verificación / auditoría:
Responsable y frecuencia de revalidación:
```

---

## 8. Trazabilidad de extremo a extremo

El sistema registra el linaje completo de cada dato analítico: desde la observación original (URL/autor/timestamp o señal de origen) hasta el KPI agregado, pasando por cada transformación. Esto permite reconstruir cualquier cifra del dashboard ante una auditoría del PRTR o de la Junta de Andalucía.
