locals {
  env = terraform.workspace == "default" ? "local" : terraform.workspace
}

module "storage" {
  source      = "./modules/storage"
  environment = local.env
}

module "compute" {
  source         = "./modules/compute"
  environment    = local.env
  landing_bucket = module.storage.landing_bucket_name
  lakehouse_arn  = module.storage.lakehouse_bucket_arn
}

module "orchestration" {
  source                    = "./modules/orchestration"
  environment               = local.env
  
  # Recebe os ARNs das Lambdas recém-criadas no Compute
  lambda_extractor_arn      = module.compute.lambda_arn
  sftp_lambda_extractor_arn = module.compute.sftp_lambda_arn
}

module "processing" {
  source              = "./modules/processing"
  environment         = local.env
  glue_role_arn       = module.compute.glue_role_arn
  lakehouse_bucket_id = module.storage.lakehouse_bucket_name 
}