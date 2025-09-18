"""
Spark Streaming Job - Procesa tweets de Kafka y aplica análisis de sentimientos
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.streaming import StreamingQuery

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentimentStreamProcessor:
    def __init__(self):
        self.spark = self._create_spark_session()
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.input_topic = os.getenv('KAFKA_TOPIC_TWEETS', 'raw_tweets')
        self.output_topic = os.getenv('KAFKA_TOPIC_SENTIMENTS', 'processed_sentiments')
        self.clickhouse_url = f"jdbc:clickhouse://{os.getenv('CLICKHOUSE_HOST', 'localhost')}:{os.getenv('CLICKHOUSE_PORT', '8123')}/{os.getenv('CLICKHOUSE_DATABASE', 'sentiment_db')}"
        
        # Definir esquemas
        self.tweet_schema = self._define_tweet_schema()
        self.sentiment_schema = self._define_sentiment_schema()
    
    def _create_spark_session(self) -> SparkSession:
        """Crear sesión de Spark con configuraciones optimizadas"""
        return SparkSession.builder \
            .appName("SentimentAnalysisStreaming") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoint") \
            .config("spark.sql.streaming.stateStore.maintenanceInterval", "60s") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
    
    def _define_tweet_schema(self) -> StructType:
        """Definir esquema para tweets de entrada"""
        return StructType([
            StructField("id", StringType(), True),
            StructField("text", StringType(), True),
            StructField("created_at", StringType(), True),
            StructField("author_id", StringType(), True),
            StructField("public_metrics", MapType(StringType(), IntegerType()), True),
            StructField("lang", StringType(), True),
            StructField("possibly_sensitive", BooleanType(), True),
            StructField("context_annotations", ArrayType(MapType(StringType(), StringType())), True),
            StructField("ingestion_timestamp", StringType(), True),
            StructField("source", StringType(), True)
        ])
    
    def _define_sentiment_schema(self) -> StructType:
        """Definir esquema para datos procesados"""
        return StructType([
            StructField("tweet_id", StringType(), False),
            StructField("text", StringType(), True),
            StructField("created_at", TimestampType(), True),
            StructField("author_id", StringType(), True),
            StructField("lang", StringType(), True),
            StructField("retweet_count", IntegerType(), True),
            StructField("like_count", IntegerType(), True),
            StructField("reply_count", IntegerType(), True),
            StructField("quote_count", IntegerType(), True),
            StructField("sentiment_positive", DoubleType(), True),
            StructField("sentiment_neutral", DoubleType(), True),
            StructField("sentiment_negative", DoubleType(), True),
            StructField("predicted_sentiment", StringType(), True),
            StructField("confidence", DoubleType(), True),
            StructField("processing_timestamp", TimestampType(), True),
            StructField("date_partition", DateType(), True)
        ])
    
    def read_from_kafka(self):
        """Leer stream de tweets desde Kafka"""
        return self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_servers) \
            .option("subscribe", self.input_topic) \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()
    
    def parse_tweets(self, kafka_df):
        """Parsear tweets desde formato Kafka"""
        return kafka_df \
            .select(
                col("key").cast("string").alias("tweet_key"),
                from_json(col("value").cast("string"), self.tweet_schema).alias("tweet_data"),
                col("timestamp").alias("kafka_timestamp")
            ) \
            .select("tweet_data.*", "kafka_timestamp")
    
    def analyze_sentiment_udf(self):
        """UDF para análisis de sentimientos"""
        def analyze_sentiment(text):
            if not text:
                return {
                    'positive': 0.33,
                    'neutral': 0.34,
                    'negative': 0.33,
                    'predicted_sentiment': 'neutral',
                    'confidence': 0.34
                }
            
            # Aquí iría la lógica del modelo ML
            # Por simplicidad, usamos reglas básicas
            text_lower = text.lower()
            
            positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'best', 'awesome', '🚀', '💎', '📈']
            negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'crash', 'dump', '📉', '😰', '💸']
            
            positive_score = sum(1 for word in positive_words if word in text_lower) / len(positive_words)
            negative_score = sum(1 for word in negative_words if word in text_lower) / len(negative_words)
            neutral_score = 1 - positive_score - negative_score
            
            # Normalizar scores
            total = positive_score + negative_score + neutral_score
            if total > 0:
                positive_score /= total
                negative_score /= total
                neutral_score /= total
            else:
                positive_score = negative_score = neutral_score = 0.33
            
            # Determinar sentimiento predicho
            scores = {
                'positive': positive_score,
                'neutral': neutral_score,
                'negative': negative_score
            }
            predicted_sentiment = max(scores, key=scores.get)
            confidence = scores[predicted_sentiment]
            
            return {
                'positive': positive_score,
                'neutral': neutral_score,
                'negative': negative_score,
                'predicted_sentiment': predicted_sentiment,
                'confidence': confidence
            }
        
        # Definir esquema de retorno para UDF
        sentiment_return_schema = StructType([
            StructField("positive", DoubleType(), True),
            StructField("neutral", DoubleType(), True),
            StructField("negative", DoubleType(), True),
            StructField("predicted_sentiment", StringType(), True),
            StructField("confidence", DoubleType(), True)
        ])
        
        return udf(analyze_sentiment, sentiment_return_schema)
    
    def process_tweets(self, tweets_df):
        """Procesar tweets y aplicar análisis de sentimientos"""
        sentiment_udf = self.analyze_sentiment_udf()
        
        return tweets_df \
            .filter(col("text").isNotNull()) \
            .withColumn("sentiment_analysis", sentiment_udf(col("text"))) \
            .select(
                col("id").alias("tweet_id"),
                col("text"),
                to_timestamp(col("created_at")).alias("created_at"),
                col("author_id"),
                col("lang"),
                coalesce(col("public_metrics.retweet_count"), lit(0)).alias("retweet_count"),
                coalesce(col("public_metrics.like_count"), lit(0)).alias("like_count"),
                coalesce(col("public_metrics.reply_count"), lit(0)).alias("reply_count"),
                coalesce(col("public_metrics.quote_count"), lit(0)).alias("quote_count"),
                col("sentiment_analysis.positive").alias("sentiment_positive"),
                col("sentiment_analysis.neutral").alias("sentiment_neutral"),
                col("sentiment_analysis.negative").alias("sentiment_negative"),
                col("sentiment_analysis.predicted_sentiment").alias("predicted_sentiment"),
                col("sentiment_analysis.confidence").alias("confidence"),
                current_timestamp().alias("processing_timestamp"),
                to_date(coalesce(to_timestamp(col("created_at")), current_timestamp())).alias("date_partition")
            )
    
    def write_to_clickhouse(self, processed_df):
        """Escribir datos procesados a ClickHouse"""
        def write_batch_to_clickhouse(batch_df, batch_id):
            try:
                logger.info(f"Escribiendo batch {batch_id} a ClickHouse")
                
                batch_df.write \
                    .format("jdbc") \
                    .option("url", self.clickhouse_url) \
                    .option("dbtable", "sentiment_analysis") \
                    .option("user", os.getenv('CLICKHOUSE_USER', 'admin')) \
                    .option("password", os.getenv('CLICKHOUSE_PASSWORD', 'password')) \
                    .option("driver", "com.clickhouse.jdbc.ClickHouseDriver") \
                    .mode("append") \
                    .save()
                
                logger.info(f"Batch {batch_id} escrito exitosamente")
                
            except Exception as e:
                logger.error(f"Error escribiendo batch {batch_id}: {e}")
        
        return processed_df.writeStream \
            .foreachBatch(write_batch_to_clickhouse) \
            .outputMode("append") \
            .trigger(processingTime='30 seconds') \
            .option("checkpointLocation", "/tmp/spark-checkpoint-clickhouse")
    
    def write_to_kafka(self, processed_df):
        """Escribir datos procesados a Kafka para downstream consumers"""
        kafka_output = processed_df \
            .select(
                col("tweet_id").alias("key"),
                to_json(struct("*")).alias("value")
            )
        
        return kafka_output.writeStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_servers) \
            .option("topic", self.output_topic) \
            .outputMode("append") \
            .trigger(processingTime='10 seconds') \
            .option("checkpointLocation", "/tmp/spark-checkpoint-kafka")
    
    def run_streaming_job(self):
        """Ejecutar job de streaming completo"""
        logger.info("Iniciando job de streaming de análisis de sentimientos")
        
        try:
            # Leer tweets desde Kafka
            kafka_stream = self.read_from_kafka()
            
            # Parsear tweets
            tweets_df = self.parse_tweets(kafka_stream)
            
            # Procesar tweets y analizar sentimientos
            processed_df = self.process_tweets(tweets_df)
            
            # Escribir a ClickHouse
            clickhouse_query = self.write_to_clickhouse(processed_df)
            
            # Escribir a Kafka para downstream
            kafka_query = self.write_to_kafka(processed_df)
            
            # Iniciar queries
            clickhouse_query.start()
            kafka_query.start()
            
            # Esperar terminación
            self.spark.streams.awaitAnyTermination()
            
        except Exception as e:
            logger.error(f"Error en streaming job: {e}")
            raise
        finally:
            self.spark.stop()


if __name__ == "__main__":
    processor = SentimentStreamProcessor()
    
    try:
        processor.run_streaming_job()
    except KeyboardInterrupt:
        logger.info("Deteniendo streaming job...")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        raise