# Informe de estado del proyecto por hitos

| | |
|---|---|
| **Proyecto** | Implantación de soluciones de transformación digital del sector turístico de Níjar |
| **Expediente** | 18962/2025 |
| **Marco** | PRTR · NextGenerationEU · Componente 14 |
| **De** | IT DIGITTAL |
| **Para** | Ayuntamiento de Níjar |
| **Fecha** | 14/08/2026 |

## Introducción

El presente documento resume el **estado actual de cada hito** del contrato, con su **porcentaje de avance real**, lo que **falta para completarlo** y la **colaboración necesaria por parte del Ayuntamiento**. A fecha de hoy, los **dos tótems interactivos ya están instalados** y en funcionamiento, y la plataforma está **integrada y operativa en producción**, con sus **conectores a las fuentes externas** (redes sociales, analítica web y plataforma DTI) **construidos y verificados**. El Ayuntamiento ya ha facilitado el **acceso a Facebook e Instagram**, por lo que la **activación con datos reales** del Social Listening y de Google Analytics se encuentra en su **fase final de configuración**. Todas las piezas del proyecto (plataforma, chatbot, observatorio de datos, panel de control, tótems y herramientas de mantenimiento) están **construidas, desplegadas en producción y operativas**. Los puntos pendientes se concentran en la **activación con datos reales de las fuentes externas** y en los **actos formales de validación** (auditoría de seguridad, formación y prueba de aceptación) hasta la **firma del acta de recepción**.

## Resumen de avance

| Hito | Descripción | Avance | Estado |
|------|-------------|:------:|--------|
| **H1** | Planificación y diseños | **100 %** | Completado |
| **H2** | Implementación intermedia | **100 %** | Completado (tótems instalados y en marcha) |
| **H3** | Integración y pruebas | **90 %** | Integración finalizada; pendientes actos de validación |
| **H4** | Puesta en producción y aceptación (SAT) | **85 %** | En producción y operativo; pendiente la aceptación (SAT) |
| **C.1** | Mantenimiento y hosting (48 meses) | **Listo para iniciar** | Comienza tras la recepción |
| | **Avance global (actuaciones subvencionadas)** | **≈ 93 %** | |

---

## H1 — Planificación y diseños · 100 %

**Hecho:** plan de proyecto, análisis y diagnóstico inicial, diseño de la arquitectura e integraciones, diseño visual de los tótems (aprobado) y entrega del Plan de Transformación Digital. Actas de arranque (kick-off) y de aprobación de diseños (Go/No-Go) formalizadas.

**Falta para cerrarlo:** nada. Hito completado.

## H2 — Implementación intermedia · 100 %

**Hecho:** desarrollo de la plataforma DTI y del panel de control, **chatbot multilingüe** (105 preguntas frecuentes en 4 idiomas) con demostración funcional, observatorio de Big Data y entrega del Plan de Transformación Digital definitivo. **Los 2 tótems interactivos están físicamente instalados** (obra civil, acometidas eléctricas y de datos y puesta en marcha completadas) y sincronizados con el CMS central.

**Falta para cerrarlo:** nada. Hito completado; pendiente únicamente su reflejo en el acta de recepción global (H4).

## H3 — Integración y pruebas · 90 %

**Hecho:** pruebas funcionales y de accesibilidad (WCAG 2.1 AA), ajuste de los modelos de datos y de los cuadros de mando de Big Data, e **integración con los sistemas municipales y la plataforma DTI existente**. Los **conectores de Social Listening** (Facebook, Instagram, X) **y de Google Analytics 4 están construidos y verificados**, con sus procedimientos de **activación, verificación y renovación de credenciales** ya preparados. El Ayuntamiento ha facilitado el **acceso a Facebook e Instagram**.

