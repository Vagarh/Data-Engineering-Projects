
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

---

### 3. Pipeline de Análisis de Sentimientos en Tiempo Real

- **Directorio:** [`./social_sentiment_pipeline/`](./social_sentiment_pipeline/)

#### Descripción

Sistema completo de ingeniería de datos que captura, procesa y analiza sentimientos de redes sociales en tiempo real. El pipeline ingesta tweets usando la API de Twitter, aplica modelos de Machine Learning para análisis de sentimientos, y proporciona dashboards en tiempo real con métricas y alertas automáticas.

Este proyecto demuestra competencias avanzadas en streaming de datos, ML en producción, y arquitecturas event-driven para casos de uso de monitoreo de marca y análisis de tendencias sociales.

#### Stack Tecnológico
- **Ingesta:** Twitter API v2 + Python Producer
- **Streaming:** Apache Kafka + Spark Structured Streaming
- **ML:** Transformers (BERT/RoBERTa) para análisis de sentimientos
- **Almacenamiento:** ClickHouse (OLAP optimizado)
- **Orquestación:** Apache Airflow
- **Visualización:** Grafana + Dashboards en tiempo real
- **Contenerización:** Docker & Docker Compose

#### Características Destacadas
- **Tiempo Real:** Procesamiento de tweets en ventanas de segundos
- **ML Avanzado:** Modelos pre-entrenados de última generación
- **Analytics Rápidos:** ClickHouse optimizado para consultas analíticas
- **Monitoreo:** Dashboards con métricas de sentimiento, engagement y trending topics
- **Alertas:** Notificaciones automáticas por anomalías de sentimiento

---

### 4. Pipeline de Análisis de Logs y Seguridad

- **Directorio:** [`./security_logs_pipeline/`](./security_logs_pipeline/)

#### Descripción

Sistema completo de Security Information and Event Management (SIEM) que procesa logs de seguridad en tiempo real, detecta amenazas usando Machine Learning, y genera alertas automáticas para respuesta rápida a incidentes. El pipeline combina ingeniería de datos con ciberseguridad para crear una solución robusta de monitoreo de seguridad.

Este proyecto demuestra competencias críticas en detección de amenazas, análisis forense, y cumplimiento de normativas de seguridad (PCI-DSS, HIPAA, SOX, GDPR).

#### Stack Tecnológico
- **Colección:** Filebeat + Logstash (ELK Stack)
- **Streaming:** Apache Kafka + Apache Storm
- **Machine Learning:** Scikit-learn + Isolation Forest + LSTM
- **SIEM:** Elasticsearch + Kibana + Wazuh
- **Alertas:** ElastAlert + Slack/Email/PagerDuty
- **Orquestación:** Apache Airflow
- **Infraestructura:** Docker Compose + Kubernetes ready

#### Características Destacadas
- **Detección en Tiempo Real:** Procesamiento con latencia < 30 segundos
- **ML para Seguridad:** Isolation Forest y análisis de anomalías
- **Alertas Inteligentes:** Reducción de falsos positivos con correlación
- **Compliance:** Cumplimiento automático de normativas de seguridad
- **Investigación Forense:** Herramientas avanzadas para análisis de incidentes
- **Escalabilidad:** Arquitectura distribuida para alto volumen de logs

#### Casos de Uso
- **Detección de Intrusiones:** Análisis de logs de firewall y IDS/IPS
- **Monitoreo Web:** Detección de ataques SQL injection, XSS, CSRF
- **Análisis de Autenticación:** Detección de ataques de fuerza bruta
- **Comportamiento Anómalo:** Identificación de actividad sospechosa de usuarios
