variable "environment" {
  type        = string
  description = "O ambiente atual vindo do workspace (ex: local, dev, prod)"
}

variable "lambda_extractor_arn" {
  type        = string
  description = "ARN da Lambda que extrai dados da API do ONS"
}

variable "sftp_lambda_extractor_arn" {
  type        = string
  description = "ARN da Lambda que extrai dados do servidor SFTP"
}