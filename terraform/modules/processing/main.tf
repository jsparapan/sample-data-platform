variable "environment" { type = string }
variable "glue_role_arn" { type = string }
variable "lakehouse_bucket_id" { type = string }

locals {
  glue_jobs = {
    "inflation_bronze" = {
      script_name = "landing_to_iceberg_inflation.py"
      local_path  = "src/glue_jobs/inflation/landing_to_iceberg_inflation.py"
    }
    "companies_bronze" = {
      script_name = "landing_to_iceberg_companies.py"
      local_path  = "src/glue_jobs/companies/landing_to_iceberg_companies.py"
    }
    "companies_silver" = {
      script_name = "iceberg_companies_silver.py"
      local_path  = "src/glue_jobs/companies/iceberg_companies_silver.py"
    }
  }
}

resource "aws_s3_object" "scripts_upload" {
  # O for_each faz o Terraform iterar sobre o mapa local.glue_jobs
  for_each = local.glue_jobs

  bucket = var.lakehouse_bucket_id
  key    = "scripts/${each.value.script_name}"
  source = "${path.root}/../${each.value.local_path}"
  etag   = filemd5("${path.root}/../${each.value.local_path}")
}

resource "aws_glue_job" "jobs" {
  # Se for "local", count = 0 (não cria nada no Floci). Se não for, cria 1 para cada item do mapa
  count = var.environment == "local" ? 0 : length(local.glue_jobs)

  # Como usamos count, precisamos transformar o mapa em uma lista indexada para acessar os valores
  # O Terraform criará: jobs[0] (inflation_bronze), jobs[1] (companies_bronze), etc.
  name     = "${keys(local.glue_jobs)[count.index]}_${var.environment}"
  role_arn = var.glue_role_arn
  
  command {
    # Aponta dinamicamente para o script correto que subiu para o S3 no passo anterior
    script_location = "s3://${var.lakehouse_bucket_id}/scripts/${values(local.glue_jobs)[count.index].script_name}"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"     = "python"
    "--datalake-formats" = "iceberg"
    "--conf"             = "spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions --conf spark.sql.catalog.glue_catalog=org.apache.iceberg.spark.SparkCatalog"
  }

  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
}