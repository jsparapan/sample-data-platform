locals {
  env = terraform.workspace
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
  lambda_extractor_arn      = module.compute.lambda_arn
  sftp_lambda_extractor_arn = module.compute.sftp_lambda_arn
}