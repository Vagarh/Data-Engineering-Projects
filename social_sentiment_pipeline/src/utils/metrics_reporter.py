"""
Generador de reportes de métricas del pipeline
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from clickhouse_driver import Client
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsReporter:
    def __init__(self):
        self.client = Client(
            host=os.getenv('CLICKHOUSE_HOST', 'clickhouse'),
            port=int(os.getenv('CLICKHOUSE_PORT', '9000')),
            user=os.getenv('CLICKHOUSE_USER', 'admin'),
            password=os.getenv('CLICKHOUSE_PASSWORD', 'password'),
            database=os.getenv('CLICKHOUSE_DATABASE', 'sentiment_db')
        )
    
    def get_pipeline_health_metrics(self) -> Dict[str, Any]:
        """Obtener métricas de salud del pipeline"""
        try:
            # Tweets procesados en las últimas 24 horas
            query_24h = """
            SELECT 
                count() as total_tweets,
                countIf(predicted_sentiment = 'positive') as positive_tweets,
                countIf(predicted_sentiment = 'neutral') as neutral_tweets,
                countIf(predicted_sentiment = 'negative') as negative_tweets,
                avg(confidence) as avg_confidence,
                sum(like_count) as total_likes,
                sum(retweet_count) as total_retweets,
                uniq(author_id) as unique_authors
            FROM sentiment_analysis 
            WHERE processing_timestamp >= now() - INTERVAL 24 HOUR
            """
            
            result_24h = self.client.execute(query_24h)[0]
            
            # Tweets procesados en la última hora
            query_1h = """
            SELECT count() as tweets_last_hour
            FROM sentiment_analysis 
            WHERE processing_timestamp >= now() - INTERVAL 1 HOUR
            """
            
            tweets_last_hour = self.client.execute(query_1h)[0][0]
            
            # Calcular tasas
            total_tweets = result_24h[0]
            positive_rate = (result_24h[1] / total_tweets * 100) if total_tweets > 0 else 0
            negative_rate = (result_24h[3] / total_tweets * 100) if total_tweets > 0 else 0
            
            return {
                'timestamp': datetime.now().isoformat(),
                'period_24h': {
                    'total_tweets': total_tweets,
                    'positive_tweets': result_24h[1],
                    'neutral_tweets': result_24h[2],
                    'negative_tweets': result_24h[3],
                    'positive_rate_pct': round(positive_rate, 2),
                    'negative_rate_pct': round(negative_rate, 2),
                    'avg_confidence': round(result_24h[4], 3) if result_24h[4] else 0,
                    'total_likes': result_24h[5],
                    'total_retweets': result_24h[6],
                    'unique_authors': result_24h[7]
                },
                'period_1h': {
                    'tweets_processed': tweets_last_hour
                },
                'health_status': self._calculate_health_status(total_tweets, tweets_last_hour, result_24h[4])
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas de salud: {e}")
            return {'error': str(e)}
    
    def _calculate_health_status(self, total_24h: int, total_1h: int, avg_confidence: float) -> str:
        """Calcular estado de salud del pipeline"""
        if total_24h == 0:
            return 'CRITICAL - No data processed in 24h'
        elif total_1h == 0:
            return 'WARNING - No data processed in last hour'
        elif avg_confidence and avg_confidence < 0.5:
            return 'WARNING - Low model confidence'
        elif total_24h < 100:
            return 'WARNING - Low volume'
        else:
            return 'HEALTHY'
    
    def get_trending_topics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Obtener temas trending basados en palabras clave"""
        try:
            query = f"""
            WITH word_counts AS (
                SELECT 
                    arrayJoin(extractAll(lower(text), '[a-zA-Z]{{3,}}')) as word,
                    predicted_sentiment,
                    count() as mentions
                FROM sentiment_analysis 
                WHERE processing_timestamp >= now() - INTERVAL {hours} HOUR
                    AND length(word) >= 3
                    AND word NOT IN ('the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'way', 'she', 'use', 'her', 'now', 'oil', 'sit', 'set')
                GROUP BY word, predicted_sentiment
            )
            SELECT 
                word,
                sum(mentions) as total_mentions,
                sumIf(mentions, predicted_sentiment = 'positive') as positive_mentions,
                sumIf(mentions, predicted_sentiment = 'negative') as negative_mentions,
                (sumIf(mentions, predicted_sentiment = 'positive') - sumIf(mentions, predicted_sentiment = 'negative')) / sum(mentions) as sentiment_score
            FROM word_counts
            GROUP BY word
            HAVING total_mentions >= 5
            ORDER BY total_mentions DESC
            LIMIT 20
            """
            
            results = self.client.execute(query)
            
            trending = []
            for row in results:
                trending.append({
                    'word': row[0],
                    'total_mentions': row[1],
                    'positive_mentions': row[2],
                    'negative_mentions': row[3],
                    'sentiment_score': round(row[4], 3)
                })
            
            return trending
            
        except Exception as e:
            logger.error(f"Error obteniendo trending topics: {e}")
            return []
    
    def get_hourly_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """Obtener tendencias por hora"""
        try:
            query = f"""
            SELECT 
                hour_timestamp,
                total_tweets,
                positive_tweets,
                neutral_tweets,
                negative_tweets,
                avg_confidence,
                total_likes,
                total_retweets
            FROM sentiment_hourly_agg
            WHERE date_partition >= today() - {days}
            ORDER BY hour_timestamp DESC
            LIMIT 168  -- 7 días * 24 horas
            """
            
            results = self.client.execute(query)
            
            trends = []
            for row in results:
                trends.append({
                    'timestamp': row[0].isoformat(),
                    'total_tweets': row[1],
                    'positive_tweets': row[2],
                    'neutral_tweets': row[3],
                    'negative_tweets': row[4],
                    'avg_confidence': round(row[5], 3) if row[5] else 0,
                    'total_likes': row[6],
                    'total_retweets': row[7]
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Error obteniendo tendencias horarias: {e}")
            return []
    
    def get_top_influencers(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Obtener top influencers por engagement"""
        try:
            query = f"""
            SELECT 
                author_id,
                count() as tweet_count,
                sum(like_count + retweet_count) as total_engagement,
                avg(confidence) as avg_confidence,
                countIf(predicted_sentiment = 'positive') / count() as positive_rate
            FROM sentiment_analysis
            WHERE processing_timestamp >= now() - INTERVAL {hours} HOUR
            GROUP BY author_id
            HAVING tweet_count >= 2
            ORDER BY total_engagement DESC
            LIMIT 10
            """
            
            results = self.client.execute(query)
            
            influencers = []
            for row in results:
                influencers.append({
                    'author_id': row[0],
                    'tweet_count': row[1],
                    'total_engagement': row[2],
                    'avg_confidence': round(row[3], 3),
                    'positive_rate': round(row[4], 3)
                })
            
            return influencers
            
        except Exception as e:
            logger.error(f"Error obteniendo top influencers: {e}")
            return []
    
    def generate_full_report(self) -> Dict[str, Any]:
        """Generar reporte completo"""
        logger.info("Generando reporte completo de métricas...")
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'pipeline_health': self.get_pipeline_health_metrics(),
            'trending_topics': self.get_trending_topics(24),
            'hourly_trends': self.get_hourly_trends(7),
            'top_influencers': self.get_top_influencers(24)
        }
        
        return report
    
    def save_report_to_file(self, report: Dict[str, Any], filename: str = None):
        """Guardar reporte a archivo JSON"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'/tmp/sentiment_report_{timestamp}.json'
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Reporte guardado en: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")
            return None
    
    def print_summary(self, report: Dict[str, Any]):
        """Imprimir resumen del reporte"""
        health = report.get('pipeline_health', {})
        period_24h = health.get('period_24h', {})
        
        print("\n" + "="*60)
        print("📊 REPORTE DE ANÁLISIS DE SENTIMIENTOS")
        print("="*60)
        print(f"🕐 Timestamp: {report.get('report_timestamp', 'N/A')}")
        print(f"🏥 Estado: {health.get('health_status', 'UNKNOWN')}")
        print("\n📈 MÉTRICAS 24H:")
        print(f"  • Total tweets: {period_24h.get('total_tweets', 0):,}")
        print(f"  • Positivos: {period_24h.get('positive_tweets', 0):,} ({period_24h.get('positive_rate_pct', 0)}%)")
        print(f"  • Negativos: {period_24h.get('negative_tweets', 0):,} ({period_24h.get('negative_rate_pct', 0)}%)")
        print(f"  • Confianza promedio: {period_24h.get('avg_confidence', 0)}")
        print(f"  • Total likes: {period_24h.get('total_likes', 0):,}")
        print(f"  • Total retweets: {period_24h.get('total_retweets', 0):,}")
        
        trending = report.get('trending_topics', [])
        if trending:
            print(f"\n🔥 TOP 5 TRENDING:")
            for i, topic in enumerate(trending[:5], 1):
                print(f"  {i}. {topic['word']} ({topic['total_mentions']} menciones)")
        
        print("="*60)


def main():
    """Función principal"""
    reporter = MetricsReporter()
    
    try:
        # Generar reporte completo
        report = reporter.generate_full_report()
        
        # Imprimir resumen
        reporter.print_summary(report)
        
        # Guardar a archivo
        filename = reporter.save_report_to_file(report)
        
        if filename:
            logger.info(f"✅ Reporte generado exitosamente: {filename}")
        else:
            logger.error("❌ Error generando reporte")
            
    except Exception as e:
        logger.error(f"Error en generación de reporte: {e}")
        raise


if __name__ == "__main__":
    main()