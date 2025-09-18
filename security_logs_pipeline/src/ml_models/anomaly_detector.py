"""
Detector de anomalías usando Machine Learning para logs de seguridad
"""
import os
import json
import logging
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from kafka import KafkaConsumer, KafkaProducer
from elasticsearch import Elasticsearch
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityAnomalyDetector:
    def __init__(self):
        self.model_path = os.getenv('ML_MODEL_PATH', '/app/models')
        self.anomaly_threshold = float(os.getenv('ANOMALY_THRESHOLD', '0.8'))
        
        # Configuración Kafka
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
        self.input_topic = os.getenv('KAFKA_TOPIC_PROCESSED_LOGS', 'processed-security-logs')
        self.output_topic = os.getenv('KAFKA_TOPIC_ALERTS', 'security-alerts')
        
        # Configuración Elasticsearch
        self.es_client = Elasticsearch(
            [os.getenv('ELASTICSEARCH_HOSTS', 'http://elasticsearch:9200')],
            basic_auth=(
                os.getenv('ELASTICSEARCH_USERNAME', 'elastic'),
                os.getenv('ELASTICSEARCH_PASSWORD', 'password')
            )
        )
        
        # Modelos y encoders
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        
        # Features para cada tipo de log
        self.feature_configs = {
            'web': {
                'numerical': ['status_code', 'response_size', 'processing_time'],
                'categorical': ['method', 'user_agent_category', 'path_category'],
                'derived': ['hour_of_day', 'day_of_week', 'is_weekend']
            },
            'firewall': {
                'numerical': ['src_port', 'dst_port', 'packet_count', 'bytes_transferred'],
                'categorical': ['protocol', 'action', 'src_ip_category', 'dst_ip_category'],
                'derived': ['hour_of_day', 'day_of_week', 'port_risk_score']
            },
            'auth': {
                'numerical': ['hour_of_day', 'day_of_week'],
                'categorical': ['result', 'auth_method', 'service', 'username_category'],
                'derived': ['is_weekend', 'is_admin_user', 'failure_rate']
            },
            'system': {
                'numerical': ['process_id', 'hour_of_day', 'day_of_week'],
                'categorical': ['event_type', 'severity', 'process_category', 'user_category'],
                'derived': ['is_weekend', 'is_suspicious_process']
            },
            'dns': {
                'numerical': ['response_time', 'hour_of_day', 'day_of_week'],
                'categorical': ['query_type', 'response_code', 'domain_category'],
                'derived': ['is_weekend', 'domain_reputation_score']
            }
        }
        
        os.makedirs(self.model_path, exist_ok=True)
    
    def extract_features(self, log_data: Dict[str, Any]) -> pd.DataFrame:
        """Extraer features de un log para ML"""
        log_type = log_data.get('log_type', 'unknown')
        
        if log_type not in self.feature_configs:
            logger.warning(f"Tipo de log desconocido: {log_type}")
            return pd.DataFrame()
        
        features = {}
        timestamp = pd.to_datetime(log_data.get('timestamp', datetime.now()))
        
        # Features derivadas temporales
        features['hour_of_day'] = timestamp.hour
        features['day_of_week'] = timestamp.dayofweek
        features['is_weekend'] = 1 if timestamp.dayofweek >= 5 else 0
        
        # Features específicas por tipo de log
        if log_type == 'web':
            features.update(self._extract_web_features(log_data))
        elif log_type == 'firewall':
            features.update(self._extract_firewall_features(log_data))
        elif log_type == 'auth':
            features.update(self._extract_auth_features(log_data))
        elif log_type == 'system':
            features.update(self._extract_system_features(log_data))
        elif log_type == 'dns':
            features.update(self._extract_dns_features(log_data))
        
        return pd.DataFrame([features])
    
    def _extract_web_features(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer features específicas de logs web"""
        features = {}
        
        # Features numéricas directas
        features['status_code'] = log_data.get('status_code', 200)
        features['response_size'] = log_data.get('response_size', 0)
        features['processing_time'] = log_data.get('processing_time', 0.0)
        
        # Categorización de User Agent
        user_agent = log_data.get('user_agent', '').lower()
        if any(bot in user_agent for bot in ['bot', 'crawler', 'spider']):
            features['user_agent_category'] = 'bot'
        elif any(tool in user_agent for tool in ['curl', 'wget', 'python', 'sqlmap']):
            features['user_agent_category'] = 'tool'
        else:
            features['user_agent_category'] = 'browser'
        
        # Categorización de path
        path = log_data.get('path', '').lower()
        if any(admin in path for admin in ['/admin', '/wp-admin', '/phpmyadmin']):
            features['path_category'] = 'admin'
        elif any(api in path for api in ['/api', '/rest', '/graphql']):
            features['path_category'] = 'api'
        elif path.endswith(('.php', '.asp', '.jsp')):
            features['path_category'] = 'dynamic'
        else:
            features['path_category'] = 'static'
        
        # Features adicionales
        features['method'] = log_data.get('method', 'GET')
        
        return features
    
    def _extract_firewall_features(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer features específicas de logs de firewall"""
        features = {}
        
        # Features numéricas
        features['src_port'] = log_data.get('src_port', 0)
        features['dst_port'] = log_data.get('dst_port', 0)
        features['packet_count'] = log_data.get('packet_count', 0)
        features['bytes_transferred'] = log_data.get('bytes_transferred', 0)
        
        # Categorización de IPs
        src_ip = log_data.get('src_ip', '')
        if src_ip.startswith(('192.168.', '10.', '172.16.')):
            features['src_ip_category'] = 'private'
        else:
            features['src_ip_category'] = 'public'
        
        dst_ip = log_data.get('dst_ip', '')
        if dst_ip.startswith(('192.168.', '10.', '172.16.')):
            features['dst_ip_category'] = 'private'
        else:
            features['dst_ip_category'] = 'public'
        
        # Score de riesgo del puerto
        high_risk_ports = [22, 23, 3389, 1433, 3306, 5432, 21, 25]
        features['port_risk_score'] = 1 if features['dst_port'] in high_risk_ports else 0
        
        features['protocol'] = log_data.get('protocol', 'TCP')
        features['action'] = log_data.get('action', 'ALLOW')
        
        return features
    
    def _extract_auth_features(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer features específicas de logs de autenticación"""
        features = {}
        
        features['result'] = log_data.get('result', 'SUCCESS')
        features['auth_method'] = log_data.get('auth_method', 'password')
        features['service'] = log_data.get('service', 'ssh')
        
        # Categorización de usuario
        username = log_data.get('username', '').lower()
        admin_users = ['admin', 'root', 'administrator', 'sa']
        features['username_category'] = 'admin' if username in admin_users else 'regular'
        features['is_admin_user'] = 1 if username in admin_users else 0
        
        # Tasa de fallos (requiere contexto histórico - simplificado)
        features['failure_rate'] = 0.1 if features['result'] == 'FAILED' else 0.0
        
        return features
    
    def _extract_system_features(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer features específicas de logs de sistema"""
        features = {}
        
        features['process_id'] = log_data.get('process_id', 0)
        features['event_type'] = log_data.get('event_type', 'unknown')
        features['severity'] = log_data.get('severity', 'INFO')
        
        # Categorización de proceso
        process_name = log_data.get('process_name', '').lower()
        suspicious_processes = ['powershell.exe', 'cmd.exe', 'nc.exe', 'wget.exe']
        features['is_suspicious_process'] = 1 if process_name in suspicious_processes else 0
        
        if process_name.endswith('.exe'):
            features['process_category'] = 'executable'
        elif process_name.endswith('.dll'):
            features['process_category'] = 'library'
        else:
            features['process_category'] = 'other'
        
        # Categorización de usuario
        user = log_data.get('user', '').lower()
        system_users = ['system', 'administrator', 'root']
        features['user_category'] = 'system' if user in system_users else 'regular'
        
        return features
    
    def _extract_dns_features(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer features específicas de logs DNS"""
        features = {}
        
        features['response_time'] = log_data.get('response_time', 0.0)
        features['query_type'] = log_data.get('query_type', 'A')
        features['response_code'] = log_data.get('response_code', 'NOERROR')
        
        # Categorización de dominio
        query = log_data.get('query', '').lower()
        suspicious_domains = ['evil.com', 'bad.com', 'suspicious.org', 'attacker.net']
        
        if any(domain in query for domain in suspicious_domains):
            features['domain_category'] = 'suspicious'
            features['domain_reputation_score'] = 0.9
        elif query.endswith(('.com', '.org', '.net')):
            features['domain_category'] = 'legitimate'
            features['domain_reputation_score'] = 0.1
        else:
            features['domain_category'] = 'unknown'
            features['domain_reputation_score'] = 0.5
        
        return features
    
    def train_model(self, log_type: str, training_data: pd.DataFrame):
        """Entrenar modelo de detección de anomalías para un tipo de log"""
        logger.info(f"Entrenando modelo para {log_type}")
        
        if training_data.empty:
            logger.warning(f"No hay datos de entrenamiento para {log_type}")
            return
        
        # Separar features y labels
        X = training_data.drop(['is_anomaly'], axis=1, errors='ignore')
        y = training_data.get('is_anomaly', np.zeros(len(training_data)))
        
        # Preparar encoders para variables categóricas
        categorical_features = self.feature_configs[log_type]['categorical']
        encoders = {}
        
        for feature in categorical_features:
            if feature in X.columns:
                encoder = LabelEncoder()
                X[feature] = encoder.fit_transform(X[feature].astype(str))
                encoders[feature] = encoder
        
        # Escalar features numéricas
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Entrenar modelo Isolation Forest
        model = IsolationForest(
            contamination=0.1,  # Esperamos ~10% de anomalías
            random_state=42,
            n_estimators=100
        )
        
        model.fit(X_scaled)
        
        # Guardar modelo y preprocessors
        self.models[log_type] = model
        self.scalers[log_type] = scaler
        self.encoders[log_type] = encoders
        
        # Evaluar modelo
        predictions = model.predict(X_scaled)
        anomaly_scores = model.decision_function(X_scaled)
        
        # Convertir predicciones (-1 = anomalía, 1 = normal)
        predictions_binary = (predictions == -1).astype(int)
        
        logger.info(f"Modelo {log_type} entrenado:")
        logger.info(f"  - Anomalías detectadas: {np.sum(predictions_binary)}/{len(predictions_binary)}")
        logger.info(f"  - Score promedio: {np.mean(anomaly_scores):.3f}")
        
        # Guardar modelo a disco
        self.save_model(log_type)
    
    def predict_anomaly(self, log_data: Dict[str, Any]) -> Tuple[bool, float]:
        """Predecir si un log es anómalo"""
        log_type = log_data.get('log_type', 'unknown')
        
        if log_type not in self.models:
            logger.warning(f"No hay modelo entrenado para {log_type}")
            return False, 0.0
        
        # Extraer features
        features_df = self.extract_features(log_data)
        if features_df.empty:
            return False, 0.0
        
        # Aplicar encoders
        X = features_df.copy()
        for feature, encoder in self.encoders[log_type].items():
            if feature in X.columns:
                try:
                    X[feature] = encoder.transform(X[feature].astype(str))
                except ValueError:
                    # Valor no visto durante entrenamiento
                    X[feature] = 0
        
        # Escalar features
        X_scaled = self.scalers[log_type].transform(X)
        
        # Predecir
        prediction = self.models[log_type].predict(X_scaled)[0]
        anomaly_score = self.models[log_type].decision_function(X_scaled)[0]
        
        # Convertir score a probabilidad (0-1)
        anomaly_probability = max(0, min(1, (0.5 - anomaly_score) / 0.5))
        
        is_anomaly = prediction == -1 or anomaly_probability > self.anomaly_threshold
        
        return is_anomaly, anomaly_probability
    
    def save_model(self, log_type: str):
        """Guardar modelo a disco"""
        model_file = f"{self.model_path}/{log_type}_model.pkl"
        scaler_file = f"{self.model_path}/{log_type}_scaler.pkl"
        encoders_file = f"{self.model_path}/{log_type}_encoders.pkl"
        
        joblib.dump(self.models[log_type], model_file)
        joblib.dump(self.scalers[log_type], scaler_file)
        joblib.dump(self.encoders[log_type], encoders_file)
        
        logger.info(f"Modelo {log_type} guardado en {model_file}")
    
    def load_model(self, log_type: str):
        """Cargar modelo desde disco"""
        model_file = f"{self.model_path}/{log_type}_model.pkl"
        scaler_file = f"{self.model_path}/{log_type}_scaler.pkl"
        encoders_file = f"{self.model_path}/{log_type}_encoders.pkl"
        
        try:
            self.models[log_type] = joblib.load(model_file)
            self.scalers[log_type] = joblib.load(scaler_file)
            self.encoders[log_type] = joblib.load(encoders_file)
            logger.info(f"Modelo {log_type} cargado desde {model_file}")
            return True
        except FileNotFoundError:
            logger.warning(f"No se encontró modelo para {log_type}")
            return False
    
    def process_kafka_stream(self):
        """Procesar stream de logs desde Kafka"""
        logger.info("Iniciando procesamiento de stream Kafka")
        
        # Cargar modelos existentes
        for log_type in self.feature_configs.keys():
            self.load_model(log_type)
        
        # Configurar consumer y producer
        consumer = KafkaConsumer(
            self.input_topic,
            bootstrap_servers=self.kafka_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='ml-anomaly-detector'
        )
        
        producer = KafkaProducer(
            bootstrap_servers=self.kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        try:
            for message in consumer:
                log_data = message.value
                
                # Predecir anomalía
                is_anomaly, anomaly_score = self.predict_anomaly(log_data)
                
                if is_anomaly:
                    # Crear alerta
                    alert = {
                        'timestamp': datetime.now().isoformat(),
                        'alert_type': 'anomaly_detected',
                        'log_type': log_data.get('log_type'),
                        'anomaly_score': anomaly_score,
                        'original_log': log_data,
                        'severity': self._calculate_severity(anomaly_score),
                        'description': self._generate_alert_description(log_data, anomaly_score)
                    }
                    
                    # Enviar alerta a Kafka
                    producer.send(self.output_topic, alert)
                    
                    # Indexar en Elasticsearch
                    self._index_alert_to_elasticsearch(alert)
                    
                    logger.warning(f"Anomalía detectada: {log_data.get('log_type')} - Score: {anomaly_score:.3f}")
                
        except KeyboardInterrupt:
            logger.info("Deteniendo procesamiento...")
        finally:
            consumer.close()
            producer.close()
    
    def _calculate_severity(self, anomaly_score: float) -> str:
        """Calcular severidad basada en el score de anomalía"""
        if anomaly_score > 0.9:
            return "CRITICAL"
        elif anomaly_score > 0.8:
            return "HIGH"
        elif anomaly_score > 0.6:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_alert_description(self, log_data: Dict[str, Any], anomaly_score: float) -> str:
        """Generar descripción de la alerta"""
        log_type = log_data.get('log_type', 'unknown')
        
        descriptions = {
            'web': f"Actividad web anómala detectada desde {log_data.get('source_ip')}",
            'firewall': f"Tráfico de red sospechoso: {log_data.get('src_ip')} → {log_data.get('dst_ip')}:{log_data.get('dst_port')}",
            'auth': f"Intento de autenticación anómalo: usuario {log_data.get('username')} desde {log_data.get('src_ip')}",
            'system': f"Evento de sistema sospechoso: {log_data.get('event_type')} en proceso {log_data.get('process_name')}",
            'dns': f"Consulta DNS sospechosa: {log_data.get('query')} desde {log_data.get('client_ip')}"
        }
        
        base_description = descriptions.get(log_type, f"Anomalía detectada en log tipo {log_type}")
        return f"{base_description} (Score: {anomaly_score:.3f})"
    
    def _index_alert_to_elasticsearch(self, alert: Dict[str, Any]):
        """Indexar alerta en Elasticsearch"""
        try:
            index_name = f"security-alerts-{datetime.now().strftime('%Y.%m')}"
            self.es_client.index(index=index_name, body=alert)
        except Exception as e:
            logger.error(f"Error indexando alerta en Elasticsearch: {e}")


def main():
    """Función principal"""
    detector = SecurityAnomalyDetector()
    
    # Procesar stream de Kafka
    detector.process_kafka_stream()


if __name__ == "__main__":
    main()