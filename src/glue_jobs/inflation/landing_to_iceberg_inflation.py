from spark_utils import get_spark_session
from pyspark.sql.functions import col, explode

DATABASE_NAME = "uk_economy_db_local"
TABLE_NAME = "uk_cpi_inflation"
S3_LANDING_PATH = "s3a://uk-lakehouse-landing-local/raw/ons/cpi_data/*/*.json"

spark = get_spark_session("FlociGlueIcebergInflationIngestion")

try:
    print(f"💡 Lendo dados brutos: {S3_LANDING_PATH}")
    df_raw = spark.read.json(S3_LANDING_PATH)
    df_years = df_raw.select(explode(col("years")).alias("year_data"))
    df_final = df_years.select(
        col("year_data.date").alias("year"),
        col("year_data.value").cast("double").alias("cpi_value"),
        col("year_data.label").alias("description")
    )

    table_fqdn = f"glue_catalog.{DATABASE_NAME}.{TABLE_NAME}"
    spark.sql(f"CREATE DATABASE IF NOT EXISTS glue_catalog.{DATABASE_NAME}")

    print(f"✨ Atualizando a tabela nativa Iceberg: {table_fqdn}")
    
    # A SOLUÇÃO: Em vez de Drop + Create, usamos createOrReplace()
    df_final.writeTo(table_fqdn) \
        .tableProperty("format-version", "2") \
        .createOrReplace()

    print("🚀 Processamento concluído! Histórico e Time Travel preservados.")

except Exception as e:
    print(f"❌ Erro no processamento: {str(e)}")
    raise e
finally:
    spark.stop()