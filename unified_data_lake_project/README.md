
# Proyecto: Data Lake Unificado con Fuentes Batch y Streaming

Este proyecto implementa una plataforma de datos completa para ingerir, procesar y unificar datos tanto de fuentes batch (archivos CSV) como de fuentes en tiempo real (simuladas a través de un productor de Kafka).

La arquitectura utiliza un stack tecnológico moderno y estándar en la industria:

- **Orquestación:** Apache Airflow
- **Procesamiento:** Apache Spark
- **Mensajería/Streaming:** Apache Kafka
- **Base de Datos (Metadatos Airflow):** PostgreSQL
- **Contenerización:** Docker

## Cómo Empezar

1.  **Prerrequisitos:**
    *   Tener Docker y Docker Compose instalados en su máquina.

2.  **Levantar el Entorno:**
    *   Clonar este repositorio.
    *   Navegar al directorio raíz del proyecto.
    *   Ejecutar el siguiente comando para construir y levantar todos los servicios:

    ```bash
    docker-compose up -d
    ```

3.  **Acceder a los Servicios:**
    *   **Airflow UI:** `http://localhost:8080` (usuario: `admin`, contraseña: `admin`)
    *   **Spark Master UI:** `http://localhost:8081`
