# Runbook operativo — Plataforma DTI Níjar

| | |
|---|---|
| **Expediente** | 18962/2025 |
| **Hito** | H4 — SAT y puesta en producción |
| **Versión** | 1.0 |

Documento operativo para la puesta en producción y el día a día durante los 48 meses del C.1.

---

## 1. Bootstrap del backend Terraform

Antes del primer `terraform apply` hay que crear el bucket S3 y la tabla DynamoDB que almacenan el estado. **Esto se hace una sola vez por entorno** y se ejecuta con credenciales de un IAM admin del Ayuntamiento.

```bash
# 1. Crear el bucket S3 (estado)
aws s3 mb s3://nijar-dti-tfstate --region eu-central-1
aws s3api put-bucket-versioning \
  --bucket nijar-dti-tfstate \
  --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption \
  --bucket nijar-dti-tfstate \
  --server-side-encryption-configuration '{
    "Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"aws:kms"}}]
  }'
aws s3api put-public-access-block \
  --bucket nijar-dti-tfstate \
  --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# 2. Crear la tabla DynamoDB (lock)
aws dynamodb create-table \
  --table-name nijar-dti-tfstate-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-central-1

# 3. Aplicar Terraform
cd infra/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

Outputs relevantes que necesitarás después:

```bash
terraform output kubeconfig_command
terraform output ecr_api_repository_url
terraform output rds_password_secret_arn
terraform output acm_certificate_arn
terraform output waf_acl_arn
```

## 2. Configurar kubectl

```bash
$(terraform output -raw kubeconfig_command)
kubectl get nodes
```

## 3. Vincular IRSA (IAM Roles for Service Accounts)

El ServiceAccount `nijar-api` en el namespace `nijar-dti` debe asumir un rol IAM con permisos para Secrets Manager y S3. Sustituye `<ACCOUNT-ID>`:

```bash
# Crear el rol IAM con la confianza al OIDC provider del cluster
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OIDC_ID=$(aws eks describe-cluster --name nijar-dti-production \
  --query "cluster.identity.oidc.issuer" --output text | sed 's|.*/||')

cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/oidc.eks.eu-central-1.amazonaws.com/id/${OIDC_ID}" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "oidc.eks.eu-central-1.amazonaws.com/id/${OIDC_ID}:sub": "system:serviceaccount:nijar-dti:nijar-api",
        "oidc.eks.eu-central-1.amazonaws.com/id/${OIDC_ID}:aud": "sts.amazonaws.com"
      }
    }
  }]
}
EOF

aws iam create-role --role-name nijar-dti-production-irsa \
  --assume-role-policy-document file://trust-policy.json

# Attach políticas mínimas
aws iam attach-role-policy --role-name nijar-dti-production-irsa \
  --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
aws iam attach-role-policy --role-name nijar-dti-production-irsa \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

## 4. Despliegue inicial

```bash
# 1. Sustituir placeholders en los manifests
sed -i "s|ACCOUNT-ID|$ACCOUNT_ID|g" infra/k8s/00-namespace.yaml
sed -i "s|ECR_REPO_URL|$(terraform -chdir=infra/terraform output -raw ecr_api_repository_url)|g" infra/k8s/*.yaml
sed -i "s|ACM_CERTIFICATE_ARN|$(terraform -chdir=infra/terraform output -raw acm_certificate_arn)|g" infra/k8s/50-ingress.yaml
sed -i "s|WAF_ACL_ARN|$(terraform -chdir=infra/terraform output -raw waf_acl_arn)|g" infra/k8s/50-ingress.yaml

# 2. Instalar AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName=nijar-dti-production \
  --set serviceAccount.create=true \
  --set serviceAccount.name=aws-load-balancer-controller

# 3. Instalar External Secrets Operator
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets --create-namespace

# 4. Instalar observabilidad
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kube-prom prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --values infra/observability/prometheus-values.yaml

helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --values infra/observability/loki-values.yaml

# 5. Aplicar manifests de la plataforma
kubectl apply -f infra/k8s/00-namespace.yaml
kubectl apply -f infra/k8s/15-config.yaml
kubectl apply -f infra/k8s/20-external-secrets.yaml
kubectl apply -f infra/k8s/40-mqtt-rasa.yaml
kubectl apply -f infra/k8s/30-workers.yaml
kubectl apply -f infra/k8s/10-api-deployment.yaml
kubectl apply -f infra/k8s/50-ingress.yaml

# 6. ServiceMonitor + alertas
kubectl apply -f infra/observability/prometheus-servicemonitor.yaml
kubectl apply -f infra/observability/alerts.yaml

# 7. Verificar
kubectl get pods -n nijar-dti
kubectl rollout status -n nijar-dti deployment/nijar-api
```

