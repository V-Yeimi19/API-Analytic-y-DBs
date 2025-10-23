FROM python:3.11-slim

WORKDIR /app

# Copiamos los archivos necesarios
COPY requirements.txt .

# Instala dependencias del sistema necesarias para compilar cryptography
RUN apt-get update && apt-get install -y gcc libssl-dev python3-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["python", "ingest_data.py"]

