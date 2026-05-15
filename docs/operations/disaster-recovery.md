# Plan de Disaster Recovery (DR)

| | |
|---|---|
| **Expediente** | 18962/2025 |
| **Hito** | H4 — SAT y puesta en producción |
| **Versión** | 1.0 |
| **Marco** | ENS Nivel Medio (medida `op.cont.4 — Pruebas periódicas`) |

---

## 1. Objetivos de recuperación

| Métrica | Objetivo | Justificación |
|---------|----------|---------------|
| **RTO** (Recovery Time Objective) | **4 horas** | Compatible con la disponibilidad del 99% mensual (~7h26m de downtime/mes admisible) |
| **RPO** (Recovery Point Objective) | **1 hora** | Frecuencia de los backups automáticos de RDS + archivado de logs MQTT |
| **MTTR** indicativo | **30 minutos** | Para incidencias menores y rollback de despliegue |

## 2. Inventario de activos críticos

| Activo | Mecanismo de protección | Frecuencia |
|--------|-------------------------|------------|
| **BBDD PostgreSQL** | RDS automated backup (35 días) + AWS Backup vault (1 año) + snapshots manuales antes de cambios mayores | Diario + bajo demanda |
| **Secretos** | AWS Secrets Manager con replicación entre AZ + KMS rotación de claves | Continuo |
| **Imágenes Docker** | ECR con `lifecycle` (mantiene 30 imágenes) | Por cada deploy |
| **Modelos Rasa** | PVC EBS con snapshots semanales | Semanal |
| **Configuración K8s** | Manifests en Git (todo es declarativo) | Por cada commit |
| **Estado Terraform** | S3 versionado + DynamoDB lock | Por cada apply |
| **Logs operativos** | CloudWatch Logs (365 días) + Loki (30 días en cluster) | Continuo |
| **Frontend (dashboard, tótem)** | Servido por la propia API; redundancia en Git + S3 | Por cada deploy |

## 3. Escenarios de desastre y procedimientos

### 3.1 Caída de un nodo EKS
**Impacto:** mínimo — los pods se reaparición en otros nodos.
**Acción:** automatizada por el ASG. Verificar con `kubectl get nodes`.

### 3.2 Caída de una AZ
**Impacto:** degradación temporal.
**Acción:**
- RDS Multi-AZ promueve la réplica automáticamente (~60-120 s).
- Redis Multi-AZ failover automático.
- EKS reprograma pods en las otras 2 AZ.
- ALB redirige tráfico a las AZ sanas.

Verificación post-incidente:
```bash
aws rds describe-db-instances --db-instance-identifier nijar-dti-production-db \
  --query "DBInstances[0].AvailabilityZone"
kubectl get pods -n nijar-dti -o wide  # comprobar distribución
```

### 3.3 Pérdida total de la BBDD
**Impacto:** alto — la API responde 503 hasta el restore.
**Procedimiento (RTO < 2h):**

```bash
# 1. Identificar el snapshot más reciente
aws rds describe-db-snapshots \
  --db-instance-identifier nijar-dti-production-db \
  --snapshot-type automated \
  --query "DBSnapshots[?Status=='available'] | sort_by(@, &SnapshotCreateTime) | [-1].DBSnapshotIdentifier"

# 2. Restaurar a una nueva instancia (renombrar la antigua antes)
aws rds modify-db-instance --db-instance-identifier nijar-dti-production-db \
  --new-db-instance-identifier nijar-dti-production-db-broken \
  --apply-immediately

aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier nijar-dti-production-db \
  --db-snapshot-identifier <snapshot-id> \
  --db-instance-class db.t3.medium \
  --multi-az \
  --kms-key-id $(aws kms describe-key --key-id alias/nijar-dti-production-rds --query KeyMetadata.Arn --output text)

# 3. Esperar (10-30 min) y verificar
aws rds wait db-instance-available --db-instance-identifier nijar-dti-production-db

# 4. Reiniciar la API para que tome la nueva conexión
kubectl rollout restart -n nijar-dti deployment/nijar-api
```

