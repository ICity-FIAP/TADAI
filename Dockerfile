# Utilize uma imagem com Python pré-instalado
FROM python:3.9-slim

# Crie um diretório de trabalho
WORKDIR /app

# Copie o código do aplicativo e dependências para o contêiner
COPY app_AWS.py /app
COPY requirements.txt /app


# Instale as dependências
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Baixar o modelo de S3 durante a construção (se aplicável e seguro para o seu uso caso)
# RUN aws s3 cp s3://your-bucket/Model /app/Model

# Quando o contêiner iniciar, execute o aplicativo Flask
CMD ["python", "./app_AWS.py"]
