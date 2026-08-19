# =============================================================================
# RDS PostgreSQL 16 con PostGIS — BBDD principal
# =============================================================================

# Password aleatoria almacenada en Secrets Manager
resource "random_password" "db" {
  length  = 32
  special = true
  # Excluimos caracteres que dan problemas en URLs o shells
  override_special = "!#$%&*-_=+"
}

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${local.name_prefix}/db/password"
  description             = "Password del usuario maestro de RDS"
  recovery_window_in_days = 7
  kms_key_id              = aws_kms_key.secrets.id
  tags                    = local.common_tags
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db.result
}

# Subnet group privada
resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnets"
  subnet_ids = aws_subnet.private[*].id
  tags       = { Name = "${local.name_prefix}-db-subnets" }
}

# Security group: solo accesible desde EKS y bastión
resource "aws_security_group" "rds" {
  name        = "${local.name_prefix}-rds"
  description = "PostgreSQL accesible solo desde EKS"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Postgres desde EKS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-rds-sg" }
}

# Parameter group con PostGIS habilitado
resource "aws_db_parameter_group" "postgis" {
  name   = "${local.name_prefix}-postgis-pg16"
  family = "postgres16"

  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  tags = local.common_tags
}

resource "aws_db_instance" "main" {
  identifier     = "${local.name_prefix}-db"
  engine         = "postgres"
  engine_version = "16.3"
  instance_class = var.rds_instance_class

  allocated_storage     = var.rds_allocated_storage_gb
  max_allocated_storage = var.rds_allocated_storage_gb * 4
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.rds.arn

  db_name  = "nijar_dti"
  username = "nijar_admin"
  password = random_password.db.result
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.postgis.name
  publicly_accessible    = false

  multi_az                = var.environment == "production"
  backup_retention_period = var.rds_backup_retention_days
  backup_window           = "02:00-04:00"
  maintenance_window      = "sun:04:30-sun:06:00"

  enabled_cloudwatch_logs_exports = ["postgresql"]
  performance_insights_enabled    = true
  performance_insights_kms_key_id = aws_kms_key.rds.arn

  deletion_protection       = var.environment == "production"
  delete_automated_backups  = false
  skip_final_snapshot       = false
  final_snapshot_identifier = "${local.name_prefix}-db-final-${formatdate("YYYYMMDD-hhmm", timestamp())}"

  tags = { Name = "${local.name_prefix}-db" }

  lifecycle {
    ignore_changes = [final_snapshot_identifier, password]
  }
}

# KMS para cifrado RDS
resource "aws_kms_key" "rds" {
  description             = "Cifrado RDS ${local.name_prefix}"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  tags                    = local.common_tags
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${local.name_prefix}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

# KMS para Secrets Manager
resource "aws_kms_key" "secrets" {
  description             = "Cifrado de secretos ${local.name_prefix}"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  tags                    = local.common_tags
}

resource "aws_kms_alias" "secrets" {
  name          = "alias/${local.name_prefix}-secrets"
  target_key_id = aws_kms_key.secrets.key_id
}
