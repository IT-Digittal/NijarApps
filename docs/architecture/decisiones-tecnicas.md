# Decisiones técnicas (ADRs) — Plataforma DTI Níjar

Registro de las decisiones arquitectónicas relevantes del proyecto. Cada ADR (Architecture Decision Record) documenta una decisión, su contexto, las alternativas consideradas y las consecuencias asumidas.

---

## ADR-001 · Stack backend: Python 3.11 + FastAPI + SQLAlchemy 2.0

**Estado:** Aceptado
**Fecha:** Hito 1 (Semana 1)

**Contexto.** Necesitamos un framework web para implementar las APIs REST/JSON de la plataforma DTI con OpenAPI 3.1, soporte async y tipado estricto. El proyecto requiere alta productividad en 8 semanas y mantenibilidad durante 48 meses de mantenimiento.

**Decisión.** Adoptar **Python 3.11+ con FastAPI**, **SQLAlchemy 2.0 async** y **Pydantic v2**.

**Alternativas consideradas.**

| Alternativa | Pros | Contras |
|-------------|------|---------|
| Node.js + NestJS | Ecosistema TypeScript, buen rendimiento I/O | Menos talento NLP/Big Data integrado; ORMs menos maduros |
| Java + Spring Boot | Madurez empresarial, buen rendimiento | Mayor verbosidad; menor productividad para el plazo de 8 semanas |
| Go + Gin/Echo | Excelente rendimiento, despliegue ligero | Ecosistema NLP/IA muy limitado |

**Consecuencias.**
- ✅ Generación automática de la especificación OpenAPI desde el código.
- ✅ Pydantic v2 garantiza validación estricta de payloads y modelos serializables a JSON Schema.
- ✅ Stack único Python para API + NLP (Rasa) + Big Data + análisis de sentimiento.
- ⚠️ Necesidad de configurar correctamente las pools async para PostgreSQL (asyncpg).

---

## ADR-002 · Base de datos: PostgreSQL 16 + PostGIS 3

**Estado:** Aceptado
**Fecha:** Hito 1 (Semana 1)

**Contexto.** La plataforma requiere consultas geoespaciales (mapas, mapas de calor, alertas geolocalizadas), almacenamiento relacional (entidades FIWARE) y volúmenes elevados de telemetría IoT (observaciones de sensores).

**Decisión.** Usar **PostgreSQL 16** con la extensión **PostGIS 3.4** para datos geoespaciales y la extensión **pg_trgm** para búsqueda textual eficiente.

**Alternativas consideradas.**

| Alternativa | Pros | Contras |
|-------------|------|---------|
| MongoDB | Flexible para documentos JSON | Sin soporte SQL transaccional robusto; geoespacial menos potente |
| MySQL + MyISAM/InnoDB | Muy extendido | Soporte geoespacial limitado |
| ScyllaDB / Cassandra | Excelente para series temporales | Operación compleja para el tamaño del despliegue |

**Consecuencias.**
- ✅ Consultas espaciales nativas (`ST_DWithin`, mapas de calor, geocercas).
- ✅ Soporte ACID completo, transacciones, integridad referencial.
- ✅ Misma BBDD para todo (relacional + geo + JSON), simplifica operación y backup.
- ⚠️ Para volúmenes muy elevados de observaciones IoT, se contempla activar **TimescaleDB** o particionado nativo en producción si se observa degradación.

---

## ADR-003 · Modelo semántico: FIWARE Smart Data Models

**Estado:** Aceptado
**Fecha:** Hito 1 (Semana 1)

**Contexto.** La norma UNE 178104 y el PPT exigen un modelo semántico común para la ciudad inteligente que garantice interoperabilidad presente y futura.

**Decisión.** Adoptar **FIWARE Smart Data Models** como base del modelo semántico:

- `RecursoTuristico` ← `PointOfInterest`, `TouristAttraction`
- `EventoTuristico` ← `Event`
- `Sensor` ← `Device`
- `Observacion` ← `AirQualityObserved`, `WeatherObserved`
- `Servicio`, `Visita`, `Opinion` → extensiones propias documentadas

