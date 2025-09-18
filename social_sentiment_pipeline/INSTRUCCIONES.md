# 🚀 Instrucciones de Instalación y Uso

## Prerrequisitos

1. **Docker Desktop** instalado y corriendo
2. **Credenciales de Twitter API v2** (Bearer Token mínimo)
3. **Git** para clonar el repositorio
4. **8GB RAM** mínimo recomendado

## 🔧 Configuración Inicial

### 1. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
copy .env.example .env

# Editar .env con tus credenciales de Twitter API
notepad .env
```

**Importante:** Debes obtener credenciales de Twitter API en https://developer.twitter.com/

### 2. Iniciar el Pipeline

```bash
# Construir y levantar todos los servicios
docker-compose up -d

# O usar el script de inicio (en Linux/Mac)
# ./scripts/start_pipeline.sh
```

### 3. Verificar Servicios

Espera 2-3 minutos y verifica que todos los servicios estén corriendo:

```bash
docker-compose ps
```

## 🌐 Acceso a Interfaces

Una vez que todos los servicios estén corriendo:

| Servicio | URL | Credenciales |
|----------|-----|--------------|
| **Airflow** | http://localhost:8080 | admin / admin |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Kafka UI** | http://localhost:8081 | - |
| **Spark Master** | http://localhost:8082 | - |

## 📊 Uso del Pipeline

### 1. Activar DAGs en Airflow

1. Ve a http://localhost:8080
2. Inicia sesión con admin/admin
3. Activa el DAG `sentiment_analysis_pipeline`
4. El pipeline comenzará a procesar tweets automáticamente

### 2. Monitorear en Grafana

1. Ve a http://localhost:3000
2. Inicia sesión con admin/admin
3. Ve a Dashboards → "Análisis de Sentimientos en Tiempo Real"
4. Observa métricas en tiempo real

### 3. Verificar Datos en ClickHouse

```bash
# Conectar a ClickHouse
docker-compose exec clickhouse clickhouse-client

# Ver datos procesados
SELECT count() FROM sentiment_db.sentiment_analysis;

# Ver últimos tweets procesados
SELECT * FROM sentiment_db.sentiment_analysis ORDER BY processing_timestamp DESC LIMIT 10;
```

## 🔍 Monitoreo y Troubleshooting

### Ver Logs de Servicios

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f kafka
docker-compose logs -f spark-master
docker-compose logs -f airflow-webserver
```

### Verificar Salud de Kafka

```bash
# Listar topics
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# Ver mensajes en topic
docker-compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic raw_tweets --from-beginning
```

### Reiniciar Servicios

```bash
# Reiniciar un servicio específico
docker-compose restart kafka

# Reiniciar todo el pipeline
docker-compose down
docker-compose up -d
```

## 📈 Análisis de Datos

### Jupyter Notebook

```bash
# Instalar dependencias localmente (opcional)
pip install jupyter pandas matplotlib seaborn clickhouse-driver

# Ejecutar notebook de análisis
jupyter notebook notebooks/exploratory_analysis.ipynb
```

### Generar Reportes

```bash
# Ejecutar reporte de métricas
docker-compose exec airflow-webserver python /opt/airflow/src/utils/metrics_reporter.py
```

## 🛑 Detener el Pipeline

```bash
# Detener servicios manteniendo datos
docker-compose down

# Detener y eliminar todos los datos
docker-compose down -v

# O usar script (Linux/Mac)
# ./scripts/stop_pipeline.sh
```

## 🎯 Casos de Uso

### 1. Monitoreo de Marca
- Configura keywords relacionadas con tu marca en `.env`
- Monitorea sentimientos en tiempo real
- Recibe alertas por sentimientos negativos masivos

### 2. Análisis de Eventos
- Cambia keywords para eventos específicos
- Analiza reacción pública en tiempo real
- Genera reportes post-evento

### 3. Investigación de Mercado
- Monitorea competidores y productos
- Analiza tendencias de sentimiento
- Identifica influencers y temas trending

## 🔧 Personalización

### Cambiar Keywords de Búsqueda

Edita el archivo `.env`:
```
SEARCH_KEYWORDS=bitcoin,ethereum,tesla,apple,google,tu_marca
```

### Ajustar Intervalos de Procesamiento

En `docker-compose.yml`, modifica variables de entorno:
```yaml
environment:
  PROCESSING_INTERVAL_SECONDS: 30  # Cambiar intervalo
  BATCH_SIZE: 100                  # Cambiar tamaño de batch
```

### Personalizar Dashboards

1. Ve a Grafana → Dashboards
2. Edita el dashboard existente
3. Agrega nuevos paneles y métricas
4. Guarda los cambios

## 📚 Recursos Adicionales

- **Twitter API Docs:** https://developer.twitter.com/en/docs/twitter-api
- **Apache Kafka:** https://kafka.apache.org/documentation/
- **Apache Spark:** https://spark.apache.org/docs/latest/
- **ClickHouse:** https://clickhouse.com/docs/
- **Grafana:** https://grafana.com/docs/

## 🆘 Soporte

Si encuentras problemas:

1. Verifica que Docker Desktop esté corriendo
2. Asegúrate de tener las credenciales de Twitter API correctas
3. Revisa los logs con `docker-compose logs -f`
4. Verifica que los puertos no estén ocupados por otros servicios
5. Reinicia el pipeline completo si es necesario

## 🎉 ¡Listo!

Tu pipeline de análisis de sentimientos en tiempo real está funcionando. Ahora puedes:

- ✅ Procesar miles de tweets por minuto
- ✅ Analizar sentimientos con ML avanzado
- ✅ Visualizar métricas en tiempo real
- ✅ Generar alertas automáticas
- ✅ Crear reportes de análisis

¡Perfecto para demostrar habilidades de ingeniería de datos moderna!