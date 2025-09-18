"""
DAG de Airflow para orquestar el pipeline de análisis de logs de seguridad
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.http.sensors.http import HttpSensor

# Configuración por defecto del DAG
default_args = {
    'owner': 'security-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

# Definir el DAG
dag = DAG(
    'security_logs_pipeline',
    default_args=default_args,
    description='Pipeline completo de análisis de logs de seguridad',
    schedule_interval=timedelta(hours=1),  # Ejecutar cada hora
    max_active_runs=1,
    tags=['security', 'logs', 'ml', 'siem']
)

def check_elasticsearch_health():
    """Verificar que Elasticsearch esté funcionando"""
    import requests
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        response = requests.get('http://elasticsearch:9200/_cluster/health', timeout=30)
        if response.status_code == 200:
            health_data = response.json()
            status = health_data.get('status', 'unknown')
            
            if status in ['green', 'yellow']:
                logger.info(f"Elasticsearch está saludable: {status}")
                return True
            else:
                logger.error(f"Elasticsearch no está saludable: {status}")
                return False
        else:
            logger.error(f"Elasticsearch no responde: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error verificando Elasticsearch: {e}")
        return False

def check_kafka_health():
    """Verificar que Kafka esté funcionando"""
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

def create_kafka_topics():
    """Crear topics de Kafka necesarios"""
    import subprocess
    import logging
    
    logger = logging.getLogger(__name__)
    
    topics = [
        'raw-security-logs',
        'processed-security-logs',
        'security-alerts'
    ]
    
    for topic in topics:
        try:
            cmd = [
                'kafka-topics.sh',
                '--create',
                '--bootstrap-server', 'kafka:29092',
                '--topic', topic,
                '--partitions', '3',
                '--replication-factor', '1',
                '--if-not-exists'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"Topic {topic} creado/verificado exitosamente")
            else:
                logger.warning(f"Posible error creando topic {topic}: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error creando topic {topic}: {e}")

def setup_elasticsearch_indices():
    """Configurar índices y templates de Elasticsearch"""
    import requests
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Template para logs de seguridad
    security_logs_template = {
        "index_patterns": ["security-logs-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "index.refresh_interval": "30s"
            },
            "mappings": {
                "properties": {
                    "@timestamp": {"type": "date"},
                    "timestamp": {"type": "date"},
                    "log_type": {"type": "keyword"},
                    "severity": {"type": "keyword"},
                    "source_ip": {"type": "ip"},
                    "src_ip": {"type": "ip"},
                    "dst_ip": {"type": "ip"},
                    "status_code": {"type": "integer"},
                    "method": {"type": "keyword"},
                    "path": {"type": "text"},
                    "user_agent": {"type": "text"},
                    "threat_type": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "geoip": {
                        "properties": {
                            "location": {"type": "geo_point"},
                            "country_name": {"type": "keyword"},
                            "city_name": {"type": "keyword"}
                        }
                    }
                }
            }
        }
    }
    
    # Template para alertas de seguridad
    security_alerts_template = {
        "index_patterns": ["security-alerts-*"],
        "template": {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "alert_type": {"type": "keyword"},
                    "severity": {"type": "keyword"},
                    "anomaly_score": {"type": "float"},
                    "description": {"type": "text"},
                    "alert_id": {"type": "keyword"},
                    "log_type": {"type": "keyword"},
                    "response_recommendations": {"type": "text"}
                }
            }
        }
    }
    
    templates = {
        "security-logs-template": security_logs_template,
        "security-alerts-template": security_alerts_template
    }
    
    for template_name, template_body in templates.items():
        try:
            response = requests.put(
                f'http://elasticsearch:9200/_index_template/{template_name}',
                json=template_body,
                headers={'Content-Type': 'application/json'},
                auth=('elastic', 'password'),
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Template {template_name} creado exitosamente")
            else:
                logger.error(f"Error creando template {template_name}: {response.text}")
                
        except Exception as e:
            logger.error(f"Error configurando template {template_name}: {e}")

def train_ml_models():
    """Entrenar modelos de ML con datos históricos"""
    import logging
    import subprocess
    
    logger = logging.getLogger(__name__)
    
    try:
        # Ejecutar script de entrenamiento
        result = subprocess.run([
            'python', '/opt/airflow/src/ml_models/model_trainer.py'
        ], capture_output=True, text=True, timeout=1800)  # 30 minutos timeout
        
        if result.returncode == 0:
            logger.info("Modelos ML entrenados exitosamente")
            logger.info(result.stdout)
        else:
            logger.error(f"Error entrenando modelos: {result.stderr}")
            raise Exception(f"Error en entrenamiento: {result.stderr}")
            
    except Exception as e:
        logger.error(f"Error ejecutando entrenamiento: {e}")
        raise

def generate_security_report():
    """Generar reporte de seguridad"""
    import logging
    import subprocess
    
    logger = logging.getLogger(__name__)
    
    try:
        result = subprocess.run([
            'python', '/opt/airflow/src/utils/security_reporter.py'
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            logger.info("Reporte de seguridad generado exitosamente")
            logger.info(result.stdout)
        else:
            logger.error(f"Error generando reporte: {result.stderr}")
            
    except Exception as e:
        logger.error(f"Error ejecutando reporte: {e}")

def cleanup_old_indices():
    """Limpiar índices antiguos para optimizar almacenamiento"""
    import requests
    import logging
    from datetime import datetime, timedelta
    
    logger = logging.getLogger(__name__)
    
    try:
        # Eliminar índices más antiguos de 30 días
        cutoff_date = datetime.now() - timedelta(days=30)
        cutoff_str = cutoff_date.strftime('%Y.%m.%d')
        
        # Obtener lista de índices
        response = requests.get(
            'http://elasticsearch:9200/_cat/indices/security-*?format=json',
            auth=('elastic', 'password'),
            timeout=30
        )
        
        if response.status_code == 200:
            indices = response.json()
            
            for index_info in indices:
                index_name = index_info['index']
                
                # Extraer fecha del nombre del índice
                if 'security-logs-' in index_name:
                    date_part = index_name.replace('security-logs-', '')
                    try:
                        index_date = datetime.strptime(date_part, '%Y.%m.%d')
                        if index_date < cutoff_date:
                            # Eliminar índice antiguo
                            delete_response = requests.delete(
                                f'http://elasticsearch:9200/{index_name}',
                                auth=('elastic', 'password'),
                                timeout=30
                            )
                            
                            if delete_response.status_code == 200:
                                logger.info(f"Índice {index_name} eliminado")
                            else:
                                logger.warning(f"Error eliminando {index_name}")
                                
                    except ValueError:
                        # Formato de fecha no reconocido
                        continue
                        
        else:
            logger.error(f"Error obteniendo lista de índices: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error en cleanup de índices: {e}")

def monitor_pipeline_health():
    """Monitorear la salud general del pipeline"""
    import requests
    import logging
    
    logger = logging.getLogger(__name__)
    
    health_checks = {
        'elasticsearch': 'http://elasticsearch:9200/_cluster/health',
        'kibana': 'http://kibana:5601/api/status',
        'logstash': 'http://logstash:9600/_node/stats'
    }
    
    health_status = {}
    
    for service, url in health_checks.items():
        try:
            response = requests.get(url, timeout=30)
            health_status[service] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'status_code': response.status_code
            }
            
        except Exception as e:
            health_status[service] = {
                'status': 'error',
                'error': str(e)
            }
    
    # Log del estado general
    healthy_services = sum(1 for status in health_status.values() if status['status'] == 'healthy')
    total_services = len(health_status)
    
    logger.info(f"Estado del pipeline: {healthy_services}/{total_services} servicios saludables")
    
    for service, status in health_status.items():
        if status['status'] != 'healthy':
            logger.warning(f"Servicio {service} no saludable: {status}")
    
    return health_status

# Definir tareas del DAG

# 1. Verificar salud de servicios
check_elasticsearch_task = PythonOperator(
    task_id='check_elasticsearch_health',
    python_callable=check_elasticsearch_health,
    dag=dag
)

check_kafka_task = PythonOperator(
    task_id='check_kafka_health',
    python_callable=check_kafka_health,
    dag=dag
)

# 2. Configurar infraestructura
setup_kafka_topics_task = PythonOperator(
    task_id='create_kafka_topics',
    python_callable=create_kafka_topics,
    dag=dag
)

setup_elasticsearch_task = PythonOperator(
    task_id='setup_elasticsearch_indices',
    python_callable=setup_elasticsearch_indices,
    dag=dag
)

# 3. Entrenar modelos ML (diario)
train_models_task = PythonOperator(
    task_id='train_ml_models',
    python_callable=train_ml_models,
    dag=dag
)

# 4. Generar reportes
generate_report_task = PythonOperator(
    task_id='generate_security_report',
    python_callable=generate_security_report,
    dag=dag
)

# 5. Mantenimiento
cleanup_task = PythonOperator(
    task_id='cleanup_old_indices',
    python_callable=cleanup_old_indices,
    dag=dag
)

# 6. Monitoreo
monitor_task = PythonOperator(
    task_id='monitor_pipeline_health',
    python_callable=monitor_pipeline_health,
    dag=dag
)

# 7. Iniciar servicios de procesamiento
start_log_generator_task = BashOperator(
    task_id='start_log_generator',
    bash_command='docker-compose restart log-generator',
    dag=dag
)

start_ml_processor_task = BashOperator(
    task_id='start_ml_processor',
    bash_command='docker-compose restart ml-processor',
    dag=dag
)

# Definir dependencias
[check_elasticsearch_task, check_kafka_task] >> [setup_kafka_topics_task, setup_elasticsearch_task]
setup_elasticsearch_task >> train_models_task
[setup_kafka_topics_task, train_models_task] >> [start_log_generator_task, start_ml_processor_task]
[start_log_generator_task, start_ml_processor_task] >> monitor_task
monitor_task >> generate_report_task
generate_report_task >> cleanup_task