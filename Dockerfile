# Use uma imagem base com Python
FROM python:3.9.13

# Copie os arquivos necessários para o contêiner
COPY app.py /app/
COPY app_updated.py /app/
COPY Final_MVP.html /app/
COPY Final_MVP_updated.html /app/
COPY Modelo.ipynb /app/
COPY requirements.txt /app/

# Defina o diretório de trabalho
WORKDIR /app

# Instale as dependências
RUN pip install -r requirements.txt

# Exponha a porta que o app usará
EXPOSE 5000

# Execute o app
CMD ["python", "app_AWS.py"]
