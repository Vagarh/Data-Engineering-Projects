# Proyecto: Análisis de Tendencias de Videos en YouTube

Este proyecto implementa un pipeline de datos automatizado para ingerir, procesar y almacenar datos de videos populares de YouTube, utilizando un stack tecnológico moderno y contenerizado con Docker.

## Objetivo del Negocio

Construir un pipeline de datos automatizado que ingiera diariamente datos de los videos más populares de YouTube por región, los procese para extraer métricas clave y los almacene en un Data Warehouse para ser analizados por un equipo de Business Intelligence (BI).

## Arquitectura

```mermaid
graph TD
    A[API de YouTube / Kaggle Dataset] --> B(Script de Ingesta en Python);
    B --> C[Data Lake (MinIO / Staging local)];
    C -- Carga Raw Data --> D{ETL/ELT Pipeline};
    D -- Orquestado por --> E[Apache Airflow];
    subgraph "Proceso de Transformación"
        D --> F(dbt - Data Build Tool);
    end
    F -- Transforma y Modela --> G[Data Warehouse (PostgreSQL)];
    G -- Datos Limpios --> H[Herramienta de BI (Metabase / Power BI)];

    subgraph "Entorno Contenerizado con Docker"
        B;
        C;
        E;
        G;
        H;
    end

    I[Calidad de Datos (Great Expectations / dbt test)] -- Valida --> F;
    E -- Dispara --> B;
```

## Stack Tecnológico

| Componente                | Tecnología                                                                   | Propósito                                                                      |
| ------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **Fuente de Datos** | Kaggle Dataset: [Trending YouTube Video Statistics](https://www.kaggle.com/datasets/datasnaek/youtube-new) | Simula una fuente de datos real con archivos CSV por país.                     |
| **Ingesta** | Python (`requests`, `pandas`, `s3fs`)                                                | Script para descargar los datos y depositarlos en el Data Lake.                |
| **Data Lake** | MinIO                                                                        | Almacenamiento de objetos compatible con S3 para los datos crudos (raw).       |
| **Contenerización** | **Docker & Docker Compose** | Para crear un entorno de desarrollo reproducible y aislado.                    |
| **Orquestación** | **Apache Airflow** | Para automatizar, programar y monitorear el pipeline completo (el DAG).        |
| **Data Warehouse** | **PostgreSQL** | Base de datos relacional para almacenar los datos limpios y modelados.         |
| **Transformación (ELT)** | **dbt (Data Build Tool)** | Para transformar los datos dentro del Data Warehouse usando SQL.               |
| **Calidad de Datos** | **dbt tests** | Para validar la integridad y calidad de los modelos de datos.                  |
| **Visualización (Opcional)** | Metabase / Superset                                                          | Herramienta de BI de código abierto para conectar al DWH y crear dashboards.   |

## Cómo Ejecutar el Proyecto

Sigue estos pasos para levantar y ejecutar el pipeline de datos:

1.  **Clonar el Repositorio:**
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd youtube_trends_pipeline
    ```
    *(Nota: Si ya estás en el directorio `youtube_trends_pipeline`, puedes omitir el `cd`.)*

2.  **Levantar el Entorno con Docker Compose:**
    Asegúrate de tener Docker Desktop (o Docker Engine) instalado y en ejecución. Desde la raíz del proyecto (`youtube_trends_pipeline/`), ejecuta:
    ```bash
    docker-compose up -d
    ```
    Esto construirá las imágenes (si es la primera vez) y levantará todos los servicios en segundo plano: PostgreSQL, MinIO, y los componentes de Airflow (webserver, scheduler, etc.).

3.  **Acceder a la Interfaz de Usuario de Airflow:**
    Una vez que los contenedores estén en funcionamiento (puede tardar unos minutos en inicializarse Airflow), abre tu navegador y navega a:
    ```
    http://localhost:8080
    ```
    Las credenciales de inicio de sesión por defecto son:
    *   **Usuario:** `admin`
    *   **Contraseña:** `admin`

4.  **Configurar Conexiones en Airflow:**
    Dentro de la UI de Airflow, ve a `Admin` -> `Connections` y crea las siguientes conexiones:

    *   **Conexión S3 para MinIO:**
        *   **Conn Id:** `minio_s3_conn`
        *   **Conn Type:** `S3`
        *   **Host:** `http://minio:9000`
        *   **Login (AWS Access Key ID):** `minioadmin`
        *   **Password (AWS Secret Access Key):** `minioadmin`
        *   **Extra:**
            ```json
            {
                "aws_access_key_id": "minioadmin",
                "aws_secret_access_key": "minioadmin",
                "endpoint_url": "http://minio:9000",
                "region_name": "us-east-1",
                "s3_url": "http://minio:9000"
            }
            ```

    *   **Conexión PostgreSQL para Data Warehouse:**
        *   **Conn Id:** `postgres_dwh_conn`
        *   **Conn Type:** `Postgres`
        *   **Host:** `postgres-db`
        *   **Port:** `5432`
        *   **Schema (Database):** `youtube_dwh`
        *   **Login:** `airflow_user`
        *   **Password:** `airflow_pass`

5.  **Activar y Ejecutar el DAG:**
    En la UI de Airflow, busca el DAG llamado `youtube_daily_pipeline`. Actívalo (toggle switch) y luego puedes disparar una ejecución manual haciendo clic en el botón de "Play" o "Trigger DAG".

6.  **Verificar los Datos Transformados en PostgreSQL:**
    Puedes conectarte a la base de datos PostgreSQL (`postgres-db`) usando un cliente como `psql` o `DBeaver` con las siguientes credenciales:
    *   **Host:** `localhost` (desde tu máquina local) o `postgres-db` (desde otro contenedor Docker)
    *   **Port:** `5432`
    *   **Database:** `youtube_dwh`
    *   **User:** `airflow_user`
    *   **Password:** `airflow_pass`

    Una vez conectado, puedes consultar las tablas en el esquema `marts` (ej: `SELECT * FROM marts.fct_video_trends;`) para ver los datos transformados por dbt.

## Limpieza del Entorno

Para detener y eliminar todos los contenedores y volúmenes de Docker asociados con este proyecto, ejecuta desde la raíz del proyecto:
```bash
docker-compose down -v
```
Esto es útil para limpiar tu sistema y empezar de nuevo.

---

Este proyecto demuestra habilidades clave en arquitectura de datos, automatización, calidad de datos y buenas prácticas de DevOps, esenciales para un ingeniero de datos competente.
