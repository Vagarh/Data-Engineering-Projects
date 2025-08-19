Proyecto: Data Lake Unificado con Fuentes Batch y Streaming
1. Objetivo Principal
Construir una plataforma de datos escalable que centralice información de dos tipos de fuentes distintas:

Fuentes Batch: Cargas masivas de datos históricos (archivos CSV) que representan el estado del negocio hasta un punto en el tiempo.
Fuentes Streaming: Flujos continuos de eventos en tiempo real desde una API (ej. cotizaciones de criptomonedas, interacciones en redes sociales) que capturan el estado más reciente.
El resultado final será una única tabla de datos (single source of truth), optimizada y particionada, que combine ambas vistas para permitir análisis completos y actualizados.

2. Arquitectura Propuesta
Utilizaremos el stack tecnológico sugerido, que es un estándar de facto en la industria para este tipo de soluciones.

(Este es un diagrama conceptual para ilustrar el flujo)

Desglose de Componentes:

Capa de Almacenamiento (Storage Layer): AWS S3 o Google Cloud Storage (GCS)

Rol: Será nuestro Data Lake. Almacenará los datos en diferentes estados: crudos (raw), procesados y optimizados.
Por qué? Es un almacenamiento de objetos virtualmente infinito, de bajo costo, altamente durable y desacoplado del cómputo. Esto nos permite escalar ambos de forma independiente.
Estructura de Carpetas (Buckets):
s3://mi-data-lake/raw/batch/: Donde aterrizarán los archivos CSV históricos.
s3://mi-data-lake/raw/streaming/: (Opcional) Checkpoints del streaming.
s3://mi-data-lake/processed/unified-events/: Nuestra tabla final en formato Delta Lake.
Capa de Ingesta (Ingestion Layer)

Batch (Archivos CSV):
Proceso: Un script o proceso automatizado cargará los archivos CSV directamente a la zona raw/batch/ de nuestro Data Lake.
Streaming (API en tiempo real):
Componente: Apache Kafka (o Google Pub/Sub).
Rol: Actúa como un "buffer" o intermediario para los datos en tiempo real. Un script (productor) leerá de la API de Binance/Twitter y publicará cada evento como un mensaje en un topic de Kafka.
Por qué? Desacopla la fuente (API) del procesador (Spark). Si Spark se cae, Kafka retiene los mensajes para que no se pierdan datos. Permite que múltiples sistemas consuman los mismos datos en tiempo real.
Capa de Procesamiento (Processing Layer): Apache Spark

Rol: Es el motor de cómputo unificado. Se encargará de leer los datos crudos (tanto batch como streaming), transformarlos y escribirlos en la tabla final.
Por qué? Spark tiene APIs para procesar tanto datos en batch (DataFrames) como en streaming (Structured Streaming) con un código muy similar, lo que simplifica el desarrollo.
Capa de Orquestación (Orchestration Layer): Apache Airflow

Rol: Será el cerebro que automatice y programe nuestro pipeline de datos batch.
Proceso: Crearemos un DAG (Grafo Acíclico Dirigido) en Airflow que se ejecute en un horario definido (ej. cada noche a la 1 AM). Este DAG ejecutará el trabajo de Spark que procesa los nuevos archivos CSV que hayan llegado al Data Lake.
Por qué? Proporciona monitoreo, reintentos automáticos en caso de fallos, manejo de dependencias y una interfaz visual para gestionar nuestros flujos de trabajo.
Formato de la Tabla Final: Delta Lake

Rol: Es el componente clave que permite el valor agregado. Delta Lake es una capa de almacenamiento de código abierto que se coloca sobre nuestro Data Lake (S3/GCS) y le añade funcionalidades de un Data Warehouse.
Por qué?
Transacciones ACID: Permite que el job de Spark Batch y el job de Spark Streaming escriban en la misma tabla al mismo tiempo sin corromper los datos.
Operaciones MERGE (UPSERT): Facilita la inserción de nuevos registros y la actualización de los existentes. Fundamental para integrar los datos históricos con los nuevos.
Schema Enforcement: Asegura que todos los datos que se escriben en la tabla sigan una estructura definida, evitando datos de mala calidad.
Time Travel: Permite consultar el estado de la tabla en un punto anterior en el tiempo.
3. Flujo de Datos Detallado
Flujo 1: Pipeline Batch (Datos Históricos)

