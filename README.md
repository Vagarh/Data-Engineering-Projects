# Data Engineering Projects Portfolio

[![CI/CD Pipeline](https://github.com/Vagarh/Data-Engineering-Projects/actions/workflows/ci.yml/badge.svg)](https://github.com/Vagarh/Data-Engineering-Projects/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> Portafolio profesional de proyectos de ingeniería de datos que demuestran habilidades en pipelines ETL/ELT, streaming en tiempo real, Machine Learning en producción y arquitecturas de datos modernas.

---

## Tabla de Contenidos

- [Arquitectura General](#arquitectura-general)
- [Proyectos](#proyectos)
  - [Data Lake Unificado](#1-data-lake-unificado-batch--streaming)
  - [Pipeline ELT YouTube](#2-pipeline-elt-de-tendencias-de-youtube)
  - [Análisis de Sentimientos](#3-pipeline-de-análisis-de-sentimientos-en-tiempo-real)
  - [Pipeline de Seguridad SIEM](#4-pipeline-de-análisis-de-logs-y-seguridad)
  - [Feature Store para ML](#5-feature-store-para-ml)
- [Stack Tecnológico](#stack-tecnológico)
- [Estructura del Repositorio](#estructura-del-repositorio)
- [Quick Start](#quick-start)
- [Testing](#testing)
- [CI/CD](#cicd)
- [Contribución](#contribución)
- [Licencia](#licencia)

---

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA ENGINEERING PORTFOLIO                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   Data Sources  │  │   Data Sources  │  │   Data Sources  │             │
│  │  ─────────────  │  │  ─────────────  │  │  ─────────────  │             │
│  │  • APIs         │  │  • Twitter API  │  │  • System Logs  │             │
│  │  • CSV Files    │  │  • Social Media │  │  • Firewall     │             │
│  │  • Streaming    │  │                 │  │  • IDS/IPS      │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
│           │                    │                    │                       │
│           ▼                    ▼                    ▼                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        INGESTION LAYER                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │   Kafka     │  │  Filebeat   │  │  Logstash   │                 │   │
│  │  │  Producers  │  │  Collectors │  │  Pipelines  │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       PROCESSING LAYER                              │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │   Apache    │  │   Apache    │  │    dbt      │                 │   │
│  │  │   Spark     │  │   Storm     │  │ Transforms  │                 │   │
│  │  │ (Streaming) │  │  (Events)   │  │   (SQL)     │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        STORAGE LAYER                                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │ Delta Lake  │  │ ClickHouse  │  │Elasticsearch│                 │   │
│  │  │  (ACID)     │  │   (OLAP)    │  │  (Search)   │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      ORCHESTRATION & ML                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │   Apache    │  │  ML Models  │  │  Feature    │                 │   │
│  │  │   Airflow   │  │(BERT, LSTM) │  │   Store     │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      VISUALIZATION LAYER                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │   Grafana   │  │   Kibana    │  │  Dashboards │                 │   │
│  │  │ (Metrics)   │  │  (Logs)     │  │   (BI)      │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Proyectos

### 1. Data Lake Unificado (Batch + Streaming)

📁 **Directorio:** [`./unified_data_lake_project/`](./unified_data_lake_project/)

Plataforma de datos completa que ingiere datos de dos fuentes distintas: un flujo de eventos en **tiempo real** (simulado desde una API de criptomonedas) y cargas **batch** de archivos CSV históricos.

```
┌──────────────┐     ┌──────────────┐
│  Crypto API  │     │  CSV Files   │
│  (Real-time) │     │  (Batch)     │
└──────┬───────┘     └──────┬───────┘
       │                    │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│    Kafka     │     │    Spark     │
│   Producer   │     │   Batch Job  │
└──────┬───────┘     └──────┬───────┘
       │                    │
       ▼                    ▼
┌──────────────────────────────────┐
│         Delta Lake (MERGE)       │
│     Unified Source of Truth      │
└──────────────────────────────────┘
```

**Stack:** Apache Spark | Delta Lake | Apache Kafka | Apache Airflow | Docker

**Características:**
- Procesamiento batch y streaming unificado
- Idempotencia mediante operaciones MERGE
- Arquitectura Delta Lake para ACID transactions
- Orquestación completa con Airflow

---

### 2. Pipeline ELT de Tendencias de YouTube

📁 **Directorio:** [`./youtube_trends_pipeline/`](./youtube_trends_pipeline/)

Pipeline de datos ELT que extrae datos sobre las tendencias de YouTube, los carga en PostgreSQL y utiliza **dbt** para transformaciones SQL.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  YouTube     │────▶│  PostgreSQL  │────▶│     dbt      │
│  Trends API  │     │  (Raw Data)  │     │  (Transform) │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │   Analytics  │
                                          │    Tables    │
                                          └──────────────┘
```

**Stack:** dbt | Apache Airflow | PostgreSQL | GitHub Actions | Docker

**Características:**
- Paradigma ELT moderno con dbt
- Tests de calidad de datos integrados
- CI/CD con GitHub Actions
- Modelos staging y marts organizados

---

### 3. Pipeline de Análisis de Sentimientos en Tiempo Real

📁 **Directorio:** [`./social_sentiment_pipeline/`](./social_sentiment_pipeline/)

Sistema que captura, procesa y analiza sentimientos de redes sociales en tiempo real usando modelos de Machine Learning.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Twitter     │────▶│    Kafka     │────▶│    Spark     │
│    API       │     │   Streams    │     │  Streaming   │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │ BERT/RoBERTa │
                                          │  Sentiment   │
                                          └──────┬───────┘
                                                  │
                     ┌────────────────────────────┼────────────────────────────┐
                     ▼                            ▼                            ▼
              ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
              │  ClickHouse  │            │   Grafana    │            │   Alerts     │
              │   (OLAP)     │            │  Dashboards  │            │   System     │
              └──────────────┘            └──────────────┘            └──────────────┘
```

**Stack:** Twitter API | Kafka | Spark Streaming | Transformers (BERT) | ClickHouse | Grafana

**Características:**
- Procesamiento en ventanas de segundos
- Modelos NLP de última generación
- Analytics OLAP con ClickHouse
- Alertas automáticas por anomalías

---

### 4. Pipeline de Análisis de Logs y Seguridad

📁 **Directorio:** [`./security_logs_pipeline/`](./security_logs_pipeline/)

Sistema SIEM completo que procesa logs de seguridad en tiempo real, detecta amenazas usando ML y genera alertas automáticas.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Filebeat    │────▶│   Logstash   │────▶│    Kafka     │
│ (Collectors) │     │  (Pipeline)  │     │   Topics     │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │ ML Detection │
                                          │ (Isolation   │
                                          │  Forest/LSTM)│
                                          └──────┬───────┘
                                                  │
                     ┌────────────────────────────┼────────────────────────────┐
                     ▼                            ▼                            ▼
              ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
              │Elasticsearch │            │    Kibana    │            │   Alerts     │
              │   (SIEM)     │            │ (Dashboard)  │            │(Slack/Email) │
              └──────────────┘            └──────────────┘            └──────────────┘
```

**Stack:** ELK Stack | Apache Storm | Scikit-learn | TensorFlow | Wazuh | PagerDuty

**Características:**
- Detección en tiempo real (latencia < 30s)
- ML para detección de anomalías
- Compliance: PCI-DSS, HIPAA, SOX, GDPR
- Análisis forense integrado

---

### 5. Feature Store para ML

📁 **Directorio:** [`./ml_feature_store/`](./ml_feature_store/)

Plataforma centralizada para gestión de features de Machine Learning, permitiendo reutilización, versionado y serving en tiempo real y batch.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Data Sources │────▶│   Feature    │────▶│   Feature    │
│ (Raw Data)   │     │ Engineering  │     │   Registry   │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                     ┌────────────────────────────┼────────────────────────────┐
                     ▼                            ▼                            ▼
              ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
              │ Offline Store│            │ Online Store │            │   Feature    │
              │  (Parquet)   │            │   (Redis)    │            │   Serving    │
              └──────────────┘            └──────────────┘            └──────────────┘
                     │                            │                            │
                     ▼                            ▼                            ▼
              ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
              │    Batch     │            │  Real-time   │            │  ML Models   │
              │   Training   │            │  Inference   │            │  (Serving)   │
              └──────────────┘            └──────────────┘            └──────────────┘
```

**Stack:** Feast | Redis | PostgreSQL | Apache Airflow | FastAPI | Docker

**Características:**
- Registry centralizado de features
- Serving batch y online
- Versionado y linaje de features
- API REST para inferencia en tiempo real

---

## Stack Tecnológico

### Procesamiento & Streaming
| Tecnología | Uso |
|------------|-----|
| Apache Spark | Batch & Streaming Processing |
| Apache Kafka | Event Streaming |
| Apache Storm | Real-time Event Processing |
| dbt | SQL Transformations |

### Almacenamiento
| Tecnología | Uso |
|------------|-----|
| Delta Lake | ACID Data Lake |
| PostgreSQL | Data Warehouse |
| ClickHouse | OLAP Analytics |
| Elasticsearch | Search & SIEM |
| Redis | Feature Store Online |

### Machine Learning
| Tecnología | Uso |
|------------|-----|
| Transformers | NLP (BERT/RoBERTa) |
| Scikit-learn | Anomaly Detection |
| TensorFlow | Deep Learning (LSTM) |
| Feast | Feature Store |

### Orquestación & Infraestructura
| Tecnología | Uso |
|------------|-----|
| Apache Airflow | Workflow Orchestration |
| Docker | Containerization |
| GitHub Actions | CI/CD |
| Grafana/Kibana | Monitoring & Visualization |

---

## Estructura del Repositorio

```
Data-Engineering-Projects/
├── .github/
│   └── workflows/
│       └── ci.yml                    # CI/CD Pipeline
├── unified_data_lake_project/        # Proyecto 1: Data Lake
│   ├── producer/
│   ├── spark/
│   ├── airflow/
│   ├── tests/
│   └── docker-compose.yml
├── youtube_trends_pipeline/          # Proyecto 2: YouTube ELT
│   ├── dbt_youtube/
│   ├── dags/
│   ├── scripts/
│   ├── tests/
│   └── docker-compose.yml
├── social_sentiment_pipeline/        # Proyecto 3: Sentiment Analysis
│   ├── src/
│   ├── airflow/
│   ├── grafana/
│   ├── tests/
│   └── docker-compose.yml
├── security_logs_pipeline/           # Proyecto 4: SIEM
│   ├── src/
│   ├── airflow/
│   ├── config/
│   ├── tests/
│   └── docker-compose.yml
├── ml_feature_store/                 # Proyecto 5: Feature Store
│   ├── src/
│   ├── feature_repo/
│   ├── api/
│   ├── tests/
│   └── docker-compose.yml
├── tests/                            # Tests globales
│   └── integration/
├── docs/                             # Documentación adicional
├── scripts/                          # Scripts de utilidad
├── requirements-dev.txt              # Dependencias de desarrollo
└── README.md
```

---

## Quick Start

### Pre-requisitos

- Docker & Docker Compose
- Python 3.9+
- Make (opcional)

### Ejecutar un proyecto

```bash
# Clonar el repositorio
git clone https://github.com/Vagarh/Data-Engineering-Projects.git
cd Data-Engineering-Projects

# Elegir un proyecto y levantar
cd unified_data_lake_project
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Configuración de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar variables de entorno
nano .env
```

---

## Testing

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Ejecutar todos los tests
pytest

# Ejecutar tests con coverage
pytest --cov=. --cov-report=html

# Ejecutar tests de un proyecto específico
pytest unified_data_lake_project/tests/

# Linting
black . --check
flake8 .
mypy .
```

---

## CI/CD

El pipeline de CI/CD ejecuta automáticamente en cada push y pull request:

- **Linting:** Black, Flake8, MyPy
- **Testing:** Pytest con coverage
- **Security:** Bandit security scan
- **Docker:** Build validation

Ver [`.github/workflows/ci.yml`](.github/workflows/ci.yml) para detalles.

---

## Contribución

1. Fork el repositorio
2. Crear una rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Add nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

---

## Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## Contacto

- **GitHub:** [@Vagarh](https://github.com/Vagarh)

---

<p align="center">
  <i>Construido con pasión por la ingeniería de datos</i>
</p>