## 5. Comandos del día a día

### Ver logs en directo
```bash
kubectl logs -n nijar-dti -l app=nijar-api --tail=100 -f
kubectl logs -n nijar-dti -l app=nijar-mqtt-subscriber --tail=100 -f
```

### Reiniciar un componente
```bash
kubectl rollout restart -n nijar-dti deployment/nijar-api
```

### Conectar a la BBDD desde un pod efímero
```bash
kubectl run pgcli --rm -it -n nijar-dti --image=postgres:16-alpine --restart=Never -- \
  psql "$DATABASE_URL"
```

### Acceder a Grafana
```bash
kubectl port-forward -n monitoring svc/kube-prom-grafana 3000:80
# http://localhost:3000  (usuario admin, password en values.yaml)
```

### Forzar refresco de External Secrets
```bash
kubectl annotate externalsecret -n nijar-dti nijar-api-secrets \
  force-sync=$(date +%s) --overwrite
```

## 6. Troubleshooting

| Síntoma | Causa probable | Acción |
|---------|----------------|--------|
| API responde 503 | ALB sin endpoints sanos | `kubectl get pods -n nijar-dti -l app=nijar-api` y revisar readinessProbe |
| Pods en CrashLoopBackOff | Secrets no sincronizados | `kubectl describe externalsecret -n nijar-dti` y revisar logs del operator |
| Migración Alembic falla | Versión de tabla `alembic_version` divergente | Conectar a la BBDD y revisar; la migración se relanza con `kubectl delete job nijar-migrate -n nijar-dti && kubectl apply -f infra/k8s/30-workers.yaml` |
| Sin ingesta IoT | Subscriber MQTT down o broker inaccesible | Logs del subscriber y del Mosquitto, comprobar `kubectl exec -it mqtt-0 -n nijar-dti -- mosquitto_sub -t '#' -v` |
| Chatbot devuelve fallback siempre | Rasa caído o modelo no cargado | `kubectl logs -n nijar-dti deployment/rasa`. Re-entrenar si es necesario |
| Alta latencia API | HPA no escaló o queries lentas | Grafana → API overview → p95. Revisar Performance Insights de RDS |

## 7. Re-entrenamiento del chatbot Rasa

Cuando se añadan FAQs en `nijar_dti.data.seeds.faqs`:

```bash
# 1. Regenerar artefactos Rasa desde las FAQs actualizadas
kubectl exec -n nijar-dti deployment/nijar-api -- \
  python -m nijar_dti.workers.rasa_generator --out-dir /tmp/rasa-new

# 2. Copiar al pod de Rasa y entrenar
kubectl cp /tmp/rasa-new nijar-dti/$(kubectl get pod -n nijar-dti -l app=rasa -o name | head -1):/app/
kubectl exec -n nijar-dti deployment/rasa -- rasa train --out /app/models

# 3. Reiniciar Rasa para cargar el modelo
kubectl rollout restart -n nijar-dti deployment/rasa
```

## 8. Procedimientos de emergencia

### Rollback rápido
```bash
kubectl rollout undo -n nijar-dti deployment/nijar-api
kubectl rollout status -n nijar-dti deployment/nijar-api
```

### Drenar un nodo
```bash
kubectl cordon <node>
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
```

### Escalar manualmente
```bash
kubectl scale -n nijar-dti deployment/nijar-api --replicas=4
```

### Acceso de emergencia con credenciales root de RDS
La password está en Secrets Manager. **Solo el responsable técnico** puede consultarla:

```bash
aws secretsmanager get-secret-value \
  --secret-id nijar-dti-production/db/password \
  --query SecretString --output text
```

Toda consulta queda registrada en CloudTrail (ENS Medio).
