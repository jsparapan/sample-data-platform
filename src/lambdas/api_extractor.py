import json
import urllib.request
import os
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Iniciando execução da Lambda de extração do ONS (CPI)...")
    
    # ROTA DEFINITIVA: Endpoint público e estável do ONS para a série d7g7 (CPI)
    url = "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7g7/mm23/data"
    
    bucket_name = os.environ.get("LANDING_BUCKET", "uk-lakehouse-landing-local")
    
    # Identifica o Floci na rede do Docker ou usa o localhost
    floci_endpoint = os.environ.get("AWS_ENDPOINT_URL", "http://172.17.0.1:4566")
    
    logger.info(f"Configuração - Bucket: {bucket_name} | Endpoint S3: {floci_endpoint}")
    
    s3_client = boto3.client("s3", endpoint_url=floci_endpoint, region_name="us-east-1")
    
    try:
        # Cria a requisição simulando um navegador comum para evitar bloqueios
        logger.info(f"Fazendo requisição GET para a URL: {url}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            logger.info("Dados obtidos e decodificados com sucesso da API do ONS.")
            
        current_date = datetime.now().strftime("%Y-%m-%d")
        s3_key = f"raw/ons/cpi_data/{current_date}/inflation.json"
        
        logger.info(f"Fazendo upload do JSON para s3://{bucket_name}/{s3_key}...")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(data)
        )
        
        logger.info("Upload concluído com sucesso!")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f"Sucesso! Arquivo salvo em {s3_key}")
        }
        
    except Exception as e:
        # exc_info=True captura o stack trace completo (a linha exata do erro)
        logger.error(f"Erro crítico ao extrair dados: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps(f"Erro ao extrair dados: {str(e)}")
        }