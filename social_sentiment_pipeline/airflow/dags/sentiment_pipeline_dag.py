"""
DAG de Airflow para orquestar el pipeline de análisis de sentimientos
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.http.sensors.http import HttpSensor

# Configuración por defecto del DAG
default_args = {
    'owner': 'data-engineering-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

# Definir el DAG
dag = DAG(
    'sentiment_analysis_pipeline',
    default_args=default_args,
    description='Pipeline completo de análisis de sentimientos en tiempo real',
    schedule_interval=timedelta(hours=1),  # Ejecutar cada hora
    max_active_runs=1,
    tags=['sentiment', 'streaming', 'ml', 'social-media']
)

def check_kafka_health():
    """Verificar que Kafka esté funcionando correctamente"""
    import subprocess
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Verificar que Kafka esté respondiendo
        result = subprocess.run([
            'kafka-topics.sh', '--bootstrap-server', 'kafka:29092', '--list'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info("Kafka está funcionando correctamente")
            return True
        else:
            logger.error(f"Error verificando Kafka: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error conectando a Kafka: {e}")
        return False

def check_clickhouse_health():
    """Verificar que ClickHouse esté funcionando correctamente"""
    import requests
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        response = requests.get('http://clickhouse:8123/ping', timeout=10)
        if response.status_code == 200:
            logger.info("ClickHouse está funcionando correctamente")
            return True
        else:
            logger.error(f"ClickHouse no responde correctamente: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error conectando a ClickHouse: {e}")
        return False

def start_twitter_producer():
    """Iniciar el producer de Twitter"""
    import subprocess
    import logging
    import os
    
    logger = logging.getLogger(__name__)
    
    try:
        # Ejecutar el producer de Twitter
        cmd = [
            'python', '/opt/airflow/src/producers/twitter_producer.py'
        ]
        
        logger.info("Iniciando Twitter producer...")
        
        # Ejecutar en background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        
        logger.info(f"Twitter producer iniciado con PID: {process.pid}")
        return process.pid
        
    except Exception as e:
        logger.error(f"Error iniciando Twitter producer: {e}")
        raise

def start_spark_streaming():
    """Iniciar el job de Spark Streaming"""
    import subprocess
    import logging
    import os
    
    logger = logging.getLogger(__name__)
    
    try:
        # Comando para ejecutar Spark job
        cmd = [
            'spark-submit',
            '--master', 'spark://spark-master:7077',
            '--packages', 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1',
            '/opt/airflow/src/processors/spark_streaming.py'
        ]
        
        logger.info("Iniciando Spark Streaming job...")
        
        # Ejecutar Spark job
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        
        logger.info(f"Spark Streaming job iniciado con PID: {process.pid}")
        return process.pid
        
    except Exception as e:
        logger.error(f"Error iniciando Spark Streaming: {e}")
        raise

def monitor_pipeline_health():
    """Monitorear la salud del pipeline"""
    import logging
    import time
    from datetime import datetime, timedelta
    
    logger = logging.getLogger(__name__)
    
    try:
        # Verificar métricas en ClickHouse
        from clickhouse_driver import Client
        
        client = Client(
            host='clickhouse',
            port=9000,
            user='admin',
            password='password',
            database='sentiment_db'
        )
        
        # Verificar datos recientes (última hora)
        query = """
        SELECT 
            count() as total_tweets,
            countIf(predicted_sentiment = 'positive') as positive_tweets,
            countIf(predicted_sentiment = 'negative') as negative_tweets,
            avg(confidence) as avg_confidence
        FROM sentiment_analysis 
        WHERE processing_timestamp >= now() - INTERVAL 1 HOUR
        """
        
        result = client.execute(query)
        
        if result and len(result) > 0:
            total_tweets, positive_tweets, negative_tweets, avg_confidence = result[0]
            
            logger.info(f"Métricas de la última hora:")
            logger.info(f"  - Total tweets: {total_tweets}")
            logger.info(f"  - Tweets positivos: {positive_tweets}")
            logger.info(f"  - Tweets negativos: {negative_tweets}")
            logger.info(f"  - Confianza promedio: {avg_confidence:.3f}")
            
            # Alertas básicas
            if total_tweets == 0:
                logger.warning("⚠️  No se han procesado tweets en la última hora")
            
            if avg_confidence and avg_confidence < 0.5:
                logger.warning(f"⚠️  Confianza promedio baja: {avg_confidence:.3f}")
            
            return True
        else:
            logger.warning("No se encontraron datos recientes")
            return False
            
    except Exception as e:
        logger.error(f"Error monitoreando pipeline: {e}")
        return False

def cleanup_old_data():
    """Limpiar datos antiguos para optimizar almacenamiento"""
    import logging
    from datetime import datetime, timedelta
    
    logger = logging.getLogger(__name__)
    
    try:
        from clickhouse_driver import Client
        
        client = Client(
            host='clickhouse',
            port=9000,
            user='admin',
            password='password',
            database='sentiment_db'
        )
        
        # Eliminar datos más antiguos de 30 días
        cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        query = f"""
        ALTER TABLE sentiment_analysis 
        DROP PARTITION '{cutoff_date}'
        """
        
        try:
            client.execute(query)
            logger.info(f"Datos anteriores a {cutoff_date} eliminados exitosamente")
        except Exception as e:
            # Es normal que falle si no existe la partición
            logger.info(f"No hay particiones para eliminar antes de {cutoff_date}")
        
        # Optimizar tablas
        optimize_queries = [
            "OPTIMIZE TABLE sentiment_analysis FINAL",
            "OPTIMIZE TABLE sentiment_hourly_agg FINAL"
        ]
        
        for query in optimize_queries:
            try:
                client.execute(query)
                logger.info(f"Optimización ejecutada: {query}")
            except Exception as e:
                logger.warning(f"Error en optimización: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error en cleanup: {e}")
        return False

# Definir tareas del DAG

# 1. Verificar salud de servicios
check_kafka_task = PythonOperator(
    task_id='check_kafka_health',
    python_callable=check_kafka_health,
    dag=dag
)

check_clickhouse_task = PythonOperator(
    task_id='check_clickhouse_health',
    python_callable=check_clickhouse_health,
    dag=dag
)

# 2. Iniciar componentes del pipeline
start_producer_task = PythonOperator(
    task_id='start_twitter_producer',
    python_callable=start_twitter_producer,
    dag=dag
)

start_streaming_task = PythonOperator(
    task_id='start_spark_streaming',
    python_callable=start_spark_streaming,
    dag=dag
)

# 3. Monitorear pipeline
monitor_task = PythonOperator(
    task_id='monitor_pipeline_health',
    python_callable=monitor_pipeline_health,
    dag=dag
)

# 4. Cleanup y optimización
cleanup_task = PythonOperator(
    task_id='cleanup_old_data',
    python_callable=cleanup_old_data,
    dag=dag
)

# 5. Generar reporte de métricas
generate_report_task = BashOperator(
    task_id='generate_metrics_report',
    bash_command="""
    echo "Generando reporte de métricas..."
    python /opt/airflow/src/utils/metrics_reporter.py
    """,
    dag=dag
)

# Definir dependencias
check_kafka_task >> start_producer_task
check_clickhouse_task >> start_streaming_task
[start_producer_task, start_streaming_task] >> monitor_task
monitor_task >> cleanup_task
cleanup_task >> generate_report_task