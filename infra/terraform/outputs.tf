output "vpc_id" {
  description = "ID de la VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "IDs de las subnets privadas (EKS, RDS, Redis)"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "IDs de las subnets públicas (ALB)"
  value       = aws_subnet.public[*].id
}

output "eks_cluster_name" {
  description = "Nombre del cluster EKS"
  value       = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  description = "Endpoint API del cluster EKS"
  value       = aws_eks_cluster.main.endpoint
}

output "eks_cluster_ca_certificate" {
  description = "CA certificate del cluster EKS (base64)"
  value       = aws_eks_cluster.main.certificate_authority[0].data
  sensitive   = true
}

output "rds_endpoint" {
  description = "Endpoint RDS PostgreSQL"
  value       = aws_db_instance.main.address
}

output "rds_port" {
  description = "Puerto RDS"
  value       = aws_db_instance.main.port
}

output "rds_database_name" {
  description = "Nombre de la base de datos"
  value       = aws_db_instance.main.db_name
}

output "rds_password_secret_arn" {
  description = "ARN del Secret de Secrets Manager con la password de RDS"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "redis_primary_endpoint" {
  description = "Endpoint primario de Redis"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "ecr_api_repository_url" {
  description = "URL del repositorio ECR de la API"
  value       = aws_ecr_repository.api.repository_url
}

output "s3_backups_bucket" {
  description = "Bucket S3 de backups"
  value       = aws_s3_bucket.backups.id
}

output "acm_certificate_arn" {
  description = "ARN del certificado ACM (para asociar al ALB)"
  value       = aws_acm_certificate.main.arn
}

output "waf_acl_arn" {
  description = "ARN del Web ACL del WAF"
  value       = aws_wafv2_web_acl.main.arn
}

output "kubeconfig_command" {
  description = "Comando para configurar kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.main.name}"
}
