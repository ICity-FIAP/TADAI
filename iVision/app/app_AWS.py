#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮Bibliotecas❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import os
import cv2
import numpy as np
import tensorflow.keras.backend as K
import time
import threading
import atexit
import boto3
import json
import tempfile
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from flask import Flask, request, jsonify, send_from_directory, Response
from tensorflow.keras.models import load_model
from tempfile import NamedTemporaryFile
from tensorflow.keras.applications.vgg16 import preprocess_input, VGG16
from moviepy.editor import ImageSequenceClip
from dotenv import load_dotenv
from flask_cors import CORS
from botocore.exceptions import ClientError
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━





#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮AWS CREDENTIALS❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import boto3
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


def create_temporary_token(secret_name, region_name):
    credentials = get_secret(secret_name, region_name)
    
    sts_client = boto3.client(
        'sts',
        aws_access_key_id=credentials['aws_access_key_id'],
        aws_secret_access_key=credentials['aws_secret_access_key'],
        region_name=region_name
    )
    
    assumed_role_object = sts_client.assume_role(
        RoleArn="arn:aws:iam::account-of-the-role-to-assume:role/name-of-the-role",
        RoleSessionName="AssumeRoleSession1"
    )
    
    credentials = assumed_role_object['Credentials']
    
    return {
        'aws_access_key_id': credentials['AccessKeyId'],
        'aws_secret_access_key': credentials['SecretAccessKey'],
        'aws_session_token': credentials['SessionToken']
    }

# Retrieve AWS Secrets and Set as Environment Variables
try:
    secrets = get_secret('YOUR_SECRET_NAME', 'YOUR_AWS_REGION')
    os.environ.update(secrets)
except Exception as e:
    print(f"Unable to retrieve secrets: {str(e)}")

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮SNS❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

sns_client = boto3.client('sns', region_name='us-east-1')
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━






#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮S3❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
S3_BUCKET_NAME = 'tadai-icity'
s3_client = boto3.client('s3')
model_key = 's3://tadai-icity/Modelo/Model/'

def upload_video_to_s3(file_name, bucket, object_name=None):
    s3 = boto3.client('s3')
    s3.upload_file(file_name, bucket, object_name or file_name)

def get_s3_video_url(bucket, file_name):
    return f"https://{bucket}.s3.amazonaws.com/{file_name}"


#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━





# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮Kinesis❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

kinesis_client = boto3.client('kinesis', region_name='us-east-1')

response = kinesis_client.get_data_endpoint(
    StreamName='your_stream_name',
    APIName='GET_MEDIA'
)
stream_url = response['DataEndpoint']

kvam = boto3.client('kinesis-video-archived-media', endpoint_url=stream_url)
url_response = kvam.get_hls_streaming_session_url(
    StreamName='your_stream_name',
    PlaybackMode='LIVE'
)
url = url_response['HLSStreamingSessionURL']

# Load ML Model from S3 Bucket
def load_model_from_s3(bucket_name, model_key):
    s3_client = boto3.client('s3')
    with tempfile.NamedTemporaryFile(suffix='.h5') as tmp:
        s3_client.download_file(bucket_name, model_key, tmp.name)
        model = load_model(tmp.name)
    return model

# Example of model loading, replace with your real values
# CNN_Model = load_model_from_s3('your_bucket_name', 'your_model_key')
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮SNS❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def send_accident_notification(topic_arn, message, subject):
    # Criar um cliente SNS
    sns_client = boto3.client(
        'sns',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name='us-east-1'
    )
    
    # Enviar a mensagem
    response = sns_client.publish(
        TopicArn=topic_arn,
        Message=message,
        Subject=subject
    )
    
    return response


#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮S3❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'S3_BUCKET_NAME')
s3_client = boto3.client('s3')

def upload_video_to_s3(file_name, bucket, object_name=None):
    s3 = boto3.client('s3')
    s3.upload_file(file_name, bucket, object_name or file_name)

def get_s3_video_url(bucket, file_name):
    return f"https://{bucket}.s3.amazonaws.com/{file_name}"

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮Kinesis❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Criação de um Cliente Kinesis
kinesis_client = boto3.client('kinesis', region_name='us-east-1')  # Corrigido para us-east-1