URN format NGSI-LD: `urn:ngsi-ld:<EntityType>:nijar:<slug>`.

**Alternativas consideradas.**
- Schema.org (orientación más SEO/web, menos completo para IoT).
- Modelo propio ad-hoc (rechazado por el riesgo de bloqueo tecnológico).

**Consecuencias.**
- ✅ Compatibilidad inmediata con plataformas Smart City interoperables.
- ✅ Reutilización de vocabulario maduro y documentado.
- ✅ Facilita la apertura futura de datos abiertos (CC BY 4.0).
- ⚠️ Necesidad de mapear cuidadosamente las extensiones propias para evitar divergencias semánticas.

---

## ADR-004 · Mensajería IoT: MQTT + Redis pub/sub

**Estado:** Aceptado
**Fecha:** Hito 1 (Semana 2)

**Contexto.** La plataforma debe ingerir telemetría de sensores IoT con cadencia de 60 s y propagar eventos en tiempo real a otros componentes (alertas Smart Office, banderas de playa, avisos de aforo en app).

**Decisión.**
- **MQTT** como protocolo estándar de ingesta IoT (broker Eclipse Mosquitto compatible con EMQX en producción).
- **Redis pub/sub** como bus de eventos interno entre servicios de la plataforma.
- Se ofrece también un endpoint **HTTP `/api/v1/data/iot/ingest`** como vía alternativa para sistemas que no puedan publicar por MQTT.

**Consecuencias.**
- ✅ Estándar de facto en IoT, soportado por la mayoría de sensores comerciales.
- ✅ Topics MQTT estructurados (`nijar/sensors/<sensor_id>/observation`) facilitan filtrado y autorización.
- ✅ Redis pub/sub es ligero y suficiente para los volúmenes esperados (no se necesita Kafka).
- ⚠️ MQTT requiere TLS y autenticación por certificado en producción (cumplimiento ENS).

---

## ADR-005 · Hosting: cloud en UE con titularidad municipal

**Estado:** Aceptado
**Fecha:** Hito 1 (Semana 2)

**Contexto.** La actuación C.1 obliga a 48 meses de hosting con SLA mensual del 99 % (99,5 % si se ofertó la mejora del Criterio 1) y RGPD plena.

**Decisión.**
- **Cloud público con datacenter en la Unión Europea** (RGPD) — proveedor a confirmar entre AWS Frankfurt/Madrid, Google Cloud Madrid o Azure Spain Central según evaluación coste/SLA.
- **Credenciales de administración propiedad del Ayuntamiento.** IT DIGITTAL opera como administrador delegado durante el contrato, pero el municipio puede revocar accesos en cualquier momento.
- **Escalado vertical y horizontal sin interrupción** para absorber picos estacionales (junio–septiembre).

**Consecuencias.**
- ✅ Soberanía del dato garantizada.
- ✅ Continuidad del servicio independiente del adjudicatario (transición ordenada al fin del contrato).
- ✅ Escalado preparado para verticales futuros sin migración.
- ⚠️ Coste OPEX recurrente que debe contemplarse en el presupuesto C.1.

---

## ADR-006 · Autenticación: OAuth2 + JWT con RBAC

**Estado:** Aceptado
**Fecha:** Hito 1 (Semana 2)

**Contexto.** El ENS Medio exige control de accesos con privilegio mínimo, autenticación robusta y trazabilidad. El PPT define 5 perfiles RBAC.

**Decisión.**
- **OAuth2 Bearer + JWT** firmados con HS256.
- **Access tokens** de vida corta (60 min por defecto) y **refresh tokens** de vida larga (7 días).
- **5 roles RBAC**: `administrador_tic`, `gestor_contenidos`, `analista_datos`, `operador_smart_office`, `auditor`.
- **2FA obligatorio** para administradores TIC.
- **Integración con SSO/AD municipal** si está disponible.
- **Hashing bcrypt** con cost factor 12 para contraseñas.

