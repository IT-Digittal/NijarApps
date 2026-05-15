terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.50" }
    random = { source = "hashicorp/random", version = "~> 3.6" }
  }

  # Estado remoto en S3 con bloqueo en DynamoDB.
  # IMPORTANTE: el bucket y la tabla se crean fuera de Terraform (bootstrap)
  # para evitar el problema del huevo y la gallina. Ver docs/operations/runbook.md.
  backend "s3" {
    bucket         = "nijar-dti-tfstate"
    key            = "production/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "nijar-dti-tfstate-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge({
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Expediente  = "18962-2025"
      Marco       = "PRTR-NextGenerationEU-C14"
      Owner       = "IT-DIGITTAL"
      Compliance  = "ENS-Medio,RGPD"
    }, var.tags_extra)
  }
}

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}
