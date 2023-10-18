# sudo apt update && sudo apt upgrade
# sudo pip install awscli boto3
# sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly


import boto3
import subprocess
import time
import json
from botocore.exceptions import ClientError


def get_secret():
    secret_name = "app_AWS_py"
    region_name = "us-east-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
    )

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("The requested secret " + secret_name + " was not found")
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            print("The request was invalid due to:", e)
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            print("The request had invalid params:", e)
        elif e.response['Error']['Code'] == 'DecryptionFailure':
            print("The requested secret can't be decrypted using the provided KMS key:", e)
        elif e.response['Error']['Code'] == 'InternalServiceError':
            print("An error occurred on service side:", e)
            
    else:
        if 'SecretString' in get_secret_value_response:
            text_secret_data = get_secret_value_response['SecretString']
            try:
                secrets = json.loads(text_secret_data)
            except json.JSONDecodeError as json_error:
                print("Error: Failed to decode the secret string as JSON:", str(json_error))
                return None
            else:
                return secrets


secrets = get_secret()

# Example of how to access the values
# (add verification logic as needed)
if secrets:
    AWS_ACCESS_KEY_ID = secrets.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = secrets.get('AWS_SECRET_ACCESS_KEY')
    ARN_SNS = secrets.get('ARN_SNS')
else:
    print("No secrets were retrieved.")
    AWS_ACCESS_KEY_ID = AWS_SECRET_ACCESS_KEY = ARN_SNS = None


# Configurações iniciais
role_to_assume_arn = 'arn:aws:iam::YOUR_ACCOUNT_ID:role/YourRoleName'
stream_name = "YourStreamName"
duration_seconds = 3600  # 1 hora

session = boto3.Session()

def get_temporary_credentials():
    sts_client = session.client('sts')
    assumed_role_object = sts_client.assume_role(
        RoleArn=role_to_assume_arn,
        RoleSessionName="SampleSession",
        DurationSeconds=duration_seconds
    )
    return assumed_role_object['Credentials']

def start_streaming_to_kinesis(credentials):
    kinesis_client = boto3.client(
        'kinesisvideo',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    
    # Obter a URL de endpoint do Kinesis Video Streams
    response = kinesis_client.get_data_endpoint(
        StreamName=stream_name,
        APIName='PUT_MEDIA'
    )

    endpoint_url = response['DataEndpoint']
    
    rtsp_url = "rtsp://admin:P@ssw0rd@192.168.15.189:554/cam/realmonitor?channel=1&subtype=0"  # Substitua pelo seu endereço RTSP
    
    # Caminhos dos certificados
    certificate_path = "rasp\certificate.pem.crt"
    private_key_path = "rasp\private.pem.key"
    ca_path = "rasp\AmazonRootCA1.pem"  # Se você tiver um CA root
    
    # Usando o GStreamer para capturar o fluxo RTSP e transmitir para o Kinesis
    cmd = (
        f"gst-launch-1.0 rtspsrc location={rtsp_url} short-header=TRUE ! "
        f"rtph264depay ! h264parse ! video/x-h264,stream-format=avc,alignment=au ! "
        f"kvssink stream-name={stream_name} storage-size=512 "
        f"access-key={credentials['AccessKeyId']} "
        f"secret-key={credentials['SecretAccessKey']} "
        f"aws-region='us-east-1' "
        f"iot-certificate='{certificate_path}' "
        f"iot-private-key='{private_key_path}' "
        f"iot-core-endpoint='YOUR_IOT_ENDPOINT' "  # Substitua pelo seu endpoint do IoT Core
        f"sts-endpoint='' "
        f"kinesis-video-endpoint='{endpoint_url}'"
    )
    
    if ca_path:  # Se você tiver um CA root
        cmd += f" ca-cert-path='{ca_path}'"
    
    subprocess.run(cmd, shell=True)


def main():
    while True:
        try:
            credentials = get_temporary_credentials()
            start_streaming_to_kinesis(credentials)
            time.sleep(600)  # Supondo que você deseje retransmitir ou verificar a cada 10 minutos
        except Exception as e:
            print(f"Erro encontrado: {e}. Tentando novamente...")

if __name__ == "__main__":
    main()
