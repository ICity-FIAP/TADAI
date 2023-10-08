import boto3

# Credenciais hardcoded (não recomendado)
aws_access_key_id = 'AKIAW5TF25IQM46BJS63'
aws_secret_access_key = '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'

# Cliente SNS
sns_client = boto3.client("sns", 
    region_name="us-east-1",
    aws_access_key_id=aws_access_key_id, 
    aws_secret_access_key=aws_secret_access_key
)  

topic_arn = 'arn:aws:sns:us-east-1:475881204256:SNS-ICity'

def pub():
    # Cliente S3
    s3_client = boto3.client('s3',
        region_name='us-east-1',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )
    
    # Estrutura da mensagem
    publish_object = {'ACIDENTE DETECTADO PORRA CARALHO'}
    message = str(publish_object)  # Converta o objeto para uma string para ser enviada como mensagem
    
    # Publicando a mensagem no SNS
    response = sns_client.publish(
        TopicArn=topic_arn,
        Subject='PURCHASE',
        Message=message,
        MessageAttributes={
            'TransactionType': {
                'DataType': 'String',
                'StringValue':'PURCHASE'
            }
        }
    )
    
    print(response['ResponseMetadata']['HTTPStatusCode'])

# Chamando a função
pub()
