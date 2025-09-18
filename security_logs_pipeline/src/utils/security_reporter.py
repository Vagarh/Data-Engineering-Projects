"""
Generador de reportes de seguridad del pipeline
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from elasticsearch import Elasticsearch
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityReporter:
    def __init__(self):
        self.es_client = Elasticsearch(
            [os.getenv('ELASTICSEARCH_HOSTS', 'http://elasticsearch:9200')],
            basic_auth=(
                os.getenv('ELASTICSEARCH_USERNAME', 'elastic'),
                os.getenv('ELASTICSEARCH_PASSWORD', 'password')
            )
        )
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Generar reporte diario de seguridad"""
        logger.info("Generando reporte diario de seguridad...")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        
        report = {
            'report_date': end_time.strftime('%Y-%m-%d'),
            'period': f"{start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}",
            'summary': self._get_summary_metrics(start_time, end_time),
            'threats_detected': self._get_threats_summary(start_time, end_time),
            'top_attackers': self._get_top_attackers(start_time, end_time),
            'attack_patterns': self._get_attack_patterns(start_time, end_time),
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _get_summary_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Obtener métricas resumen"""
        query = {
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": start_time.isoformat(),
                        "lte": end_time.isoformat()
                    }
                }
            },
            "aggs": {
                "log_types": {
                    "terms": {"field": "log_type"}
                },
                "severities": {
                    "terms": {"field": "severity"}
                },
                "threat_types": {
                    "terms": {"field": "threat_type"}
                }
            }
        }
        
        try:
            response = self.es_client.search(
                index="security-logs-*",
                body=query,
                size=0
            )
            
            total_logs = response['hits']['total']['value']
            
            return {
                'total_logs_processed': total_logs,
                'log_types': {
                    bucket['key']: bucket['doc_count'] 
                    for bucket in response['aggregations']['log_types']['buckets']
                },
                'severity_distribution': {
                    bucket['key']: bucket['doc_count'] 
                    for bucket in response['aggregations']['severities']['buckets']
                },
                'threat_types': {
                    bucket['key']: bucket['doc_count'] 
                    for bucket in response['aggregations']['threat_types']['buckets']
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas resumen: {e}")
            return {}
    
    def _get_threats_summary(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Obtener resumen de amenazas detectadas"""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start_time.isoformat(),
                                    "lte": end_time.isoformat()
                                }
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "alert_types": {
                    "terms": {"field": "alert_type"}
                },
                "severities": {
                    "terms": {"field": "severity"}
                }
            }
        }
        
        try:
            response = self.es_client.search(
                index="security-alerts-*",
                body=query,
                size=0
            )
            
            total_alerts = response['hits']['total']['value']
            
            return {
                'total_alerts': total_alerts,
                'alert_types': {
                    bucket['key']: bucket['doc_count'] 
                    for bucket in response['aggregations']['alert_types']['buckets']
                },
                'severity_breakdown': {
                    bucket['key']: bucket['doc_count'] 
                    for bucket in response['aggregations']['severities']['buckets']
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de amenazas: {e}")
            return {}
    
    def _get_top_attackers(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Obtener top IPs atacantes"""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": start_time.isoformat(),
                                    "lte": end_time.isoformat()
                                }
                            }
                        },
                        {
                            "terms": {
                                "severity": ["HIGH", "CRITICAL"]
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "top_ips": {
                    "terms": {
                        "field": "source_ip",
                        "size": 10
                    },
                    "aggs": {
                        "threat_types": {
                            "terms": {"field": "threat_type"}
                        },
                        "geoip": {
                            "terms": {"field": "geoip.country_name"}
                        }
                    }
                }
            }
        }
        
        try:
            response = self.es_client.search(
                index="security-logs-*",
                body=query,
                size=0
            )
            
            attackers = []
            for bucket in response['aggregations']['top_ips']['buckets']:
                attacker = {
                    'ip': bucket['key'],
                    'attack_count': bucket['doc_count'],
                    'threat_types': [
                        t['key'] for t in bucket['threat_types']['buckets']
                    ],
                    'country': bucket['geoip']['buckets'][0]['key'] if bucket['geoip']['buckets'] else 'Unknown'
                }
                attackers.append(attacker)
            
            return attackers
            
        except Exception as e:
            logger.error(f"Error obteniendo top atacantes: {e}")
            return []
    
    def _get_attack_patterns(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analizar patrones de ataque"""
        # Análisis temporal de ataques
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": start_time.isoformat(),
                                    "lte": end_time.isoformat()
                                }
                            }
                        },
                        {
                            "exists": {"field": "threat_type"}
                        }
                    ]
                }
            },
            "aggs": {
                "attacks_over_time": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "calendar_interval": "hour"
                    }
                },
                "attack_methods": {
                    "terms": {"field": "threat_type"}
                }
            }
        }
        
        try:
            response = self.es_client.search(
                index="security-logs-*",
                body=query,
                size=0
            )
            
            # Encontrar hora pico de ataques
            hourly_attacks = response['aggregations']['attacks_over_time']['buckets']
            peak_hour = max(hourly_attacks, key=lambda x: x['doc_count']) if hourly_attacks else None
            
            return {
                'peak_attack_hour': {
                    'time': peak_hour['key_as_string'] if peak_hour else None,
                    'attack_count': peak_hour['doc_count'] if peak_hour else 0
                },
                'common_attack_methods': {
                    bucket['key']: bucket['doc_count'] 
                    for bucket in response['aggregations']['attack_methods']['buckets']
                },
                'attack_frequency': len(hourly_attacks)
            }
            
        except Exception as e:
            logger.error(f"Error analizando patrones de ataque: {e}")
            return {}
    
    def _generate_recommendations(self) -> List[str]:
        """Generar recomendaciones de seguridad"""
        recommendations = [
            "Revisar y actualizar reglas de firewall basadas en IPs atacantes identificadas",
            "Implementar rate limiting para prevenir ataques de fuerza bruta",
            "Considerar implementar Web Application Firewall (WAF) para ataques web",
            "Revisar configuración de autenticación multifactor (MFA)",
            "Actualizar sistemas y aplicaciones con últimos parches de seguridad",
            "Realizar auditoría de usuarios con privilegios elevados",
            "Implementar monitoreo de integridad de archivos críticos",
            "Revisar políticas de retención y backup de logs de seguridad"
        ]
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Guardar reporte a archivo"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'/tmp/security_report_{timestamp}.json'
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Reporte guardado en: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")
            return None
    
    def print_report_summary(self, report: Dict[str, Any]):
        """Imprimir resumen del reporte"""
        print("\n" + "="*80)
        print("🛡️  REPORTE DIARIO DE SEGURIDAD")
        print("="*80)
        print(f"📅 Fecha: {report.get('report_date', 'N/A')}")
        print(f"⏰ Período: {report.get('period', 'N/A')}")
        
        summary = report.get('summary', {})
        print(f"\n📊 RESUMEN:")
        print(f"  • Total logs procesados: {summary.get('total_logs_processed', 0):,}")
        
        severity_dist = summary.get('severity_distribution', {})
        print(f"  • Eventos críticos: {severity_dist.get('CRITICAL', 0):,}")
        print(f"  • Eventos altos: {severity_dist.get('HIGH', 0):,}")
        print(f"  • Eventos medios: {severity_dist.get('MEDIUM', 0):,}")
        
        threats = report.get('threats_detected', {})
        print(f"\n🚨 AMENAZAS DETECTADAS:")
        print(f"  • Total alertas: {threats.get('total_alerts', 0):,}")
        
        alert_types = threats.get('alert_types', {})
        for alert_type, count in list(alert_types.items())[:5]:
            print(f"  • {alert_type}: {count:,}")
        
        attackers = report.get('top_attackers', [])
        if attackers:
            print(f"\n🎯 TOP ATACANTES:")
            for i, attacker in enumerate(attackers[:5], 1):
                print(f"  {i}. {attacker['ip']} ({attacker['country']}) - {attacker['attack_count']} ataques")
        
        patterns = report.get('attack_patterns', {})
        peak_hour = patterns.get('peak_attack_hour', {})
        if peak_hour.get('time'):
            print(f"\n⏰ HORA PICO DE ATAQUES:")
            print(f"  • {peak_hour['time']}: {peak_hour['attack_count']} ataques")
        
        print(f"\n💡 RECOMENDACIONES:")
        recommendations = report.get('recommendations', [])
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"  {i}. {rec}")
        
        print("="*80)


def main():
    """Función principal"""
    reporter = SecurityReporter()
    
    try:
        # Generar reporte diario
        report = reporter.generate_daily_report()
        
        # Imprimir resumen
        reporter.print_report_summary(report)
        
        # Guardar reporte
        filename = reporter.save_report(report)
        
        if filename:
            logger.info(f"✅ Reporte de seguridad generado: {filename}")
        else:
            logger.error("❌ Error generando reporte")
            
    except Exception as e:
        logger.error(f"Error en generación de reporte: {e}")
        raise


if __name__ == "__main__":
    main()