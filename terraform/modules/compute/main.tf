# ==========================================
# 1. VARIÁVEIS DE ENTRADA DO MÓDULO
# ==========================================
variable "environment" {}
variable "landing_bucket" {}
variable "lakehouse_arn" {}

# ==========================================
# 2. PERMISSÕES (IAM ROLE)
# ==========================================
resource "aws_iam_role" "lambda_glue_role" {
  name = "lambda_glue_role_${var.environment}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = ["lambda.amazonaws.com", "glue.amazonaws.com"] }
    }]
  })
}

# ==========================================
# 3. EXTRAÇÃO VIA API (ONS INFLATION)
# ==========================================
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../../../src/lambdas/api_extractor.py"
  output_path = "${path.module}/files/api_extractor.zip"
}

resource "aws_lambda_function" "api_extractor" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "uk_api_extractor_${var.environment}"
  role             = aws_iam_role.lambda_glue_role.arn
  handler          = "api_extractor.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      LANDING_BUCKET = var.landing_bucket
    }
  }
}

# ==========================================
# 4. EXTRAÇÃO VIA SFTP - EMPACOTAMENTO E ARTEFATO
# ==========================================
data "archive_file" "sftp_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../../src/lambdas"
  output_path = "${path.module}/files/sftp_extractor.zip"
  excludes    = ["api_extractor.py"] # Evita misturar o script da outra lambda
}

# Faz o upload do ZIP pesado para o S3 antes do deploy da Lambda
resource "aws_s3_object" "sftp_lambda_upload" {
  bucket = var.landing_bucket
  key    = "artifacts/sftp_extractor.zip"
  source = data.archive_file.sftp_lambda_zip.output_path
  etag   = data.archive_file.sftp_lambda_zip.output_md5
}

# ==========================================
# 5. EXTRAÇÃO VIA SFTP (UK COMPANIES) - CONFIGURAÇÃO DA LAMBDA
# ==========================================
resource "aws_lambda_function" "sftp_extractor" {
  function_name    = "uk_sftp_extractor_${var.environment}"
  role             = aws_iam_role.lambda_glue_role.arn
  handler          = "sftp_extractor.lambda_handler"
  runtime          = "python3.12"
  source_code_hash = data.archive_file.sftp_lambda_zip.output_base64sha256
  timeout          = 60

  # Configuração corrigida: Lê o pacote diretamente do S3 local para evitar estouro de payload HTTP
  s3_bucket        = var.landing_bucket
  s3_key           = aws_s3_object.sftp_lambda_upload.key

  environment {
    variables = {
      LANDING_BUCKET = var.landing_bucket
      SFTP_HOST      = "sftp_lakehouse"
      SFTP_PORT      = "22"
      SFTP_USER      = "sftpuser"
      SFTP_PASSWORD  = "password"
    }
  }
}

# ==========================================
# 6. OUTPUTS (SAÍDAS DO MÓDULO)
# ==========================================
output "lambda_arn" { 
  value = aws_lambda_function.api_extractor.arn 
}

output "sftp_lambda_arn" { 
  value = aws_lambda_function.sftp_extractor.arn 
}