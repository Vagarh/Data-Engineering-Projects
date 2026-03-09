# 🚦 End-to-End Analytics Pipeline: Incidentes Viales (Colombia)

Este proyecto es una solución completa de Ingeniería de Datos que automatiza la extracción, transformación, almacenamiento y visualización de datos abiertos gubernamentales sobre accidentes de tránsito en Colombia (Medellín).

## 🏗️ Arquitectura del Sistema

El proyecto utiliza un stack tecnológico moderno y estándar en la industria:

1.  **Ingestión (API Socrata)**: Consumo de datos en tiempo real desde el portal de Datos Abiertos Colombia.
2.  **Orquestación (Apache Airflow)**: Pipeline automatizado (ETL) que gestiona las tareas de extracción, limpieza y carga.
3.  **Almacenamiento (PostgreSQL)**: Base de Datos relacional configurada como un Data Warehouse para persistencia masiva.
4.  **Visualización (Streamlit)**: Dashboard interactivo con mapas de calor, KPIs y análisis estadístico.
5.  **Infraestructura (Docker)**: Todo el ecosistema está contenedorizado para garantizar portabilidad y facilidad de despliegue.

## 🚀 Cómo Ejecutar el Proyecto

### Requisitos Previos
*   Instalar **Docker Desktop**.
*   Tener al menos 4GB de RAM dedicados a Docker (Airflow es robusto).

### Pasos para iniciar
1.  Clona este repositorio o entra en la carpeta del proyecto.
2.  Ejecuta el siguiente comando para construir e iniciar todos los servicios:
    ```bash
    docker-compose up -d
    ```
3.  **Acceso a los servicios:**
    *   **Airflow (ETL):** [http://localhost:8080](http://localhost:8080) (Usuario/Password: `admin` / `admin`).
    *   **Dashboard (Streamlit):** [http://localhost:8501](http://localhost:8501).
    *   **PostgreSQL:** `localhost:5432` (Base de datos: `dw_portafolio`).

## 🛠️ Flujo de Datos (ETL)

El DAG `open_data_etl_accidentes` en Airflow realiza las siguientes acciones de forma diaria:
*   **Extract**: Obtiene los últimos registros de la API pública.
*   **Transform**: Limpia tipos de datos, filtra registros sin coordenadas y estandariza nombres de columnas.
*   **Load**: Inserta los datos en PostgreSQL utilizando una estrategia de *Upsert* (ON CONFLICT DO NOTHING) para evitar duplicados.

## 📊 Dashboard de Visualización
El dashboard permite filtrar por **Comuna**, **Gravedad de accidente** y visualizar:
*   **KPIs**: Cantidad total, zona más crítica, clase de accidente predominante.
*   **Mapas**: Localización geoespacial detallada de los incidentes.
*   **Gráficos**: Distribución de accidentes por gravedad y clase (choques, caídas, etc).

---
*Proyecto desarrollado para portafolio de Ingeniería de Datos.*
