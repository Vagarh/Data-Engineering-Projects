"""
Twitter Producer - Ingesta datos de Twitter API y los envía a Kafka
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

import tweepy
from kafka import KafkaProducer
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class TwitterProducer:
    def __init__(self):
        self.kafka_producer = self._setup_kafka()
        self.twitter_client = self._setup_twitter()
        self.topic = os.getenv('KAFKA_TOPIC_TWEETS', 'raw_tweets')
        self.keywords = os.getenv('SEARCH_KEYWORDS', 'bitcoin,ethereum').split(',')
        
    def _setup_kafka(self) -> KafkaProducer:
        """Configurar productor de Kafka"""
        return KafkaProducer(
            bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            batch_size=16384,
            linger_ms=10
        )
    
    def _setup_twitter(self) -> tweepy.Client:
        """Configurar cliente de Twitter API v2"""
        return tweepy.Client(
            bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
            consumer_key=os.getenv('TWITTER_API_KEY'),
            consumer_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
            wait_on_rate_limit=True
        )
    
    def format_tweet(self, tweet: tweepy.Tweet) -> Dict[str, Any]:
        """Formatear tweet para envío a Kafka"""
        return {
            'id': tweet.id,
            'text': tweet.text,
            'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
            'author_id': tweet.author_id,
            'public_metrics': tweet.public_metrics,
            'lang': getattr(tweet, 'lang', 'unknown'),
            'possibly_sensitive': getattr(tweet, 'possibly_sensitive', False),
            'context_annotations': getattr(tweet, 'context_annotations', []),
            'ingestion_timestamp': datetime.utcnow().isoformat(),
            'source': 'twitter_api'
        }
    
    def send_to_kafka(self, tweet_data: Dict[str, Any]):
        """Enviar tweet a Kafka"""
        try:
            future = self.kafka_producer.send(
                self.topic,
                key=str(tweet_data['id']),
                value=tweet_data
            )
            
            # Callback para manejar éxito/error
            future.add_callback(self._on_send_success)
            future.add_errback(self._on_send_error)
            
        except Exception as e:
            logger.error(f"Error enviando tweet a Kafka: {e}")
    
    def _on_send_success(self, record_metadata):
        """Callback para envío exitoso"""
        logger.debug(f"Tweet enviado a {record_metadata.topic}:{record_metadata.partition}:{record_metadata.offset}")
    
    def _on_send_error(self, excp):
        """Callback para error en envío"""
        logger.error(f"Error enviando tweet: {excp}")
    
    def stream_tweets(self):
        """Stream tweets en tiempo real usando Twitter API v2"""
        logger.info(f"Iniciando stream de tweets para keywords: {self.keywords}")
        
        try:
            # Buscar tweets recientes
            for keyword in self.keywords:
                logger.info(f"Buscando tweets para: {keyword}")
                
                tweets = tweepy.Paginator(
                    self.twitter_client.search_recent_tweets,
                    query=f"{keyword} -is:retweet lang:en",
                    tweet_fields=['created_at', 'author_id', 'public_metrics', 'lang', 'possibly_sensitive', 'context_annotations'],
                    max_results=100
                ).flatten(limit=1000)
                
                for tweet in tweets:
                    tweet_data = self.format_tweet(tweet)
                    self.send_to_kafka(tweet_data)
                    logger.info(f"Tweet procesado: {tweet.id}")
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Error en stream de tweets: {e}")
            raise
    
    def run_continuous(self, interval_seconds: int = 60):
        """Ejecutar producer de forma continua"""
        logger.info(f"Iniciando producer continuo con intervalo de {interval_seconds} segundos")
        
        while True:
            try:
                self.stream_tweets()
                logger.info(f"Esperando {interval_seconds} segundos antes del siguiente batch...")
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Deteniendo producer...")
                break
            except Exception as e:
                logger.error(f"Error en producer continuo: {e}")
                time.sleep(30)  # Esperar antes de reintentar
    
    def close(self):
        """Cerrar conexiones"""
        if self.kafka_producer:
            self.kafka_producer.flush()
            self.kafka_producer.close()
        logger.info("Producer cerrado")


if __name__ == "__main__":
    producer = TwitterProducer()
    
    try:
        producer.run_continuous(interval_seconds=60)
    except KeyboardInterrupt:
        logger.info("Deteniendo aplicación...")
    finally:
        producer.close()