FROM python:3.11

WORKDIR /app

# Copiar os arquivos para o diretório de trabalho
COPY . /app

# Instalar dependências
RUN pip install -r requirements.txt

# Comando para rodar o app
CMD ["flask", "run", "--host=0.0.0.0"]