**Falta para cerrarlo:**
- **Activación con datos reales de las fuentes externas**: introducir las credenciales y ejecutar la verificación — redes sociales (acceso a Facebook/Instagram ya facilitado; pendiente el token de la app de Meta) y **Google Analytics 4** (cuenta de servicio + Property ID del destino).
- **Auditoría de seguridad (pentest)**: ejecución y entrega del informe.
- **Formación al personal (≥ 10 h)** y su acta.
- Simulacro de copia de seguridad y restauración (acta de resultado).

## H4 — Puesta en producción y aceptación (SAT) · 85 %

**Hecho:** **plataforma desplegada, integrada y operativa en el entorno de producción** (infraestructura cloud en la Unión Europea), **tótems en servicio**, telemetría en funcionamiento, guion de la prueba de aceptación y documentación técnica.

**Falta para cerrarlo:**
- **Prueba de aceptación (SAT)** presencial y firma del **acta de recepción**.
- Consolidación de la documentación final «as-built» e inicio formal del soporte.

## C.1 — Mantenimiento y hosting (48 meses) · Listo para iniciar

El **hosting de producción ya está operativo** (infraestructura cloud en la UE) y los tótems están conectados y monitorizados. Las herramientas de mantenimiento están disponibles y en uso: **informe mensual de servicio**, control de **niveles de servicio (ANS)**, gestión de incidencias, copias de seguridad y monitorización. Este periodo comienza formalmente tras la recepción (H4).

---

## Qué necesitamos del Ayuntamiento para finalizar

Con los tótems instalados y las integraciones construidas, la colaboración pendiente se limita a **activar las fuentes externas** y a **cerrar los actos formales de validación**:

| # | Necesidad | Afecta a |
|---|-----------|----------|
| 1 | **Credenciales de las fuentes externas** para la activación: **token de la app de Meta** (el acceso a Facebook/Instagram ya está facilitado) y **cuenta de servicio + Property ID de Google Analytics 4** | H3 |
| 2 | **Autorización y ventana para la auditoría de seguridad (pentest)** sobre los servicios en producción | H3 |
| 3 | **Designación de asistentes y fecha** para la **formación al personal (≥ 10 h)** | H3 |
| 4 | **Fecha para la prueba de aceptación (SAT)** presencial y firma del **acta de recepción** | H4 |
| 5 | Confirmación de **dominio(s) definitivo(s)** del Ayuntamiento y, si procede, integración con el acceso interno municipal (SSO) | H4 |
| 6 | **Contacto del Delegado de Protección de Datos** y validación de los textos legales/privacidad publicados | H3–H4 |

> Nota: el **alojamiento, el despliegue en producción, la instalación de los tótems y los conectores de integración ya están resueltos** por IT DIGITTAL; la activación de las fuentes externas es un **último paso de configuración** (introducir credenciales y verificar), con procedimientos y herramientas ya preparados por nuestra parte.

> Por seguridad, cualquier credencial o token adicional **no debe enviarse por correo en texto plano**; facilitamos un canal seguro.

## Próximos pasos propuestos

1. **Facilitar las credenciales** de Meta (token) y de Google Analytics 4 (cuenta de servicio + Property ID) para **activar los datos reales** de redes sociales y analítica (cierre de la integración del H3).
2. Acordar **ventana para el pentest** y ejecutar la auditoría (cierre técnico del H3).
3. Fijar **fecha de formación** (≥ 10 h) y levantar su acta.
4. Acordar **fecha del SAT**, realizar la prueba de aceptación y **firmar el acta de recepción** (cierre del H4).
5. Confirmar el/los **dominio(s)** definitivos del Ayuntamiento para consolidar la publicación de los servicios.

Con la recepción firmada, arranca formalmente el periodo de **mantenimiento y hosting (C.1, 48 meses)**, ya operativo en la práctica.

Quedamos a su disposición para una breve reunión de coordinación y agradecemos de antemano su colaboración.

**IT DIGITTAL — Dirección de Proyecto**
Exp. 18962/2025 · [nombre] · [email] · [teléfono]
