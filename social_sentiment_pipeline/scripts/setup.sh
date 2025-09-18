#!/bin/bash

# Script de configuración inicial del pipeline de análisis de sentimientos

echo "🚀 Configurando Pipeline de Análisis de Sentimientos..."

# Verificar que Docker esté instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor instala Docker primero."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Por favor instala Docker Compose primero."
    exit 1
fi

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p data/models
mkdir -p logs
mkdir -p airflow/logs
mkdir -p airflow/plugins

# Copiar archivo de configuración de ejemplo
if [ ! -f .env ]; then
    echo "📋 Copiando archivo de configuración..."
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales de Twitter API"
fi

# Descargar modelo de ML (simulado)
echo "🤖 Preparando modelo de ML..."
mkdir -p data/models/sentiment
echo "Modelo de sentimientos descargado" > data/models/sentiment/model_info.txt

# Configurar permisos para Airflow
echo "🔐 Configurando permisos..."
sudo chown -R 50000:0 airflow/logs airflow/plugins 2>/dev/null || echo "Nota: No se pudieron cambiar permisos (normal en algunos sistemas)"

# Construir imágenes Docker
echo "🐳 Construyendo imágenes Docker..."
docker-compose build

# Crear redes Docker
echo "🌐 Configurando redes..."
docker network create sentiment-pipeline 2>/dev/null || echo "Red ya existe"

echo "✅ Configuración inicial completada!"
echo ""
echo "📝 Próximos pasos:"
echo "1. Edita el archivo .env con tus credenciales de Twitter API"
echo "2. Ejecuta: docker-compose up -d"
echo "3. Espera unos minutos para que todos los servicios se inicien"
echo "4. Accede a:"
echo "   - Airflow: http://localhost:8080 (admin/admin)"
echo "   - Grafana: http://localhost:3000 (admin/admin)"
echo "   - Kafka UI: http://localhost:8081"
echo ""
echo "🎉 ¡Listo para procesar sentimientos en tiempo real!"