import os
import boto3
import paramiko

def lambda_handler(event, context):
    # Pega as variáveis vindas do Terraform (ou defaults para local)
    sftp_host = os.environ.get("SFTP_HOST", "sftp_lakehouse") 
    sftp_port = int(os.environ.get("SFTP_PORT", 22))
    sftp_user = os.environ.get("SFTP_USER", "sftpuser")
    sftp_pass = os.environ.get("SFTP_PASSWORD", "password")
    bucket_name = os.environ.get("LANDING_BUCKET")
    
    s3_client = boto3.client("s3")
    
    print(f"Conectando ao servidor SFTP {sftp_host}:{sftp_port}...")
    
    # Configurando o cliente SSH e ignorando validação estrita de host key (apenas para lab/estudo)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(sftp_host, port=sftp_port, username=sftp_user, password=sftp_pass)
        sftp = ssh.open_sftp()
        
        remote_path = "/upload"
        files = sftp.listdir(remote_path)
        print(f"Arquivos encontrados no SFTP: {files}")
        
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
                print(f"Sucesso: {file_name} transferido para s3://{bucket_name}/{s3_key}")
                
        return {"statusCode": 200, "body": "Extração SFTP concluída com sucesso."}
        
    except Exception as e:
        print(f"Falha na extração SFTP: {str(e)}")
        return {"statusCode": 500, "body": f"Erro: {str(e)}"}
        
    finally:
        if 'sftp' in locals(): sftp.close()
        if 'ssh' in locals(): ssh.close()