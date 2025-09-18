"""
Sistema de alertas para el pipeline de seguridad
"""
import os
import json
import logging
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

import requests
from kafka import KafkaConsumer
from elasticsearch import Elasticsearch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityAlertManager:
    def __init__(self):
        # Configuración Kafka
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
        self.alerts_topic = os.getenv('KAFKA_TOPIC_ALERTS', 'security-alerts')
        
        # Configuración Elasticsearch
        self.es_client = Elasticsearch(
            [os.getenv('ELASTICSEARCH_HOSTS', 'http://elasticsearch:9200')],
            basic_auth=(
                os.getenv('ELASTICSEARCH_USERNAME', 'elastic'),
                os.getenv('ELASTICSEARCH_PASSWORD', 'password')
            )
        )
        
        # Configuración de alertas
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        self.slack_channel = os.getenv('SLACK_CHANNEL', '#security-alerts')
        
        # Configuración de email
        self.smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('EMAIL_SMTP_PORT', '587'))
        self.email_username = os.getenv('EMAIL_USERNAME')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_recipients = os.getenv('EMAIL_RECIPIENTS', '').split(',')
        
        # Configuración PagerDuty
        self.pagerduty_key = os.getenv('PAGERDUTY_INTEGRATION_KEY')
        
        # Configuración de umbrales
        self.brute_force_threshold = int(os.getenv('BRUTE_FORCE_THRESHOLD', '10'))
        self.brute_force_window = int(os.getenv('BRUTE_FORCE_WINDOW_MINUTES', '5'))
        
        # Cache para evitar spam de alertas
        self.alert_cache = {}
        self.cache_duration = timedelta(minutes=15)
    
    def process_alerts(self):
        """Procesar alertas desde Kafka"""
        logger.info("Iniciando procesamiento de alertas")
        
        consumer = KafkaConsumer(
            self.alerts_topic,
            bootstrap_servers=self.kafka_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='security-alert-manager'
        )
        
        try:
            for message in consumer:
                alert_data = message.value
                self.handle_alert(alert_data)
                
        except KeyboardInterrupt:
            logger.info("Deteniendo procesamiento de alertas...")
        finally:
            consumer.close()
    
    def handle_alert(self, alert_data: Dict[str, Any]):
        """Manejar una alerta individual"""
        alert_type = alert_data.get('alert_type', 'unknown')
        severity = alert_data.get('severity', 'LOW')
        
        logger.info(f"Procesando alerta: {alert_type} - {severity}")
        
        # Verificar si es una alerta duplicada reciente
        if self._is_duplicate_alert(alert_data):
            logger.debug("Alerta duplicada ignorada")
            return
        
        # Enriquecer alerta con contexto adicional
        enriched_alert = self._enrich_alert(alert_data)
        
        # Determinar canales de notificación basado en severidad
        notification_channels = self._get_notification_channels(severity)
        
        # Enviar notificaciones
        for channel in notification_channels:
            try:
                if channel == 'slack':
                    self._send_slack_alert(enriched_alert)
                elif channel == 'email':
                    self._send_email_alert(enriched_alert)
                elif channel == 'pagerduty':
                    self._send_pagerduty_alert(enriched_alert)
                    
            except Exception as e:
                logger.error(f"Error enviando alerta por {channel}: {e}")
        
        # Indexar alerta en Elasticsearch
        self._index_alert(enriched_alert)
        
        # Actualizar cache
        self._update_alert_cache(alert_data)
    
    def _is_duplicate_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Verificar si es una alerta duplicada reciente"""
        alert_key = self._generate_alert_key(alert_data)
        
        if alert_key in self.alert_cache:
            last_alert_time = self.alert_cache[alert_key]
            if datetime.now() - last_alert_time < self.cache_duration:
                return True
        
        return False
    
    def _generate_alert_key(self, alert_data: Dict[str, Any]) -> str:
        """Generar clave única para la alerta"""
        alert_type = alert_data.get('alert_type', 'unknown')
        log_type = alert_data.get('log_type', 'unknown')
        
        # Incluir IP o identificador único si está disponible
        original_log = alert_data.get('original_log', {})
        identifier = (
            original_log.get('source_ip') or 
            original_log.get('src_ip') or 
            original_log.get('client_ip') or 
            'unknown'
        )
        
        return f"{alert_type}:{log_type}:{identifier}"
    
    def _enrich_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquecer alerta con contexto adicional"""
        enriched = alert_data.copy()
        
        # Agregar contexto temporal
        enriched['alert_id'] = f"SEC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        enriched['processed_at'] = datetime.now().isoformat()
        
        # Buscar alertas relacionadas recientes
        related_alerts = self._find_related_alerts(alert_data)
        if related_alerts:
            enriched['related_alerts_count'] = len(related_alerts)
            enriched['is_part_of_campaign'] = len(related_alerts) > 3
        
        # Agregar recomendaciones de respuesta
        enriched['response_recommendations'] = self._generate_response_recommendations(alert_data)
        
        return enriched
    
    def _find_related_alerts(self, alert_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Buscar alertas relacionadas en las últimas horas"""
        try:
            original_log = alert_data.get('original_log', {})
            source_ip = (
                original_log.get('source_ip') or 
                original_log.get('src_ip') or 
                original_log.get('client_ip')
            )
            
            if not source_ip:
                return []
            
            # Buscar en Elasticsearch
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"range": {"timestamp": {"gte": "now-2h"}}},
                            {"term": {"severity": "HIGH"}}
                        ],
                        "should": [
                            {"term": {"original_log.source_ip": source_ip}},
                            {"term": {"original_log.src_ip": source_ip}},
                            {"term": {"original_log.client_ip": source_ip}}
                        ],
                        "minimum_should_match": 1
                    }
                },
                "size": 10
            }
            
            response = self.es_client.search(
                index="security-alerts-*",
                body=query
            )
            
            return [hit['_source'] for hit in response['hits']['hits']]
            
        except Exception as e:
            logger.error(f"Error buscando alertas relacionadas: {e}")
            return []
    
    def _generate_response_recommendations(self, alert_data: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones de respuesta"""
        recommendations = []
        alert_type = alert_data.get('alert_type', '')
        threat_type = alert_data.get('original_log', {}).get('threat_type', '')
        
        if 'brute_force' in threat_type:
            recommendations.extend([
                "Bloquear IP origen en firewall",
                "Revisar logs de autenticación para otros intentos",
                "Considerar implementar rate limiting",
                "Verificar si las credenciales fueron comprometidas"
            ])
        
        elif 'web_attack' in threat_type:
            recommendations.extend([
                "Revisar logs del servidor web para otros ataques",
                "Verificar integridad de la aplicación web",
                "Considerar bloquear IP en WAF",
                "Revisar configuración de seguridad web"
            ])
        
        elif 'port_scan' in threat_type:
            recommendations.extend([
                "Bloquear IP origen en firewall perimetral",
                "Revisar configuración de servicios expuestos",
                "Verificar logs de otros sistemas",
                "Considerar implementar IPS"
            ])
        
        elif 'malicious_dns' in threat_type:
            recommendations.extend([
                "Bloquear dominio en DNS resolver",
                "Investigar sistema que realizó la consulta",
                "Buscar indicadores de compromiso",
                "Revisar tráfico de red del host afectado"
            ])
        
        else:
            recommendations.extend([
                "Investigar el evento en detalle",
                "Revisar logs relacionados",
                "Verificar si es un falso positivo",
                "Documentar el incidente"
            ])
        
        return recommendations
    
    def _get_notification_channels(self, severity: str) -> List[str]:
        """Determinar canales de notificación según severidad"""
        channels = []
        
        if severity == "CRITICAL":
            channels = ['slack', 'email', 'pagerduty']
        elif severity == "HIGH":
            channels = ['slack', 'email']
        elif severity == "MEDIUM":
            channels = ['slack']
        # LOW severity no genera notificaciones automáticas
        
        return channels
    
    def _send_slack_alert(self, alert_data: Dict[str, Any]):
        """Enviar alerta a Slack"""
        if not self.slack_webhook:
            logger.warning("Slack webhook no configurado")
            return
        
        severity = alert_data.get('severity', 'LOW')
        alert_type = alert_data.get('alert_type', 'unknown')
        description = alert_data.get('description', 'Sin descripción')
        
        # Emojis por severidad
        severity_emojis = {
            'CRITICAL': '🚨',
            'HIGH': '⚠️',
            'MEDIUM': '⚡',
            'LOW': 'ℹ️'
        }
        
        # Colores por severidad
        severity_colors = {
            'CRITICAL': '#FF0000',
            'HIGH': '#FF8C00',
            'MEDIUM': '#FFD700',
            'LOW': '#00CED1'
        }
        
        emoji = severity_emojis.get(severity, 'ℹ️')
        color = severity_colors.get(severity, '#00CED1')
        
        # Construir mensaje
        original_log = alert_data.get('original_log', {})
        source_ip = (
            original_log.get('source_ip') or 
            original_log.get('src_ip') or 
            original_log.get('client_ip') or 
            'N/A'
        )
        
        payload = {
            "channel": self.slack_channel,
            "username": "Security Alert Bot",
            "icon_emoji": ":shield:",
            "attachments": [
                {
                    "color": color,
                    "title": f"{emoji} Alerta de Seguridad - {severity}",
                    "text": description,
                    "fields": [
                        {
                            "title": "Tipo de Alerta",
                            "value": alert_type,
                            "short": True
                        },
                        {
                            "title": "IP Origen",
                            "value": source_ip,
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": alert_data.get('timestamp', 'N/A'),
                            "short": True
                        },
                        {
                            "title": "Score de Anomalía",
                            "value": f"{alert_data.get('anomaly_score', 0):.3f}",
                            "short": True
                        }
                    ],
                    "footer": "Security Pipeline",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        # Agregar recomendaciones si existen
        recommendations = alert_data.get('response_recommendations', [])
        if recommendations:
            payload["attachments"][0]["fields"].append({
                "title": "Recomendaciones",
                "value": "\n".join([f"• {rec}" for rec in recommendations[:3]]),
                "short": False
            })
        
        response = requests.post(self.slack_webhook, json=payload)
        
        if response.status_code == 200:
            logger.info("Alerta enviada a Slack exitosamente")
        else:
            logger.error(f"Error enviando alerta a Slack: {response.status_code}")
    
    def _send_email_alert(self, alert_data: Dict[str, Any]):
        """Enviar alerta por email"""
        if not self.email_username or not self.email_password:
            logger.warning("Credenciales de email no configuradas")
            return
        
        if not self.email_recipients:
            logger.warning("Destinatarios de email no configurados")
            return
        
        severity = alert_data.get('severity', 'LOW')
        alert_type = alert_data.get('alert_type', 'unknown')
        description = alert_data.get('description', 'Sin descripción')
        
        # Crear mensaje
        msg = MimeMultipart()
        msg['From'] = self.email_username
        msg['To'] = ', '.join(self.email_recipients)
        msg['Subject'] = f"[{severity}] Alerta de Seguridad - {alert_type}"
        
        # Cuerpo del email
        body = f"""
        ALERTA DE SEGURIDAD
        
        Severidad: {severity}
        Tipo: {alert_type}
        Descripción: {description}
        Timestamp: {alert_data.get('timestamp', 'N/A')}
        
        Detalles del Log Original:
        {json.dumps(alert_data.get('original_log', {}), indent=2)}
        
        Recomendaciones de Respuesta:
        """
        
        recommendations = alert_data.get('response_recommendations', [])
        for i, rec in enumerate(recommendations, 1):
            body += f"\n{i}. {rec}"
        
        body += f"""
        
        ---
        Alerta generada por Security Pipeline
        ID: {alert_data.get('alert_id', 'N/A')}
        """
        
        msg.attach(MimeText(body, 'plain'))
        
        # Enviar email
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_username, self.email_recipients, text)
            server.quit()
            
            logger.info("Alerta enviada por email exitosamente")
            
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
    
    def _send_pagerduty_alert(self, alert_data: Dict[str, Any]):
        """Enviar alerta a PagerDuty"""
        if not self.pagerduty_key:
            logger.warning("PagerDuty integration key no configurada")
            return
        
        payload = {
            "routing_key": self.pagerduty_key,
            "event_action": "trigger",
            "dedup_key": alert_data.get('alert_id'),
            "payload": {
                "summary": alert_data.get('description', 'Alerta de seguridad'),
                "severity": alert_data.get('severity', 'low').lower(),
                "source": "Security Pipeline",
                "component": alert_data.get('log_type', 'unknown'),
                "group": "security",
                "class": alert_data.get('alert_type', 'unknown'),
                "custom_details": alert_data.get('original_log', {})
            }
        }
        
        try:
            response = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 202:
                logger.info("Alerta enviada a PagerDuty exitosamente")
            else:
                logger.error(f"Error enviando alerta a PagerDuty: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error enviando alerta a PagerDuty: {e}")
    
    def _index_alert(self, alert_data: Dict[str, Any]):
        """Indexar alerta en Elasticsearch"""
        try:
            index_name = f"security-alerts-{datetime.now().strftime('%Y.%m')}"
            self.es_client.index(index=index_name, body=alert_data)
            logger.debug("Alerta indexada en Elasticsearch")
            
        except Exception as e:
            logger.error(f"Error indexando alerta: {e}")
    
    def _update_alert_cache(self, alert_data: Dict[str, Any]):
        """Actualizar cache de alertas"""
        alert_key = self._generate_alert_key(alert_data)
        self.alert_cache[alert_key] = datetime.now()
        
        # Limpiar cache antiguo
        cutoff_time = datetime.now() - self.cache_duration
        self.alert_cache = {
            k: v for k, v in self.alert_cache.items() 
            if v > cutoff_time
        }


def main():
    """Función principal"""
    alert_manager = SecurityAlertManager()
    alert_manager.process_alerts()


if __name__ == "__main__":
    main()