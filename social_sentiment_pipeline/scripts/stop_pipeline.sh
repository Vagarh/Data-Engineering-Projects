#!/bin/bash

# Script para detener el pipeline completo

echo "🛑 Deteniendo Pipeline de Análisis de Sentimientos..."

# Detener todos los servicios
echo "📊 Deteniendo servicios de monitoreo..."
docker-compose stop grafana kafka-ui

echo "🌪️  Deteniendo Airflow..."
docker-compose stop airflow-webserver airflow-scheduler airflow-worker

echo "⚡ Deteniendo servicios de procesamiento..."
docker-compose stop spark-master spark-worker

echo "🏗️  Deteniendo servicios de infraestructura..."
docker-compose stop kafka zookeeper clickhouse postgres redis

echo "✅ Todos los servicios detenidos!"

# Opción para limpiar completamente
read -p "¿Deseas eliminar también los volúmenes de datos? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Eliminando volúmenes..."
    docker-compose down -v
    echo "✅ Volúmenes eliminados"
else
    echo "📦 Volúmenes conservados"
    docker-compose down
fi

echo ""
echo "🎯 Pipeline detenido completamente"
echo "💡 Para reiniciar: ./scripts/start_pipeline.sh"