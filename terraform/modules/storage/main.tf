variable "environment" { type = string }

resource "aws_s3_bucket" "landing" {
  bucket        = "uk-lakehouse-landing-${var.environment}"
  force_destroy = true
}

resource "aws_s3_bucket" "lakehouse" {
  bucket        = "uk-lakehouse-iceberg-${var.environment}"
  force_destroy = true
}

output "landing_bucket_name" { value = aws_s3_bucket.landing.id }
output "lakehouse_bucket_arn"  { value = aws_s3_bucket.lakehouse.arn }
output "lakehouse_bucket_name" { value = aws_s3_bucket.lakehouse.id }