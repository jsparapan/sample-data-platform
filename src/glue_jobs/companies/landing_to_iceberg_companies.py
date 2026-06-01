import os
from spark_utils import get_spark_session

# 1. Injetar credenciais para o AWS SDK v2 do Iceberg ler automaticamente
os.environ["AWS_ACCESS_KEY_ID"] = "mock"
os.environ["AWS_SECRET_ACCESS_KEY"] = "mock"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

DATABASE_NAME = "uk_economy_db_local"
TABLE_NAME = "uk_companies"
S3_LANDING_PATH = "s3a://uk-lakehouse-landing-local/raw/sftp/uk_companies/*.csv"

spark = get_spark_session("FlociCompaniesIcebergGlue")

try:
    print(f"📖 Lendo dados brutos do SFTP em: {S3_LANDING_PATH}")
    df_raw = spark.read.option("header", "true").option("inferSchema", "true").csv(S3_LANDING_PATH)
    
    print(f"🏗️  Garantindo que o banco de dados '{DATABASE_NAME}' exista no Glue...")
    spark.sql(f"CREATE DATABASE IF NOT EXISTS glue_catalog.{DATABASE_NAME}")

    table_fqdn = f"glue_catalog.{DATABASE_NAME}.{TABLE_NAME}"
    
    if spark.catalog.tableExists(table_fqdn):
        print(f"💥 Tabela existente detectada. Executando DROP TABLE em: {table_fqdn}")
        spark.sql(f"DROP TABLE {table_fqdn}")
    
    print(f"✨ Criando a tabela nativa Iceberg do zero: {table_fqdn}")
    df_raw.writeTo(table_fqdn).create()
        
    print("✅ Processamento concluído com sucesso (Tabela recriada)!")

    print("🔍 Validando a gravação do Iceberg...")
    spark.sql(f"SELECT * FROM glue_catalog.{DATABASE_NAME}.{TABLE_NAME} LIMIT 5").show(truncate=False)

except Exception as e:
    print(f"❌ Erro durante o processamento: {str(e)}")
    raise e
finally:
    spark.stop()