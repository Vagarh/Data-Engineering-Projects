# Pipeline de Análisis de Sentimientos en Tiempo Real

## 🎯 Objetivo

Construir un sistema de ingeniería de datos que capture, procese y analice sentimientos de redes sociales en tiempo real, proporcionando insights valiosos sobre la percepción pública de marcas, productos o eventos.

## 🏗️ Arquitectura

```
Twitter API → Kafka → Spark Streaming → ML Model → ClickHouse → Grafana
     ↓           ↓         ↓              ↓           ↓          ↓
  Ingesta   Buffer    Procesamiento   Análisis   Almacén    Visualización
```

## 🛠️ Stack Tecnológico

- **Ingesta**: Twitter API v2 + Python Producer
- **Streaming**: Apache Kafka
- **Procesamiento**: Apache Spark (Structured Streaming)
- **ML**: Transformers (BERT/RoBERTa) para análisis de sentimientos
- **Almacenamiento**: ClickHouse (OLAP optimizado para analytics)
- **Orquestación**: Apache Airflow
- **Visualización**: Grafana + ClickHouse
- **Infraestructura**: Docker Compose

## 📊 Casos de Uso

1. **Monitoreo de Marca**: Seguimiento de menciones y sentimientos sobre productos/servicios
2. **Análisis de Eventos**: Reacción pública a noticias, lanzamientos, crisis
3. **Investigación de Mercado**: Tendencias y opiniones del consumidor
4. **Detección de Crisis**: Alertas automáticas por sentimientos negativos masivos

## 🚀 Características Principales

- **Tiempo Real**: Procesamiento de tweets en ventanas de segundos
- **Escalabilidad**: Arquitectura distribuida que maneja miles de tweets/minuto
- **ML Avanzado**: Modelos pre-entrenados de última generación
- **Analytics Rápidos**: ClickHouse optimizado para consultas analíticas
- **Monitoreo**: Dashboards en tiempo real con métricas clave
- **Alertas**: Notificaciones automáticas por anomalías de sentimiento

## 📁 Estructura del Proyecto

```
social_sentiment_pipeline/
├── docker-compose.yml          # Orquestación de servicios
├── requirements.txt            # Dependencias Python
├── .env.example               # Variables de entorno
├── data/                      # Datos de ejemplo y modelos
├── src/
│   ├── producers/             # Ingesta de datos
│   ├── processors/            # Spark jobs
│   ├── models/               # Modelos ML
│   └── utils/                # Utilidades comunes
├── airflow/
│   └── dags/                 # DAGs de Airflow
├── clickhouse/
│   └── init/                 # Scripts de inicialización
├── grafana/
│   ├── dashboards/           # Dashboards predefinidos
│   └── provisioning/         # Configuración automática
└── notebooks/                # Análisis exploratorio
```

## 🎯 Métricas y KPIs

- **Volumen**: Tweets procesados por minuto/hora
- **Sentimientos**: Distribución positivo/neutral/negativo
- **Tendencias**: Evolución temporal de sentimientos
- **Temas**: Palabras clave y hashtags más mencionados
- **Influencia**: Análisis por número de seguidores
- **Geolocalización**: Sentimientos por región (si disponible)

## 🔧 Instalación y Uso

```bash
# Clonar y configurar
git clone <repo>
cd social_sentiment_pipeline
cp .env.example .env

# Configurar credenciales de Twitter API
# Editar .env con tus tokens

# Levantar servicios
docker-compose up -d

# Acceder a interfaces
# Airflow: http://localhost:8080
# Grafana: http://localhost:3000
# Kafka UI: http://localhost:8081
```

## 📈 Valor de Negocio

Este pipeline demuestra competencias clave en:
- **Ingeniería de Datos en Tiempo Real**
- **Machine Learning en Producción**
- **Arquitecturas Event-Driven**
- **Analytics de Alto Rendimiento**
- **Visualización de Datos**

Ideal para roles en empresas que necesiten monitorear su reputación online, analizar tendencias de mercado o detectar crisis de comunicación en tiempo real.