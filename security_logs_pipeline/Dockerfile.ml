FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY src/ml_models/ ./ml_models/
COPY src/utils/ ./utils/

# Crear directorio para modelos
RUN mkdir -p /app/models

# Comando por defecto
CMD ["python", "ml_models/anomaly_detector.py"]