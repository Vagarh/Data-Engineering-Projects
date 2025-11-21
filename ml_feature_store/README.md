# ML Feature Store

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Feast](https://img.shields.io/badge/feast-0.34+-green.svg)](https://feast.dev/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

> Plataforma centralizada para gestión de features de Machine Learning con soporte para serving batch y online.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ML FEATURE STORE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐            │
│  │ Data Sources │────▶│   Feature    │────▶│   Feature    │            │
│  │ (Raw Data)   │     │ Engineering  │     │   Registry   │            │
│  │              │     │   Pipeline   │     │   (Feast)    │            │
│  └──────────────┘     └──────────────┘     └──────┬───────┘            │
│                                                    │                     │
│                     ┌──────────────────────────────┼──────────────────┐ │
│                     │                              │                  │ │
│                     ▼                              ▼                  ▼ │
│  ┌──────────────────────┐   ┌──────────────────────┐   ┌────────────┐ │
│  │    Offline Store     │   │    Online Store      │   │  Feature   │ │
│  │    (Parquet/S3)      │   │      (Redis)         │   │  Serving   │ │
│  │                      │   │                      │   │  (FastAPI) │ │
│  │  - Batch Training    │   │  - Real-time Inf.    │   │            │ │
│  │  - Historical Data   │   │  - Low Latency       │   │  - REST    │ │
│  │  - Point-in-time     │   │  - Feature Vectors   │   │  - gRPC    │ │
│  └──────────────────────┘   └──────────────────────┘   └────────────┘ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Apache Airflow                               │   │
│  │              (Feature Pipeline Orchestration)                    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Estructura del Proyecto

```
ml_feature_store/
├── src/
│   ├── features/                  # Feature engineering
│   │   ├── __init__.py
│   │   ├── user_features.py       # User-related features
│   │   ├── product_features.py    # Product features
│   │   └── transaction_features.py
│   ├── api/                       # Feature serving API
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI application
│   │   └── schemas.py            # Pydantic schemas
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── feature_repo/                  # Feast feature repository
│   ├── feature_store.yaml        # Feast configuration
│   ├── user_features.py          # Feature definitions
│   └── data/                     # Sample data
├── airflow/
│   └── dags/
│       └── feature_pipeline_dag.py
├── tests/
│   ├── __init__.py
│   └── test_features.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Stack Tecnológico

| Componente | Tecnología | Descripción |
|------------|------------|-------------|
| Feature Store | Feast | Registry y serving de features |
| Online Store | Redis | Serving de baja latencia |
| Offline Store | Parquet/PostgreSQL | Almacenamiento histórico |
| API | FastAPI | Serving HTTP/REST |
| Orquestación | Apache Airflow | Pipelines de features |
| Contenedores | Docker | Deployment |

## Quick Start

### 1. Configuración Inicial

```bash
# Clonar y navegar al proyecto
cd ml_feature_store

# Copiar configuración
cp .env.example .env

# Levantar servicios
docker-compose up -d
```

### 2. Inicializar Feature Store

```bash
# Aplicar definiciones de features
cd feature_repo
feast apply

# Materializar features al online store
feast materialize-incremental $(date +%Y-%m-%dT%H:%M:%S)
```

### 3. Usar la API

```bash
# Obtener features online
curl -X POST "http://localhost:8000/features/online" \
  -H "Content-Type: application/json" \
  -d '{"entity_ids": ["user_1", "user_2"], "feature_names": ["user_features:age", "user_features:total_purchases"]}'

# Health check
curl http://localhost:8000/health
```

## Features Disponibles

### User Features

| Feature | Tipo | Descripción |
|---------|------|-------------|
| `user_age` | INT | Edad del usuario |
| `user_total_purchases` | FLOAT | Total de compras históricas |
| `user_avg_purchase_value` | FLOAT | Valor promedio de compra |
| `user_days_since_last_purchase` | INT | Días desde última compra |
| `user_purchase_frequency` | FLOAT | Frecuencia de compra (compras/mes) |

### Product Features

| Feature | Tipo | Descripción |
|---------|------|-------------|
| `product_price` | FLOAT | Precio del producto |
| `product_category` | STRING | Categoría del producto |
| `product_avg_rating` | FLOAT | Rating promedio |
| `product_total_sales` | INT | Ventas totales |

### Transaction Features

| Feature | Tipo | Descripción |
|---------|------|-------------|
| `transaction_amount` | FLOAT | Monto de la transacción |
| `transaction_hour` | INT | Hora de la transacción |
| `transaction_day_of_week` | INT | Día de la semana |
| `transaction_is_weekend` | BOOL | Es fin de semana |

## Desarrollo

### Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Ejecutar Tests

```bash
pytest tests/ -v
```

### Agregar Nuevas Features

1. Definir la feature en `feature_repo/`:

```python
from feast import Entity, Feature, FeatureView, FileSource, ValueType

# Definir entidad
user = Entity(name="user_id", value_type=ValueType.STRING)

# Definir source
user_source = FileSource(
    path="data/user_features.parquet",
    timestamp_field="event_timestamp"
)

# Definir feature view
user_features = FeatureView(
    name="user_features",
    entities=["user_id"],
    features=[
        Feature(name="age", dtype=ValueType.INT64),
        Feature(name="total_purchases", dtype=ValueType.FLOAT),
    ],
    source=user_source,
)
```

2. Aplicar cambios:

```bash
feast apply
```

3. Materializar al online store:

```bash
feast materialize-incremental $(date +%Y-%m-%dT%H:%M:%S)
```

## Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/features/online` | Obtener features online |
| POST | `/features/offline` | Obtener features históricas |
| GET | `/features/list` | Listar features disponibles |
| GET | `/entities` | Listar entidades |

## Monitoreo

El proyecto incluye métricas de Prometheus:

- `feature_serving_latency`: Latencia de serving
- `feature_requests_total`: Total de requests
- `feature_errors_total`: Errores en serving
- `online_store_size`: Tamaño del online store

Acceder a métricas: `http://localhost:8000/metrics`

## Licencia

MIT License - Ver [LICENSE](../LICENSE) para más detalles.