**Consecuencias.**
- ✅ Cumplimiento ENS Medio.
- ✅ Tokens con scopes permiten autorización granular sin sesiones server-side.
- ✅ Compatibilidad con sistemas externos (web, app, integraciones futuras).

---

## ADR-007 · Chatbot: Rasa Open Source

**Estado:** Provisional (a confirmar en Hito 2)
**Fecha:** Hito 1 (Semana 2)

**Contexto.** El PPT exige un chatbot multilingüe (ES/EN/DE/FR) con NLP avanzado, control de alucinaciones y trazabilidad de fuentes. La portabilidad e interoperabilidad son obligaciones contractuales.

**Decisión provisional.** Usar **Rasa Open Source** como motor base por:
- Open source con licencia permisiva (no bloqueo tecnológico).
- Soporte nativo multilingüe.
- Posibilidad de despliegue on-cloud bajo control municipal.
- Modelo de intents/entities/stories adecuado al volumen previsto (≥100 FAQs iniciales).

**Alternativas consideradas.**

| Alternativa | Pros | Contras |
|-------------|------|---------|
| Dialogflow CX | Buena UX de configuración, multilingüe | Bloqueo a Google Cloud; coste por uso |
| IBM Watson Assistant | Madurez empresarial, multilingüe | Bloqueo a IBM; coste alto |
| LLM puro (GPT/Claude) con RAG | Calidad de respuestas | Riesgo de alucinaciones; coste por uso; dependencia de proveedor |

**Consecuencias.**
- ✅ Sin bloqueo tecnológico ni coste por uso.
- ✅ Configuración entregable como artefactos (intents en YAML, dominio, stories).
- ⚠️ Para casos complejos se evaluará añadir un capa **RAG con embeddings locales** sobre la base de conocimiento (decisión a tomar en Hito 2 según calidad obtenida).

---

## ADR-008 · Logging y observabilidad

**Estado:** Aceptado
**Fecha:** Hito 1 (Semana 2)

**Contexto.** El ENS Medio exige logs de auditoría con retención mínima de 12 meses. La operación del C.1 requiere monitorización 24/7 y reporting mensual al Ayuntamiento.

**Decisión.**
- **structlog** para logging estructurado (JSON en producción, texto coloreado en desarrollo).
- **Prometheus + Grafana** (o Nagios/Zabbix equivalentes) para métricas.
- **Elastic Stack** (o Loki + Grafana) para logs unificados.
- **Retención:** 6 meses logs operativos, 12 meses logs de auditoría/seguridad.
- **Si se ofertó SLA 99,5 %:** monitorización externa adicional con UptimeRobot/Nagios/Zabbix con panel exclusivo accesible al Ayuntamiento.

**Consecuencias.**
- ✅ Cumplimiento ENS Medio en trazabilidad.
- ✅ Reporting mensual automatizable a partir de las métricas.
- ✅ MTTR reducido por correlación entre logs de aplicación, BBDD, IoT y seguridad.

---

## ADR-009 · Estrategia de migraciones de BBDD

**Estado:** Aceptado
**Fecha:** Hito 1 (Semana 2)

**Contexto.** Los modelos evolucionarán durante los 48 meses de mantenimiento. Necesitamos un mecanismo seguro de cambios de esquema con rollback.

**Decisión.** **Alembic** con autogeneración a partir de los modelos SQLAlchemy.
- Migraciones revisadas y versionadas en Git.
- Aplicación automática en arranque del contenedor (`alembic upgrade head`).
- En producción: aplicación manual durante ventana de mantenimiento programada con backup previo.

**Consecuencias.**
- ✅ Cambios de esquema reproducibles y auditables.
- ✅ Posibilidad de downgrade ante incidencias.

---

## ADR-010 · Estrategia de tests y CI

**Estado:** Aceptado
**Fecha:** Hito 1 (Semana 2)

**Contexto.** El SAT del Hito 4 exige pruebas funcionales completas, pentest y validación WCAG. Necesitamos un pipeline de CI que detecte regresiones desde el primer día.