Ingesta: Un proceso (manual o automático) deposita un nuevo archivo historico_2024-08-20.csv en s3://mi-data-lake/raw/batch/.
Orquestación: A la hora programada, el DAG de Airflow se activa.
Ejecución: Airflow lanza un trabajo de Spark Batch.
Procesamiento:
El job de Spark lee el nuevo archivo CSV.
Aplica transformaciones: limpieza de datos, estandarización de fechas, validación de campos, etc.
Utiliza el comando MERGE INTO de Delta Lake para insertar/actualizar estos registros en la tabla final ubicada en s3://mi-data-lake/processed/unified-events/. Si un registro ya existe, se puede actualizar; si es nuevo, se inserta.
Flujo 2: Pipeline Streaming (Datos en Tiempo Real)

Ingesta: Un script productor en Python se conecta al WebSocket de Binance. Por cada nueva transacción que recibe, la formatea como un JSON y la envía al topic crypto_trades en Kafka.
Procesamiento Continuo: Un trabajo de Spark Structured Streaming está corriendo de forma persistente.
Lectura: El job de Spark se suscribe al topic crypto_trades de Kafka y consume los mensajes en micro-lotes (ej. cada 30 segundos).
Transformación y Escritura:
Para cada micro-lote, Spark aplica las mismas transformaciones que en el flujo batch para asegurar la consistencia.
Utiliza la función foreachBatch junto con el comando MERGE INTO para escribir los datos del micro-lote en la misma tabla Delta s3://mi-data-lake/processed/unified-events/.
4. Estructura y Optimización de la Tabla Final
La tabla unified-events en formato Delta Lake será la joya de la corona. Para que sea eficiente, la diseñaremos así:

Formato de Archivo Subyacente: Parquet. Delta Lake usa Parquet por defecto. Es un formato columnar que ofrece una excelente compresión y rendimiento de lectura para cargas de trabajo analíticas.
Particionamiento: Es la técnica más importante para optimizar el rendimiento. Particionaremos la tabla por fecha.
Ejemplo: PARTITIONED BY (event_date DATE)
Cómo funciona? Físicamente, en S3/GCS, Delta Lake creará una estructura de carpetas como:
/processed/unified-events/
├── event_date=2024-08-19/
│   └── part-0001.snappy.parquet
├── event_date=2024-08-20/
│   └── part-0001.snappy.parquet
│   └── part-0002.snappy.parquet
...
Beneficio: Cuando un analista haga una consulta filtrando por un rango de fechas (WHERE event_date BETWEEN '2024-08-19' AND '2024-08-20'), Spark sabrá que solo necesita leer los datos dentro de esas carpetas, ignorando el resto y acelerando la consulta drásticamente.
5. Plan de Implementación (Pasos Sugeridos)
Fase 1: Infraestructura.

Configurar la cuenta de AWS/GCP.
Crear el bucket de S3/GCS con la estructura de carpetas definida.
Configurar los permisos y roles (IAM) necesarios para que los servicios interactúen.
Fase 2: Pipeline Batch.

Desarrollar el script de Spark Batch para leer CSV, transformar y escribir en una tabla Delta.
Crear el DAG de Airflow que orqueste este script.
Probar el flujo de extremo a extremo.
Fase 3: Pipeline Streaming.

Configurar Kafka o Pub/Sub y crear el topic.
Desarrollar el script productor que se conecta a la API y publica en Kafka.
Desarrollar el job de Spark Structured Streaming que consume de Kafka y escribe en la misma tabla Delta.
Fase 4: Integración y Optimización.

Asegurarse de que la lógica MERGE funcione correctamente para ambos flujos sin conflictos.
Implementar el particionamiento en la tabla Delta.
Ejecutar comandos de optimización de Delta Lake como OPTIMIZE (compacta archivos pequeños) y Z-ORDER (mejora la localidad de los datos).
Fase 5: Consumo y Visualización.

Conectar una herramienta de BI (como Tableau, Power BI) o un notebook de Data Science (Jupyter) a la tabla Delta para demostrar que los datos están unificados y disponibles para el análisis.
Este documento te proporciona un mapa de ruta claro y técnico. Si quieres empezar a construirlo, podemos comenzar por la Fase 1, configurando el entorno y los directorios del proyecto.

