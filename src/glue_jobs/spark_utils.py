import os
from pyspark.sql import SparkSession

def get_spark_session(app_name: str) -> SparkSession:
    """Configura e retorna uma SparkSession otimizada para Iceberg e Floci (AWS Local)"""
    
    os.environ["AWS_ACCESS_KEY_ID"] = "mock"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "mock"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.glue_catalog.warehouse", "s3a://uk-lakehouse-iceberg-local/warehouse/") \
        .config("spark.sql.catalog.glue_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog") \
        .config("spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO") \
        .config("spark.sql.catalog.glue_catalog.s3.endpoint", "http://localhost:4566") \
        .config("spark.sql.catalog.glue_catalog.glue.endpoint", "http://localhost:4566") \
        .config("spark.sql.catalog.glue_catalog.s3.path-style-access", "true") \
        .config("spark.sql.catalog.glue_catalog.client.region", "us-east-1") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://localhost:4566") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.access.key", "mock") \
        .config("spark.hadoop.fs.s3a.secret.key", "mock") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()