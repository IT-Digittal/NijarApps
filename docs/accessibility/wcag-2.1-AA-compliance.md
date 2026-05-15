# Cumplimiento WCAG 2.1 nivel AA

| | |
|---|---|
| **Expediente** | 18962/2025 |
| **Versión del informe** | 1.0 (Hito 3 — autoevaluación) |
| **Estándar** | WCAG 2.1 nivel AA + UNE 139803:2012 + RD 1112/2018 |

Documento de declaración de accesibilidad de los frontales de la Plataforma DTI Níjar: **dashboard del Smart Office**, **interfaz de los tótems digitales** y **endpoints API consumidos por la app Vive Níjar**.

---

## 1. Frontales auditados

| Frontal | Ruta | Estándar mínimo |
|---------|------|------------------|
| Dashboard Smart Office | `/dashboard` | WCAG 2.1 AA |
| Tótem digital | `/totem` | WCAG 2.1 AA + criterios reforzados (texto ≥ 18 px, contraste ≥ 4.5:1, área táctil ≥ 44 px) |
| API REST | `/api/v1/*` | OpenAPI 3.1 + mensajes de error legibles |

## 2. Criterios verificados

### Principio 1 — Perceptible

| Criterio | Implementación |
|----------|-----------------|
| 1.1.1 Contenido no textual (A) | Todos los iconos llevan `aria-hidden="true"` o `aria-label`. Las imágenes de POIs no son críticas (la información va en el `<h3>` y `<p>`). |
| 1.3.1 Información y relaciones (A) | Estructura semántica con `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, `<footer>`. Tablas con `<caption>`, `<thead>`, `<th scope>`. |
| 1.3.2 Secuencia significativa (A) | Orden DOM coincide con el orden visual. Sin uso de `tabindex` positivos. |
| 1.3.3 Características sensoriales (A) | Las instrucciones nunca dependen únicamente de color, forma o ubicación. |
| 1.3.4 Orientación (AA) | Layout responsive funciona en horizontal y vertical (clases `md:` y `lg:` de Tailwind). |
| 1.3.5 Identificar el propósito (AA) | `autocomplete` en login (`username`, `current-password`); `inputmode` y `type` correctos. |
| 1.4.1 Uso del color (A) | Estados (operativo/offline) combinan color + texto + posición. |
| 1.4.2 Control de audio (A) | No hay audio en autoplay. |
| 1.4.3 Contraste mínimo (AA) | Texto sobre fondo blanco o gris claro: ratio ≥ 4.5:1. Texto sobre `bg-slate-800`: ≥ 7:1. Botón ámbar sobre slate-900: 8.1:1. |
| 1.4.4 Redimensionar texto (AA) | Hasta 200% sin pérdida de funcionalidad. Botón "A+" en el tótem amplía a 22 px base. |
| 1.4.5 Imágenes de texto (AA) | No se usan imágenes con texto. |
| 1.4.10 Reflujo (AA) | Layout reflow a 320 CSS px. Tabla de sensores con `overflow-x-auto`. |
| 1.4.11 Contraste no textual (AA) | Bordes de inputs ≥ 3:1, indicador de foco con outline 4 px sólido. |
| 1.4.12 Espaciado de texto (AA) | `line-height: 1.6` (≥ 1.5), `letter-spacing` por defecto, párrafos con `margin-bottom`. |
| 1.4.13 Contenido al pasar / enfocar (AA) | Sin tooltips persistentes invasivos. Modales cierran con Esc y botón explícito. |

### Principio 2 — Operable

| Criterio | Implementación |
|----------|-----------------|
| 2.1.1 Teclado (A) | Toda la funcionalidad accesible con teclado. Tarjetas de POI con `tabindex="0"` y manejo de Enter/Espacio. |
| 2.1.2 Sin trampas de teclado (A) | El modal del POI cierra con Esc y devuelve el foco al elemento que lo abrió. |
| 2.1.4 Atajos de teclado (A) | No se definen atajos que entren en conflicto con el navegador. |
| 2.4.1 Saltar bloques (A) | Skip link "Saltar al contenido principal" en dashboard y tótem. |
| 2.4.2 Título de página (A) | `<title>` descriptivo en cada página. |
| 2.4.3 Orden del foco (A) | Orden de tabulación lógico: header → nav → main → footer. |
| 2.4.4 Propósito de los enlaces (A) | Texto del enlace describe el destino. No hay "haga clic aquí". |
| 2.4.5 Múltiples vías (AA) | Navegación principal + categorías + búsqueda en chatbot. |
| 2.4.6 Encabezados y etiquetas (AA) | `<label>` asociado a cada `<input>`; `<h1>` … `<h3>` jerarquizados. |
| 2.4.7 Foco visible (AA) | Indicador `outline: 4px solid #f59e0b; outline-offset: 3px`. |
| 2.5.1 Gestos del puntero (A) | Sin gestos multi-touch obligatorios. |
| 2.5.2 Cancelación del puntero (A) | Acción se ejecuta en `mouseup`/`click`, no en `mousedown`. |
| 2.5.3 Etiqueta en el nombre (A) | `aria-label` coincide con el texto visible. |
| 2.5.4 Activación por movimiento (A) | Sin acciones por agitar el dispositivo. |
| 2.5.5 Tamaño del objetivo (AAA recomendado, obligatorio en tótem) | Botones del tótem ≥ 44 × 44 px (`min-h-[44px] min-w-[44px]`). |