**Decisión.**
- **pytest + httpx** para tests unitarios y de integración (cobertura mínima 70 %).
- **ruff** para linting y formato.
- **mypy** en modo estricto para tipado.
- **pre-commit** para validación local antes de commit.
- **GitHub Actions** para CI: jobs de calidad y tests con servicios PostgreSQL/Redis dockerizados.

**Consecuencias.**
- ✅ Cobertura objetiva del cumplimiento de requisitos en cada PR.
- ✅ Calidad sostenida durante los 48 meses de mantenimiento evolutivo.

---

## ADR-011 · Subscriber MQTT bridging async/sync con loop dedicado

**Estado:** Aceptado
**Fecha:** Hito 2 (Semana 3)

**Contexto.** paho-mqtt expone callbacks síncronos pero la persistencia en BBDD es async (SQLAlchemy 2.0 + asyncpg). Necesitamos persistir cada observación sin bloquear el callback MQTT.

**Decisión.** Arrancar un **loop asyncio dedicado en un hilo aparte** y enviar las coroutines de persistencia con `asyncio.run_coroutine_threadsafe`. El callback de paho retorna inmediatamente y la persistencia se contabiliza por callback en cuanto la future termina.

**Alternativas consideradas.**
- `asyncio-mqtt` — biblioteca async pura. Rechazada porque no expone reconexión exponencial nativa al mismo nivel que paho-mqtt.
- Cola intermedia (Redis Streams o asyncio.Queue) — añade complejidad y un nuevo punto de fallo para un volumen modesto (60 s × 9 sensores ≈ 13.000 obs/día).

**Consecuencias.**
- ✅ Reconexión exponencial gestionada por paho-mqtt sin código adicional.
- ✅ Sin cuello de botella en el callback: errores de BBDD no detienen el flujo MQTT.
- ⚠️ Hace falta gestionar el ciclo de vida del loop secundario (start, shutdown limpio).

---

## ADR-012 · Pipeline Social Listening con conectores agnósticos + NLP por lexicón

**Estado:** Aceptado
**Fecha:** Hito 2 (Semana 3)

**Contexto.** Necesitamos capturar menciones de tres plataformas (X, Facebook, Instagram), normalizarlas a una entidad común y aplicar NLP multilingüe sin dependencias pesadas.

**Decisión.**

1. **Clase base** `SocialListeningConnector` con un único método `fetch_mentions(since)` que devuelve `MentionRaw`. Cada plataforma implementa la suya.
2. **Modo `dry-run`** integrado en cada conector: cuando `SOCIAL_DRY_RUN=true`, devuelven datos sintéticos en 4 idiomas. Permite desarrollar y demostrar antes de obtener tokens reales.
3. **Pipeline NLP propio** (lexicón con manejo de negación) en lugar de modelos ML pesados. Suficiente para el alcance del Hito 1 y eliminable en el Hito 2 sustituyendo la implementación sin tocar el resto.
4. **Deduplicación idempotente** por `(fuente, fuente_id_externo)` antes de persistir.

**Consecuencias.**
- ✅ Onboarding rápido sin tokens.
- ✅ Aislamiento entre conectores: un fallo en X no afecta a Facebook/Instagram.
- ⚠️ El NLP por lexicón tiene precisión modesta (~75-80 %); se sustituirá por un modelo HuggingFace si las métricas del Hito 4 lo requieren.

---

## ADR-013 · Chatbot Rasa con generación automática desde FAQs

**Estado:** Aceptado
**Fecha:** Hito 2 (Semana 4)

**Contexto.** Las FAQs son la fuente de verdad. Mantener manualmente `domain.yml`, `nlu.yml` y `rules.yml` en paralelo crea divergencias.

**Decisión.**

