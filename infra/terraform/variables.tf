variable "project_name" {
  type        = string
  default     = "nijar-dti"
  description = "Identificador del proyecto. Se usa como prefijo de los recursos AWS."
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Entorno: production | staging."
  validation {
    condition     = contains(["production", "staging"], var.environment)
    error_message = "environment debe ser production o staging."
  }
}

variable "aws_region" {
  type        = string
  default     = "eu-central-1"
  description = "Región AWS. Por requisito RGPD debe estar en la UE."
  validation {
    condition     = can(regex("^eu-", var.aws_region))
    error_message = "La región debe estar en la UE (prefijo eu-)."
  }
}

variable "vpc_cidr" {
  type    = string
  default = "10.30.0.0/16"
}

variable "availability_zones" {
  type    = list(string)
  default = ["eu-central-1a", "eu-central-1b", "eu-central-1c"]
}

variable "eks_cluster_version" {
  type    = string
  default = "1.30"
}

variable "eks_node_instance_types" {
  type    = list(string)
  default = ["t3.large"]
}

variable "eks_node_desired_capacity" {
  type    = number
  default = 2
}

variable "eks_node_min_capacity" {
  type    = number
  default = 2
}

variable "eks_node_max_capacity" {
  type    = number
  default = 6
}

variable "rds_instance_class" {
  type    = string
  default = "db.t3.medium"
}

variable "rds_allocated_storage_gb" {
  type    = number
  default = 50
}

variable "rds_backup_retention_days" {
  type    = number
  default = 35
}

variable "redis_node_type" {
  type    = string
  default = "cache.t3.small"
}

variable "domain_name" {
  type        = string
  default     = "dti.nijar.es"
  description = "Dominio base del servicio."
}

variable "tags_extra" {
  type    = map(string)
  default = {}
}