### Principio 3 — Comprensible

| Criterio | Implementación |
|----------|-----------------|
| 3.1.1 Idioma de la página (A) | `<html lang="es">`. El tótem actualiza `lang` y `data-language` al cambiar idioma. |
| 3.1.2 Idioma de las partes (AA) | Cuando se muestra contenido en un idioma distinto, se marca con `lang="..."` (gestionado dinámicamente al cambiar de idioma global). |
| 3.2.1 Al recibir el foco (A) | Cambiar el foco no provoca cambios de contexto. |
| 3.2.2 Al recibir entrada (A) | El cambio de idioma requiere un click explícito (no automático al perder foco). |
| 3.2.3 Navegación coherente (AA) | El menú principal se mantiene en todas las páginas. |
| 3.2.4 Identificación coherente (AA) | Iconos y etiquetas se usan de la misma forma en todo el dashboard y tótem. |
| 3.3.1 Identificación de errores (A) | Los errores de validación se muestran en un `<div role="alert">` cercano al campo. |
| 3.3.2 Etiquetas o instrucciones (A) | Cada input tiene `<label>`. Los placeholders no sustituyen al label. |
| 3.3.3 Sugerencias ante error (AA) | "Credenciales inválidas" y mensaje específico de validación de Pydantic mostrado al usuario. |
| 3.3.4 Prevención de errores (AA) | Acciones destructivas confirmables; `DELETE` requiere confirmación en cliente y RBAC en servidor. |

### Principio 4 — Robusto

| Criterio | Implementación |
|----------|-----------------|
| 4.1.2 Nombre, función, valor (A) | `aria-pressed`, `aria-current`, `aria-live`, `aria-busy`, `aria-label`, `aria-labelledby` aplicados. |
| 4.1.3 Mensajes de estado (AA) | Banner global de conexión usa `role="status"` y `aria-live="polite"`. Mensajes del chatbot usan `<output aria-live="polite">`. |

## 3. Otros aspectos reforzados

- **Reducir movimiento (1.4.10 + 2.3.3 nivel AAA recomendado):** `@media (prefers-reduced-motion: reduce)` desactiva animaciones.
- **Modo alto contraste manual:** botón `Alto contraste` en el tótem activa una paleta blanco/negro/amarillo conforme al nivel AAA.
- **Texto ampliable manual:** botón `A+` aumenta `font-size` global a 22 px.
- **Inactividad:** el tótem detecta 60 s sin interacción y vuelve al estado inicial sin pérdida de contenido del usuario.
- **Bucle magnético:** los tótems físicos incorporan bucle magnético para personas con prótesis auditiva (compromiso técnico de Níjar).
- **Lectura fácil:** las FAQs base están redactadas con frases cortas, voz activa, evitando tecnicismos. Se ampliará con versión "lectura fácil" certificada en el Hito 4.

## 4. Validación automatizada en CI

El pipeline de CI ejecuta `axe-core` (vía `@axe-core/playwright` o `pa11y`) sobre las dos rutas estáticas (`/dashboard` y `/totem`) y bloquea el merge si aparecen issues críticos o serios. Los issues moderados se reportan pero no bloquean.

## 5. Excepciones documentadas

Ninguna a la fecha de este informe. Toda excepción futura se documenta aquí con justificación, plan de mitigación y revisión trimestral.

## 6. Contacto para cuestiones de accesibilidad

Conforme al RD 1112/2018, los usuarios pueden comunicar barreras de accesibilidad o solicitar información en formato accesible al canal:

- Correo electrónico del Ayuntamiento de Níjar (a definir antes del SAT).
- Buzón de quejas y sugerencias municipal.
- Llamada a la oficina de turismo.

El equipo técnico responde en un plazo máximo de **20 días hábiles** y la respuesta queda registrada en el sistema de gestión de incidencias.