# Substitua 'SeuStreamName' pelo nome do seu stream
stream_name = 'SeuStreamName'

# Obtenção da URL do Stream de Vídeo
try:
    response = kinesis_client.get_data_endpoint(
        StreamName=stream_name,
        APIName='GET_MEDIA'
    )
    stream_url = response['DataEndpoint']
except boto3.exceptions.botocore.exceptions.EndpointConnectionError as e:
    print(f"Erro ao conectar com o endpoint: {str(e)}")
    # Adicione mais tratamentos conforme necessário

# Obtenção do URL da Sessão de Streaming HLS
try:
    kvam = boto3.client('kinesis-video-archived-media', endpoint_url=stream_url)
    url_response = kvam.get_hls_streaming_session_url(
        StreamName=stream_name,
        PlaybackMode='LIVE'
    )
    url = url_response['HLSStreamingSessionURL']
except Exception as e:
    print(f"Erro ao obter a URL de streaming: {str(e)}")
    # Adicione mais tratamentos conforme necessário

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━





#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮SNS❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

sns_client = boto3.client('sns', region_name='us-east-1')
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━






#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮Inicio de ambientes❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
app = Flask(__name__)
CORS(app)
load_dotenv('amb_var.env')
video_buffer = []

FPS = 30  # Assumindo que a câmera tenha 30 FPS, ajustar se necessário
BUFFER_SIZE = 15 * FPS  # 10 segundos de vídeo

CNN_Model = load_model_from_s3(S3_BUCKET_NAME, model_key)

base_model = VGG16(include_top=False, weights='imagenet', input_shape=(224, 224, 3))


temp_folder ='s3://tadai-icity/Video/'

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮Camera❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Camera:
    accident_detected = False

    def __init__(self, video_url):
        self.video_url = video_url
        self.frame = None
        self.accident_flag = False
        self.max_prob = 0
        self.lock = threading.Lock()

    def capture_frame_from_kinesis(self):
        cap = cv2.VideoCapture(self.video_url)
        ret, frame = cap.read()
        if not ret:
            print("Erro ao capturar frame do vídeo")
            return None
        cap.release()
        return frame

    def run(self):
        while True:
            frame = self.capture_frame_from_kinesis()
            if frame is None:
                break
            else:
                prediction = predict_accident(frame)
                max_prob = prediction[0][0]
                with self.lock:
                    self.frame = frame
                    self.max_prob = max_prob
                    self.accident_flag = max_prob > 0.3       # limiar de decisão
                    Camera.accident_detected = self.accident_flag
            if self.accident_flag:
                clip_name = "accident_clip.mp4"
                clip_path = os.path.join(temp_folder, clip_name)
                save_buffer_as_video(video_buffer, clip_path)

camera = Camera(video_url)  # Passe a URL do vídeo do Kinesis como argumento

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━





#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮Funções Real Time❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def gen_frames(camera):
    global video_buffer
    clip_saved = False  # Indicador para evitar salvar clipes repetidos do mesmo evento
    while True:
        with camera.lock:
            frame = camera.frame
            # Adicionando o frame ao buffer
            video_buffer.append(frame)
            if len(video_buffer) > 10 * FPS:
                video_buffer.pop(0)
            max_prob = camera.max_prob
            accident_flag = camera.accident_flag

        if frame is None:
            continue

        text = f'Probabilidade de Acidente: {max_prob*100:.2f}%'
        color = (0, 0, 255) if accident_flag else (0, 255, 0)
        cv2.putText(frame, text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
        
        # Salvar um clipe se um acidente for detectado
        if accident_flag and not clip_saved:
            clip_name = "accident_clip.mp4"
            clip_path = os.path.join(temp_folder, clip_name)

            save_buffer_as_video(video_buffer[-10 * FPS:], clip_path)
            clip_saved = True
        elif not accident_flag:
            clip_saved = False

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def save_buffer_as_video(buffer, filename):
    if not buffer:
        return

    # Verificar se todos os quadros são válidos
    if any(frame is None for frame in buffer):
        print("Erro: buffer de vídeo contém quadros inválidos.")
        return

    # Se todos os quadros forem válidos, continue com a criação do clipe
    fps = FPS
    clip = ImageSequenceClip([cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) for frame in buffer], fps=fps)
    clip.write_videofile(filename, codec='libx264')


