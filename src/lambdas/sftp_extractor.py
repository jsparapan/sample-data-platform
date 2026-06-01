import os
import json
import boto3
import logging
import paramiko

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_secret(secret_arn, endpoint_url):
    """Busca as credenciais do SFTP no Secrets Manager de forma segura"""
    logger.info(f"Buscando credenciais do segredo: {secret_arn}")
    
    # Conecta ao Secrets Manager apontando para o Floci
    client = boto3.client(
        service_name='secretsmanager',
        region_name='us-east-1',
        endpoint_url=endpoint_url
    )
    
    try:
        response = client.get_secret_value(SecretId=secret_arn)
        return json.loads(response['SecretString'])
    except Exception as e:
        logger.error("Erro ao buscar o segredo", exc_info=True)
        raise e

def lambda_handler(event, context):
    # 1. Recuperando Variáveis de Ambiente
    secret_arn = os.environ['SECRET_ARN']
    bucket_name = os.environ['LANDING_BUCKET']
    sftp_host = os.environ['SFTP_HOST']
    sftp_port = int(os.environ.get('SFTP_PORT', 22))
    endpoint = os.environ.get('AWS_ENDPOINT_URL', "http://172.17.0.1:4566")
    
    # 2. Inicializando clientes AWS
    s3_client = boto3.client("s3", endpoint_url=endpoint, region_name="us-east-1")
    
    # 3. Recupera as credenciais de forma segura em tempo de execução
    credentials = get_secret(secret_arn, endpoint)
    sftp_user = credentials['username']
    sftp_pass = credentials['password']
    
    logger.info(f"Conectando ao SFTP ({sftp_host}:{sftp_port}) com o usuário: {sftp_user}")
    
    try:
        # 4. Inicializando o cliente SSH (Paramiko)
        ssh = paramiko.SSHClient()
        # Ignora a verificação da chave do host (útil para ambientes locais/mockados)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(sftp_host, port=sftp_port, username=sftp_user, password=sftp_pass)
        sftp = ssh.open_sftp()
        
        remote_path = "/upload"
        files = sftp.listdir(remote_path)
        logger.info(f"Arquivos encontrados no SFTP: {files}")
        
        for file_name in files:
            if file_name.endswith(".csv"):
                remote_file_path = f"{remote_path}/{file_name}"
                
                # Abre o arquivo no SFTP e lê os bytes
                with sftp.open(remote_file_path, "rb") as remote_file:
                    file_content = remote_file.read()
                
                # Define o destino na Landing Zone
                s3_key = f"raw/sftp/uk_companies/{file_name}"
                
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=file_content
                )
                logger.info(f"Sucesso: {file_name} transferido para s3://{bucket_name}/{s3_key}")
                
        return {"statusCode": 200, "body": "Extração SFTP concluída com sucesso."}
        
    except Exception as e:
        logger.error(f"Falha na extração SFTP: {str(e)}", exc_info=True)
        return {"statusCode": 500, "body": f"Erro: {str(e)}"}
        
    finally:
        # Garante que as conexões sejam fechadas mesmo se houver erro
        if 'sftp' in locals(): 
            sftp.close()
        if 'ssh' in locals(): 
            ssh.close()