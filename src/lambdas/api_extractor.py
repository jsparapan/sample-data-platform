import json
import urllib.request
import os
import boto3
from datetime import datetime

def lambda_handler(event, context):
    # ROTA DEFINITIVA: Endpoint público e estável do ONS para a série d7g7 (CPI)
    url = "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7g7/mm23/data"
    
    bucket_name = os.environ.get("LANDING_BUCKET", "uk-lakehouse-landing-local")
    
    # Identifica o Floci na rede do Docker ou usa o localhost
    floci_endpoint = os.environ.get("AWS_ENDPOINT_URL", "http://172.17.0.1:4566")
    s3_client = boto3.client("s3", endpoint_url=floci_endpoint, region_name="us-east-1")
    
    try:
        # Cria a requisição simulando um navegador comum para evitar bloqueios
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            
        current_date = datetime.now().strftime("%Y-%m-%d")
        s3_key = f"raw/ons/cpi_data/{current_date}/inflation.json"
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(data)
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps(f"Sucesso! Arquivo saved em {s3_key}")
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f"Erro ao extrair dados: {str(e)}")
        }