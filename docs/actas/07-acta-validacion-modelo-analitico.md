# Acta de validación del modelo analítico

| | |
|---|---|
| **Expediente** | 18962/2025 — DTI Níjar |
| **Marco** | PRTR · NextGenerationEU · Componente 14 · ISO 42001 |
| **Tipo** | Validación del modelo analítico (sentimiento y predicción) |
| **Fecha** | [dd/mm/aaaa] |
| **Periodicidad** | Inicial (S6) y revalidación trimestral (C.1) |
| **Nº de acta** | VAL-[nn] |

## Participantes

| Nombre | Organización | Rol |
|--------|--------------|-----|
| [ ] | IT DIGITTAL | Especialista NLP/IA |
| [ ] | IT DIGITTAL | Director de Proyecto |
| [ ] | Ayuntamiento de Níjar | Responsable municipal |

## 1. Análisis de sentimiento (gold standard ≥ 100 menciones)

| Métrica | Umbral | Resultado | Cumple |
|---------|--------|-----------|--------|
| Precision | ≥ 80 % | [ ] | [ ] |
| Recall | ≥ 75 % | [ ] | [ ] |
| F1-Score | ≥ 77 % | [ ] | [ ] |
| Exactitud global | ≥ 80 % | [ ] | [ ] |

- Composición del gold standard: [ ] (ES con modismos almerienses, EN, DE, FR).

## 2. Modelos predictivos de afluencia

| Métrica | Umbral | Resultado | Cumple |
|---------|--------|-----------|--------|
| MAPE (holdout temporal) | ≤ 20 % | [ ] | [ ] |
| Detección de deriva (drift) | — | [ ] | [ ] |

> Procedimiento: `docs/big-data/metodologia-y-limitaciones.md`; endpoints
> `/prediccion/validacion` y `/prediccion/anomalias`.

## 3. Decisión

- [ ] Modelo **apto** para producción (supera todos los umbrales).
- [ ] **Recalibración** requerida (ampliación de corpus / reentrenamiento).

| Acción de recalibración | Responsable | Plazo |
|-------------------------|-------------|-------|
| [ ] | | |

## 4. Conformidad

- [ ] Resultados presentados al responsable municipal para su conformidad.

---

IT DIGITTAL — Especialista NLP/IA: ______________________ Fecha: __________

Ayuntamiento de Níjar — Responsable: ______________________ Fecha: __________