1. **Generador automático** `python -m nijar_dti.workers.rasa_generator` produce los cuatro archivos YAML desde `nijar_dti.data.seeds.faqs.FAQS_SEED`.
2. **Selector de motor** controlado por `CHATBOT_ENGINE`: `lexical` (Hito 1) o `rasa` (Hito 2). Los endpoints REST no cambian.
3. **Adapter** que llama a `/model/parse` (intent + score) y `/webhooks/rest/webhook` (texto). Mapeo de confianza: ≥0.75 alta, ≥0.55 media, resto fuera de dominio.
4. **Failover automático al motor lexical** si Rasa no responde y `RASA_FALLBACK_TO_LEXICAL=true`.

**Alternativas consideradas.**
- LLM con RAG — coste por uso, dependencia de proveedor, riesgo de alucinaciones.
- Mantener lexical como único motor — calidad insuficiente en preguntas complejas.

**Consecuencias.**
- ✅ Una sola fuente de verdad: las FAQs del seed. Cambiar una FAQ ↦ regenerar ↦ re-entrenar.
- ✅ Disponibilidad 99 %+ garantizada por el failover.
- ⚠️ El re-entrenamiento de Rasa es lento (varios minutos) y tiene que coordinarse cuando cambien las FAQs en producción.

---

## ADR-014 · Frontend sin build step: Tailwind CDN + ES Modules

**Estado:** Aceptado
**Fecha:** Hito 3 (Semana 6)

**Contexto.** Necesitamos un dashboard operativo del Smart Office y una plantilla de tótem accesible. El alcance del contrato no incluye el desarrollo de un SPA Next.js completo y la operación de mantenimiento durante 48 meses tiene que ser sencilla.

**Decisión.** Frontend en HTML estático servido por la propia API:

- **Tailwind CSS por CDN** — sin pipeline de build, sin `npm install` para mantener.
- **Vanilla JS con ES Modules** y `import` desde el navegador moderno.
- **Chart.js + Leaflet desde CDN** para visualización y mapas.
- **Servido por FastAPI** (`StaticFiles` montado en `/dashboard` y `/totem`).

**Alternativas consideradas.**
- React/Next.js — añade build step, dependencias npm, deuda técnica para 48 meses.
- Svelte/Vue — más ligero pero requiere build step igual.
- Reflex / Streamlit — desarrollo rápido pero acoplamiento fuerte al backend Python.

**Consecuencias.**
- ✅ Cero dependencias frontend que mantener.
- ✅ El Ayuntamiento puede auditar el código fácilmente.
- ✅ Carga rápida; los CDN están en caché en cualquier navegador moderno.
- ⚠️ Si el alcance crece (más vistas, gráficos complejos), conviene migrar a un framework. Decisión revisable en el Hito 5 si aparece el caso.

---

## ADR-015 · Tótem: kiosko HTML accesible con i18n controlado por client-side

**Estado:** Aceptado
**Fecha:** Hito 3 (Semana 6)

**Contexto.** Los tótems deben ser accesibles WCAG 2.1 AA, ofrecer 4 idiomas, funcionar offline-tolerante y volver al estado inicial tras inactividad.

**Decisión.**

1. **HTML estático sirviendo la plantilla** del tótem; el contenido dinámico (POIs, FAQs) se carga desde la API REST sin autenticación (canal público).
2. **i18n client-side** con un diccionario por idioma cargado al inicio. Cambiar idioma no recarga la página y conserva el contexto.
3. **Modos de accesibilidad** (texto grande, alto contraste) por toggles persistentes en `localStorage`.
4. **Detección de inactividad >60 s** que vuelve al estado inicial.
5. **Botones con área táctil ≥ 44 × 44 px** para uso en exterior con guantes/pulsera.

**Consecuencias.**
- ✅ Plantilla reutilizable: el mismo HTML sirve para los 2 tótems con solo cambiar `data-totem-id`.
- ✅ Cumple WCAG 2.1 AA con tests automatizados en CI.
- ⚠️ Sin Service Worker en esta versión — si el tótem pierde conexión durante > 5 min mostrará "Cargando…". Mitigación en Hito 4 con cache local de los POIs publicados.

---

## ADR-016 · GA4: conector con autenticación service-account y modo dry-run

