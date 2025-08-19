
# Portafolio de Proyectos de Ingeniería de Datos

¡Bienvenido a mi portafolio de proyectos de ingeniería de datos! Este repositorio contiene una colección de pipelines y sistemas de datos que demuestran mis habilidades en la construcción de soluciones de datos robustas, escalables y automatizadas.

---

## Proyectos

### 1. Data Lake Unificado (Batch + Streaming)

- **Directorio:** [`./unified_data_lake_project/`](./unified_data_lake_project/)

#### Descripción

Este proyecto implementa una plataforma de datos completa que ingiere datos de dos fuentes distintas: un flujo de eventos en **tiempo real** (simulado desde una API de criptomonedas) y cargas **batch** de archivos CSV históricos. Ambos flujos de datos se procesan y se integran en una única tabla Delta Lake, creando una fuente de verdad unificada y permitiendo análisis completos.

La idempotencia se garantiza en el pipeline batch mediante operaciones `MERGE`, y todo el entorno es reproducible y se gestiona con Docker.

#### Stack Tecnológico
- **Procesamiento:** Apache Spark (Structured Streaming y Batch)
- **Almacenamiento:** Delta Lake sobre un Data Lake (simulado en disco local)
- **Mensajería/Streaming:** Apache Kafka
- **Orquestación:** Apache Airflow
- **Contenerización:** Docker & Docker Compose

---

### 2. Pipeline ELT de Tendencias de YouTube con dbt

- **Directorio:** [`./youtube_trends_pipeline/`](./youtube_trends_pipeline/)

#### Descripción

Este proyecto implementa un pipeline de datos siguiendo el paradigma **ELT (Extract, Load, Transform)**. El sistema extrae datos sobre las tendencias de YouTube, los carga en un Data Warehouse (PostgreSQL) y luego utiliza **dbt (Data Build Tool)** para ejecutar transformaciones SQL modelando los datos crudos en tablas analíticas limpias y listas para el consumo (por ejemplo, para un dashboard de BI).

El pipeline está completamente orquestado con Apache Airflow.

#### Stack Tecnológico
- **Transformación:** dbt (Data Build Tool)
- **Orquestación:** Apache Airflow
- **Data Warehouse:** PostgreSQL
- **Contenerización:** Docker & Docker Compose
- **CI/CD:** GitHub Actions (para linting de Python)