### 3.4 Pérdida total del cluster EKS
**Impacto:** crítico — toda la plataforma cae.
**Procedimiento (RTO < 4h):**

```bash
cd infra/terraform
terraform apply  # recrea el cluster (~20 min)

# Aplicar manifests siguiendo el runbook punto 4
# (la BBDD persiste en RDS — solo recreamos el plano de aplicación)
```

### 3.5 Compromiso de credenciales
**Impacto:** alto — riesgo de exfiltración o sabotaje.
**Procedimiento:**

1. Rotar inmediatamente la password RDS:
   ```bash
   aws secretsmanager rotate-secret --secret-id nijar-dti-production/db/password
   ```
2. Forzar refresh de ExternalSecrets en K8s.
3. Revocar tokens JWT activos (incrementar `SECRET_KEY` invalida todos):
   ```bash
   aws secretsmanager update-secret \
     --secret-id nijar-dti-production/api/secret-key \
     --secret-string "$(openssl rand -hex 32)"
   kubectl rollout restart -n nijar-dti deployment/nijar-api
   ```
4. Auditar CloudTrail buscando accesos sospechosos.
5. Notificar al DPO en las primeras 72h si hay datos personales afectados (RGPD art. 33).

### 3.6 Cifrado por ransomware
**Impacto:** crítico.
**Mitigación previa:** los backups en AWS Backup vault tienen `vault lock` que impide eliminación incluso por el rol de admin.
**Procedimiento:** restaurar desde el último snapshot pre-incidente del vault.

### 3.7 Pérdida de la región AWS
**Impacto:** crítico.
**Mitigación:** la inversión en una región alternativa no está incluida en el contrato base. Se ofrece como mejora con coste adicional.

Plan documental: en caso de catástrofe regional, IT DIGITTAL tiene capacidad técnica de reconstruir la plataforma en otra región UE (eu-west-1) en 72 h:
- Estado Terraform exportable desde S3.
- Imágenes Docker replicables a un ECR de otra región.
- BBDD reconstruible desde snapshots cross-region (mejora opcional con coste).

## 4. Pruebas periódicas (Drill)

| Frecuencia | Prueba | Responsable |
|------------|--------|-------------|
| **Trimestral** | Restore de BBDD a un entorno aislado | IT DIGITTAL — DBA |
| **Trimestral** | Failover Multi-AZ forzado en staging | IT DIGITTAL — Ops |
| **Anual** | Recreación completa del cluster en staging | IT DIGITTAL — Ops |
| **Anual** | Simulacro de compromiso de credenciales | IT DIGITTAL — Seguridad |

Cada ejercicio se documenta con:

- Fecha y duración
- Escenario simulado
- RTO real medido
- RPO real medido
- Hallazgos y acciones de mejora

Los informes se entregan al Ayuntamiento dentro del informe mensual del C.1 del mes en el que se realicen.

## 5. Comunicación durante un incidente

| Severidad | Canal | Plazo de notificación al Ayuntamiento |
|-----------|-------|----------------------------------------|
| Crítica (servicio caído) | Llamada + email + ticket | < 30 minutos |
| Alta (degradación importante) | Email + ticket | < 2 horas |
| Media (incidencia controlada) | Ticket | < 8 horas |
| Baja | Ticket / informe mensual | Reporte rutinario |

Plantilla de comunicación:
- Resumen del incidente.
- Servicios afectados.
- Causa raíz (preliminar) y acción inmediata.
- ETA de resolución.
- Datos personales potencialmente afectados (Sí/No → notificación al DPO).

## 6. Mantenimiento programado

Las ventanas de mantenimiento se anuncian con **5 días hábiles** de antelación al Ayuntamiento. Por defecto:

- **Domingos 02:00-06:00 CET** — actualizaciones menores (RDS auto-minor, deploy de la plataforma).
- **Trimestral** — actualizaciones mayores planificadas.

Las ventanas de mantenimiento programado **no cuentan como downtime** a efectos del cálculo de SLA.