**Estado:** Aceptado
**Fecha:** Hito 3 (Semana 7)

**Contexto.** El informe mensual del C.1 incluye una sección de eficacia digital que requiere métricas de la web turística (sesiones, usuarios, canales de adquisición). El Ayuntamiento usa Google Analytics 4.

**Decisión.**

1. **Conector** `connectors/analytics/ga4.py` que usa la **Reporting Data API v1beta** con autenticación por **service account JSON**.
2. **Modo dry-run** integrado: si las credenciales no están configuradas, devuelve datos sintéticos coherentes para desarrollo y demos.
3. **Llamada protegida** desde `dashboards_service.informe_mensual()` con `try/except`: si GA4 falla, el informe se entrega sin la sección de eficacia digital y se registra el error.
4. **Sin librería pesada**: la autenticación usa `google-auth` solo si está instalado; en modo dry-run no hay dependencia.

**Consecuencias.**
- ✅ Onboarding rápido: el informe mensual funciona desde el día 1, con datos sintéticos hasta que el Ayuntamiento entregue las credenciales.
- ✅ Failure-resilient: una caída de GA4 nunca tumba el informe mensual.
- ⚠️ `google-auth` se instala en producción cuando se activa GA4; documentado en `dependencias-terceros.md`.

---

## ADR-017 · Plan de pentest pre-SAT con metodología OWASP

**Estado:** Aceptado
**Fecha:** Hito 3 (Semana 7)

**Contexto.** El SAT del Hito 4 exige verificación de robustez técnica antes de la firma. El ENS Nivel Medio impone pruebas periódicas durante el C.1.

**Decisión.**

- Pentest gray-box principal + black-box complementario, ejecutado por un **tercero independiente** con certificaciones OSCP/CRT/OSWE.
- Metodología **OWASP WSTG + API Top 10:2023 + PTES**.
- Bloqueante para SAT: cero hallazgos críticos abiertos y todo hallazgo alto con plan de mitigación con fecha < 30 días.
- **Re-test** obligatorio tras mitigación.
- **Revisión anual** durante los 48 meses del C.1, ya incluida en el contrato.
- Pipeline CI ejecuta `pip-audit`, `osv-scanner`, `semgrep`, `trivy`, `bandit`, `axe-core` en cada PR.

**Consecuencias.**
- ✅ Trazabilidad completa para auditorías ENS.
- ✅ Detección temprana en CI reduce volumen de hallazgos en el pentest formal.
- ⚠️ Coste recurrente del pentest anual debe presupuestarse en el C.1 (incluido).

---

## ADR-018 · AWS eu-central-1 (Frankfurt) Multi-AZ con EKS managed

**Estado:** Aceptado
**Fecha:** Hito 4 (Semana 8)

**Contexto.** El contrato exige cumplimiento RGPD con datos en la UE. ENS Nivel Medio requiere alta disponibilidad y trazabilidad. El cliente prefiere portabilidad (no lock-in agresivo).

**Decisión.**
- **Región:** AWS eu-central-1 (Frankfurt) — UE, baja latencia desde España, ecosistema maduro.
- **Compute:** EKS managed (no ECS) — Kubernetes facilita la portabilidad a GKE/AKS/on-prem en el futuro.
- **Multi-AZ:** RDS, Redis y nodos EKS distribuidos en 3 AZ.
- **Cifrado:** KMS con rotación habilitada en todos los servicios stateful (RDS, EKS secrets, S3, Redis, Secrets Manager, AWS Backup).
- **Backups:** RDS automated 35 días + AWS Backup vault con vault lock 365 días + S3 versionado con Glacier después de 90 días.

**Alternativas consideradas.**
- ECS Fargate — más simple pero mayor lock-in y menos comunidad.
- eu-west-1 (Irlanda) — descartada por mayor latencia y pertenecer al mismo ámbito UE pero con riesgo Brexit residual.

