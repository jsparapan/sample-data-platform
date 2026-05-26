terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = var.aws_region
  access_key                  = "mock_access_key"
  secret_key                  = "mock_secret_key"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  dynamic "endpoints" {
    for_each = terraform.workspace == "local" ? [1] : []
    content {
      s3        = "http://localhost:4566"
      glue      = "http://localhost:4566"
      lambda    = "http://localhost:4566"
      events    = "http://localhost:4566"
      iam       = "http://localhost:4566"
      sts       = "http://localhost:4566"
    }
  }
}