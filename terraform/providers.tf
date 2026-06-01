provider "aws" {
  region = var.aws_region
  
  access_key = terraform.workspace == "local" ? "mock_access_key" : null
  secret_key = terraform.workspace == "local" ? "mock_secret_key" : null

  skip_credentials_validation = terraform.workspace == "local" ? true : false
  skip_metadata_api_check     = terraform.workspace == "local" ? true : false
  skip_requesting_account_id  = terraform.workspace == "local" ? true : false
  s3_use_path_style           = terraform.workspace == "local" ? true : false

  # Bloco dinâmico mantido apenas para os endpoints
  dynamic "endpoints" {
    for_each = terraform.workspace == "local" ? [1] : []
    content {
      s3     = "http://localhost:4566"
      glue   = "http://localhost:4566"
      lambda = "http://localhost:4566"
      events = "http://localhost:4566"
      iam    = "http://localhost:4566"
      sts    = "http://localhost:4566"
      secretsmanager = "http://localhost:4566"
    }
  }
}