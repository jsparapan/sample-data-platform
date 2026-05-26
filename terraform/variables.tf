variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Ambiente vindo do Workspace"
  default     = "local"
}