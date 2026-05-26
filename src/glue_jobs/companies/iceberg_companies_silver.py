import os
from pyspark.sql import SparkSession

# 1. Injetar credenciais para o AWS SDK v2 do Iceberg ler automaticamente
os.environ["AWS_ACCESS_KEY_ID"] = "mock"
os.environ["AWS_SECRET_ACCESS_KEY"] = "mock"
os.environ["AWS_REGION"] = "us-east-1"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

DATABASE_NAME = "uk_economy_db_local"
SOURCE_TABLE = "uk_companies"       # Camada Bronze/Raw (Origem)
TARGET_TABLE = "uk_companies_silver" # Camada Silver (Destino)

# Inicialização do SparkSession alinhado com o Floci e Iceberg 1.5.2
spark = SparkSession.builder \
    .appName("FlociCompaniesSilverIngestion") \
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
    source_fqdn = f"glue_catalog.{DATABASE_NAME}.{SOURCE_TABLE}"
    target_fqdn = f"glue_catalog.{DATABASE_NAME}.{TARGET_TABLE}"
    
    print(f"📖 Lendo dados da tabela de origem (Bronze): {source_fqdn}")
    # Lendo diretamente a tabela Iceberg que você acabou de popular
    df_bronze = spark.read.table(source_fqdn)
    
    # Aplicando a regra de negócio da camada Silver (Filtrar apenas status 'Active')
    print("🧹 Aplicando regras de limpeza da camada Silver (status = 'Active')...")
    df_silver = df_bronze.filter(df_bronze["status"] == "Active")
    
    # Estratégia de Drop se já existir no Floci (Contorno da limitação do UpdateTable)
    if spark.catalog.tableExists(target_fqdn):
        print(f"💥 Tabela Silver existente detectada. Executando DROP TABLE em: {target_fqdn}")
        spark.sql(f"DROP TABLE {target_fqdn}")
        
    print(f"✨ Criando a nova tabela Silver Iceberg: {target_fqdn}")
    df_silver.writeTo(target_fqdn).create()
    print("✅ Carga da camada Silver concluída com sucesso!")
    
    # Validação rápida exibindo o resultado final na tela
    print("\n🔍 Validando dados gravados na camada Silver:")
    spark.sql(f"SELECT * FROM {target_fqdn}").show(truncate=False)

except Exception as e:
    print(f"❌ Erro durante o processamento da Silver: {str(e)}")
    raise e
finally:
    spark.stop()