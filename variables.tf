variable "aws_region" {
  type        = string
  description = "Región de AWS donde se desplegarán los recursos de SecOps"
  default     = "us-east-1"
}

variable "bucket_name" {
  type        = string
  description = "Nombre global único del bucket de S3 para los logs de seguridad"
  default     = "secops-agent-logs-gabriel-2026"
}