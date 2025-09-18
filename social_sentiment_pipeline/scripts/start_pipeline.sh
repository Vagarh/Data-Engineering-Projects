#!/bin/bash

# Script para iniciar el pipeline completo

echo "🚀 Iniciando Pipeline de Análisis de Sentimientos..."

# Verificar que el archivo .env existe
if [ ! -f .env ]; then
    echo "❌ Archivo .env no encontrado. Ejecuta setup.sh primero."
    exit 1
fi

# Verificar que Docker esté corriendo
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker no está corriendo. Por favor inicia Docker primero."
    exit 1
fi

# Levantar servicios de infraestructura primero
echo "🏗️  Iniciando servicios de infraestructura..."
docker-compose up -d zookeeper kafka clickhouse postgres redis

# Esperar a que los servicios estén listos
echo "⏳ Esperando a que los servicios estén listos..."
sleep 30

# Verificar que Kafka esté listo
echo "🔍 Verificando Kafka..."
timeout 60 bash -c 'until docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1; do sleep 2; done'

if [ $? -eq 0 ]; then
    echo "✅ Kafka está listo"
else
    echo "❌ Timeout esperando Kafka"
    exit 1
fi

# Verificar que ClickHouse esté listo
echo "🔍 Verificando ClickHouse..."
timeout 60 bash -c 'until curl -s http://localhost:8123/ping > /dev/null 2>&1; do sleep 2; done'

if [ $? -eq 0 ]; then
    echo "✅ ClickHouse está listo"
else
    echo "❌ Timeout esperando ClickHouse"
    exit 1
fi

# Crear topics de Kafka
echo "📝 Creando topics de Kafka..."
docker-compose exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic raw_tweets --partitions 3 --replication-factor 1 --if-not-exists
docker-compose exec kafka kafka-topics --create --bootstrap-server localhost:9092 --topic processed_sentiments --partitions 3 --replication-factor 1 --if-not-exists

# Levantar servicios de procesamiento
echo "⚡ Iniciando servicios de procesamiento..."
docker-compose up -d spark-master spark-worker

# Esperar a que Spark esté listo
echo "⏳ Esperando Spark..."
sleep 20

# Levantar Airflow
echo "🌪️  Iniciando Airflow..."
docker-compose up -d airflow-webserver airflow-scheduler airflow-worker

# Levantar servicios de monitoreo
echo "📊 Iniciando servicios de monitoreo..."
docker-compose up -d kafka-ui grafana

echo "✅ Todos los servicios iniciados!"
echo ""
echo "🌐 Servicios disponibles:"
echo "  - Airflow: http://localhost:8080 (admin/admin)"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Kafka UI: http://localhost:8081"
echo "  - Spark Master: http://localhost:8082"
echo ""
echo "📋 Para verificar el estado:"
echo "  docker-compose ps"
echo ""
echo "📊 Para ver logs:"
echo "  docker-compose logs -f [servicio]"
echo ""
echo "🎯 El pipeline está listo para procesar tweets!"

# Mostrar estado de los servicios
echo ""
echo "📊 Estado actual de los servicios:"
docker-compose ps