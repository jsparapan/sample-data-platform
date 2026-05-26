import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode

# 1. Injetar credenciais para o AWS SDK v2 do Iceberg ler automaticamente do Floci
os.environ["AWS_ACCESS_KEY_ID"] = "mock"
os.environ["AWS_SECRET_ACCESS_KEY"] = "mock"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

DATABASE_NAME = "uk_economy_db_local"
TABLE_NAME = "uk_cpi_inflation"
S3_LANDING_PATH = "s3a://uk-lakehouse-landing-local/raw/ons/cpi_data/*/*.json"

# Inicializa o Spark configurando o Iceberg para usar o Glue Catalog do Floci
spark = SparkSession.builder \
    .appName("FlociGlueIcebergInflationIngestion") \
    .config("spark.hadoop.fs.s3a.connection.timeout", "60000") \
    .config("spark.hadoop.fs.s3a.connection.establish.timeout", "60000") \
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

try:
    print(f"💡 Lendo dados brutos do JSON da ONS em: {S3_LANDING_PATH}")
    
    # 1. Lendo os dados brutos da Landing Zone (Bucket de Landing)
    df_raw = spark.read.json(S3_LANDING_PATH)
    df_years = df_raw.select(explode(col("years")).alias("year_data"))
    df_final = df_years.select(
        col("year_data.date").alias("year"),
        col("year_data.value").cast("double").alias("cpi_value"),
        col("year_data.label").alias("description")
    )

    table_fqdn = f"glue_catalog.{DATABASE_NAME}.{TABLE_NAME}"

    # 2. Cria o banco de dados dinamicamente no catálogo do Floci se não existir
    print(f"🏗️  Garantindo que o banco de dados '{DATABASE_NAME}' exista no Glue...")
    spark.sql(f"CREATE DATABASE IF NOT EXISTS glue_catalog.{DATABASE_NAME}")

    # 3. [CORREÇÃO] Estratégia Drop e Recria para evitar o erro do 'UpdateTable' no Floci
    if spark.catalog.tableExists(table_fqdn):
        print(f"💥 Tabela existente detectada. Executando DROP TABLE em: {table_fqdn}")
        spark.sql(f"DROP TABLE {table_fqdn}")

    print(f"✨ Criando a tabela nativa Iceberg do zero via API V2: {table_fqdn}")
    df_final.writeTo(table_fqdn).create()

    print("🚀 Processamento concluído! Dados salvos no formato Iceberg e catalogados no Glue do Floci.")
    
    # Validação rápida exibindo o resultado final na tela
    print("\n🔍 Validando dados gravados na tabela de Inflação:")
    spark.sql(f"SELECT * FROM {table_fqdn} LIMIT 5").show(truncate=False)

except Exception as e:
    print(f"❌ Erro durante o processamento da Bronze (Inflation): {str(e)}")
    raise e
finally:
    spark.stop()