#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮Funções Envio de Video❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def prepared_frame(frame):
    frame = cv2.resize(frame, (224, 224))
    frame = np.expand_dims(frame, axis=0)
    frame = preprocess_input(frame)
    features = base_model.predict(frame)
    return features.flatten().reshape(1, -1)

def predict_accident(frame):
    frame_ready = prepared_frame(frame)
    prediction = CNN_Model.predict(frame_ready)
    return prediction



def detect_accident(video_path, CNN_Model):
    cap = cv2.VideoCapture(video_path)
    accident_flag = False
    max_prediction = 0
    frame_window = []
    frame_skip = 2  # Processar cada segundo quadro
    current_frame = 0

    try:
        while True:
            ret, frame = cap.read()
            current_frame += 1
            if current_frame % frame_skip != 0:
                continue
            if ret:
                frame_ready = prepared_frame(frame)
                prediction = CNN_Model.predict(frame_ready)
                frame_window.append(prediction[0][0])
                if len(frame_window) > 15:
                    frame_window.pop(0)
                
                max_prediction = max(max_prediction, prediction[0][0])
                avg_prediction = np.mean(frame_window)

                if avg_prediction > 0.3:  # limiar de decisão
                    accident_flag = True

                if accident_flag:
                    send_accident_notification()
                    predict = f"Probabilidade de acidente: {100 * avg_prediction:.2f}%"
                else:
                    predict = "Sem acidente"

                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(frame, predict, (50, 50), font, 1, (0, 255, 255), 3, cv2.LINE_4)
                cv2.imshow('Frame', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        K.clear_session()
        try:
            time.sleep(1.25)
            os.unlink(video_path)
        except PermissionError:
            print("Não foi possível excluir o arquivo. Ele pode estar sendo usado por outro processo.")
    
    return max_prediction, accident_flag
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━





template ='s3://tadai-icity/Template/'

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮Rotas❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
@app.route('/hello', methods=['GET'])
def HelloWorld():
    return 'Hello World'


@app.route('/', methods=['GET', 'POST'])
def home():
    return send_from_directory(template, 'Final_MVP.html')


@app.route('/api/upload', methods=['POST'])
def upload():
    video = request.files['video']
    temp_video_file = NamedTemporaryFile(delete=False)
    video.save(temp_video_file.name)
    max_prob, accident_flag = detect_accident(video_path=temp_video_file.name, CNN_Model=CNN_Model)
    if accident_flag:
        send_accident_notification()
        return jsonify({'status': 'danger', 'message': f"Acidente detectado com probabilidade de {100 * max_prob:.2f}%!", 'pred': float(max_prob)})
    else:
        return jsonify({'status': 'safe', 'message': f"Sem acidentes detectados. Probabilidade de segurança: {100 * (1 - max_prob):.2f}%", 'pred': 1 - float(max_prob)})

    
@app.route('/video_feed')
def video_feed():
    camera_thread = threading.Thread(target=camera.run)
    camera_thread.start()
    return Response(gen_frames(camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/accident_status')
def accident_status():
    return jsonify({
        "Acidente_detectado": bool(Camera.accident_detected)  # Convertendo para booleano padrão
    })




@app.route('/accident_clip', methods=['GET'])
def accident_clip():
    filename = "accident_clip.mp4"

    # Construa a URL do clipe de vídeo no S3
    video_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{filename}"

    # Retorne a URL do clipe de vídeo
    return jsonify({'video_url': video_url})



# @app.route('/some_route', methods=['GET'])
# def some_route():
#     """
#     Uma rota de exemplo que faz algo com um segredo recuperado do AWS Secrets Manager.
    
#     :return: Uma resposta HTTP.
#     """
#     secret = get_secret()
#     if secret is None:
#         return "Error retrieving secret", 500
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━❮◆❯━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━




#━━━━━━━━━━━━━━━━━━━━━❮Iniciar❯━━━━━━━━━━━━━━━━━━━━

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True) #mudar debug para flase