**Consecuencias.**
- ✅ Cumplimiento RGPD evidente (datos siempre en UE).
- ✅ Portabilidad real: Kubernetes + PostgreSQL estándar + Prometheus.
- ⚠️ EKS tiene un coste fijo del control plane (~73 USD/mes). Aceptable para el alcance.

---

## ADR-019 · External Secrets Operator (ESO) en lugar de HashiCorp Vault

**Estado:** Aceptado
**Fecha:** Hito 4 (Semana 8)

**Contexto.** Necesitamos sincronizar secretos desde un secret store externo a Kubernetes Secrets, con rotación y mínima fricción operativa.

**Decisión.** Usar **External Secrets Operator** sincronizando desde **AWS Secrets Manager** con un refresh de 1 hora.

**Alternativas consideradas.**
- HashiCorp Vault — más potente pero requiere operar y mantener un servicio adicional.
- Sealed Secrets de Bitnami — los secretos viven en Git cifrados; rota mal.
- Secrets Store CSI Driver de AWS — se integra a nivel pod (volume), nuestro backend prefiere ENV variables.

**Consecuencias.**
- ✅ Sin servicio adicional que mantener.
- ✅ IAM como mecanismo de control (auditado en CloudTrail).
- ✅ Rotación automática de la password RDS por Secrets Manager se propaga en < 1 h.
- ⚠️ Si el cluster pierde permisos IAM, los secretos no se actualizan. Mitigado con alertas Prometheus en `kube_externalsecret_status`.

---

## ADR-020 · Prometheus + Grafana + Loki en lugar de CloudWatch puro

**Estado:** Aceptado
**Fecha:** Hito 4 (Semana 8)

**Contexto.** ENS Medio requiere observabilidad completa. AWS ofrece CloudWatch como solución integrada. Otra alternativa es la stack open-source.

**Decisión.** Usar **kube-prometheus-stack** + **Loki** para métricas y logs, con CloudWatch solo para los componentes que AWS publica nativamente (VPC Flow Logs, RDS Performance Insights, ALB access logs).

**Justificación.**
- **Portabilidad:** las dashboards y alertas no quedan atadas a AWS.
- **Coste:** CloudWatch cobra por GB ingestado y por métrica custom. Para volúmenes medios, Prometheus self-hosted es 5-10x más barato.
- **Estandarización:** la comunidad open-source ofrece dashboards reutilizables (Grafana Labs).
- **Comunicación con el Ayuntamiento:** Grafana es una herramienta visual y compartible.

**Consecuencias.**
- ✅ Dashboards exportables; el Ayuntamiento puede llevarse las JSON al final del contrato.
- ✅ AlertManager se integra con cualquier proveedor de notificaciones.
- ⚠️ Requiere mantener el stack (actualizaciones, capacity planning). Asumido en el C.1.

---

## ADR-021 · CI/CD con escaneo bloqueante y OIDC sin credenciales largas

**Estado:** Aceptado
**Fecha:** Hito 4 (Semana 8)

**Contexto.** El SAT del Hito 4 exige garantías de seguridad. Los workflows necesitan credenciales para hacer deploy a AWS.

**Decisión.**

1. **CI bloqueante** ante fallo en cualquiera de: pip-audit, OSV-Scanner, semgrep, bandit, Trivy de imagen, kubeconform, terraform validate, mypy, pytest, ruff.
2. **CD con OIDC** (GitHub → AWS IAM): el rol `AWS_DEPLOY_ROLE_ARN` se asume mediante WebIdentity, sin claves largas en GitHub.
3. **Escaneo nocturno** con cadencia diaria que crea issue automático si aparece CVE crítica nueva.
4. **Smoke test post-deploy** que dispara rollback si la API no responde 200 OK en 150 s.

**Consecuencias.**
- ✅ Sin secretos rotables que olvidar — OIDC es session-based.
- ✅ La superficie temporal de explotación es < 1 h (TTL de OIDC).
- ✅ Vulnerabilidades nuevas se detectan diariamente, no solo en PRs.
- ⚠️ El primer setup de OIDC requiere acción manual del responsable AWS del Ayuntamiento. Documentado en runbook.
