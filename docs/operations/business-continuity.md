# Plan de Continuidad de Negocio — C.1 (48 meses)

| | |
|---|---|
| **Expediente** | 18962/2025 |
| **Marco** | ENS Nivel Medio · UNE-ISO 22301 |
| **Versión** | 1.0 |

---

## 1. Objetivo

Garantizar la continuidad operativa de la Plataforma DTI Níjar durante los 48 meses del C.1, anticipando escenarios de degradación y definiendo respuestas que minimicen el impacto al ciudadano y al Ayuntamiento.

## 2. Procesos críticos

| Proceso | Criticidad | Tolerancia a la interrupción |
|---------|------------|-------------------------------|
| Atención al ciudadano vía tótems | **Alta** | < 4 h |
| Chatbot multilingüe | Media | < 12 h |
| Ingesta IoT (Smart Office) | Media | < 24 h (los datos no se pierden gracias a las colas MQTT) |
| Captura Social Listening | Baja | < 7 días |
| Informe mensual del C.1 | Alta | Imprescindible cada mes natural |

## 3. Estrategias de continuidad

### 3.1 Arquitectura tolerante a fallos

- **Multi-AZ en producción:** RDS, Redis, EKS nodos repartidos en 3 AZ (eu-central-1a, 1b, 1c).
- **Sin SPOFs internos:** cada componente tiene replica o se reaparece automáticamente (Deployment con HPA, StatefulSet con PVC, ALB redundante por AWS).
- **Stateless API:** los pods de la API no guardan estado; cualquier réplica responde indistintamente.
- **Workers idempotentes:** subscriber MQTT y social-worker pueden reiniciarse sin pérdida de información.

### 3.2 Backups multinivel

| Nivel | Cobertura | Retención |
|-------|-----------|-----------|
| RDS automated backup | BBDD completa | 35 días |
| AWS Backup vault (con vault lock) | BBDD + EBS de Rasa | 365 días |
| S3 versionado | exportaciones, configuración, modelos | versionado infinito + Glacier > 90 días |
| Git | manifests, código, ADRs, runbooks | infinito |
| ECR | imágenes Docker | 30 últimas |

### 3.3 Despliegue declarativo

Toda la plataforma es **infrastructure-as-code**:
- AWS → Terraform (infra/terraform/)
- Kubernetes → Manifests YAML (infra/k8s/)
- Observabilidad → Helm values + PrometheusRule + ServiceMonitor (infra/observability/)
- Configuración Rasa → Generada desde FAQs (regenerable)

Esto permite **reconstruir el entorno completo desde cero en horas** si fuera necesario, partiendo solo del repositorio Git.

### 3.4 Independencia de proveedor

Aunque el deploy actual es AWS, el diseño minimiza el lock-in:
- Kubernetes en lugar de servicios propietarios (ECS / Lambda) → portable a GKE / AKS / on-prem.
- Prometheus + Grafana + Loki en lugar de CloudWatch como única fuente de observabilidad.
- PostgreSQL gestionado pero estándar — la BBDD se puede migrar a otro proveedor con `pg_dump`.
- Imágenes Docker en ECR pero igualmente push-eables a otro registry.

## 4. Escenarios de continuidad

### 4.1 Indisponibilidad del proveedor cloud (AWS) prolongada

- Política comunicada al Ayuntamiento.
- Si > 24 h: replicación urgente del estado en otra región UE (mejora opcional con coste).
- Si > 7 días: invocación de la cláusula de fuerza mayor del contrato.

### 4.2 Caída del proveedor de RRSS (X / Facebook / Instagram)

- El conector falla con error controlado.
- El resto de la plataforma continúa operando.
- Las menciones del periodo se recuperan al volver el servicio (la API de X mantiene 7 días, Meta más).

### 4.3 Caída de Google Analytics

- El informe mensual se entrega sin la sección de eficacia digital.
- Notificación al Ayuntamiento de la incidencia.

### 4.4 Pérdida del personal clave de IT DIGITTAL

- Documentación operativa exhaustiva (este runbook + ADRs + diagramas) permite que un ingeniero senior nuevo se ponga al día en < 5 días.
- Mínimo 2 personas formadas a la vez en cada componente crítico.

## 5. Comunicación con el Ayuntamiento durante un evento de continuidad

- **Responsable de cuenta**: punto único de contacto durante incidentes.
- **Reuniones de seguimiento**: semanales en condiciones normales, diarias durante incidentes severos.
- **Informes específicos**: en menos de 5 días hábiles tras cualquier evento de criticidad alta.

## 6. Compromisos del C.1

Durante los 48 meses se garantiza:

- SLA de disponibilidad mensual contractual.
- Soporte 24/7 con SOC.
- Mantenimiento correctivo, evolutivo y normativo (incluido).
- Pentest anual (incluido).
- Drill de DR trimestral (incluido).
- Informe mensual de servicio (incluido).
- Entrega final del repositorio + documentación + datos al Ayuntamiento al finalizar el contrato.

## 7. Transición al fin del contrato

A los 48 meses, IT DIGITTAL entrega al Ayuntamiento:

1. **Repositorio Git completo** con todo el código y la infraestructura.
2. **Imágenes Docker** publicadas en un registry pactado.
3. **Backup completo** de la BBDD (formato `pg_dump`).
4. **Documentación operativa actualizada** (runbook, DR, SLAs, ADRs).
5. **Sesiones de transferencia** (mínimo 16 h) con el equipo TIC del Ayuntamiento o el adjudicatario sucesor.
6. **Acceso de solo lectura** durante 30 días post-contrato para resolución de dudas.

El Ayuntamiento puede continuar el servicio internamente, externalizarlo a otro adjudicatario o pasar a otro proveedor cloud sin lock-in tecnológico.
