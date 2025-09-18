-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS sentiment_db;

-- Usar la base de datos
USE sentiment_db;

-- Tabla principal para análisis de sentimientos
CREATE TABLE IF NOT EXISTS sentiment_analysis (
    tweet_id String,
    text String,
    created_at DateTime,
    author_id String,
    lang String,
    retweet_count UInt32,
    like_count UInt32,
    reply_count UInt32,
    quote_count UInt32,
    sentiment_positive Float64,
    sentiment_neutral Float64,
    sentiment_negative Float64,
    predicted_sentiment String,
    confidence Float64,
    processing_timestamp DateTime,
    date_partition Date
) ENGINE = MergeTree()
PARTITION BY date_partition
ORDER BY (date_partition, created_at, tweet_id)
SETTINGS index_granularity = 8192;

-- Tabla agregada por hora para métricas rápidas
CREATE TABLE IF NOT EXISTS sentiment_hourly_agg (
    hour_timestamp DateTime,
    date_partition Date,
    total_tweets UInt64,
    positive_tweets UInt64,
    neutral_tweets UInt64,
    negative_tweets UInt64,
    avg_positive_score Float64,
    avg_neutral_score Float64,
    avg_negative_score Float64,
    avg_confidence Float64,
    total_likes UInt64,
    total_retweets UInt64,
    unique_authors UInt64
) ENGINE = SummingMergeTree()
PARTITION BY date_partition
ORDER BY (date_partition, hour_timestamp)
SETTINGS index_granularity = 8192;

-- Vista materializada para agregaciones por hora
CREATE MATERIALIZED VIEW IF NOT EXISTS sentiment_hourly_mv TO sentiment_hourly_agg AS
SELECT
    toStartOfHour(created_at) as hour_timestamp,
    date_partition,
    count() as total_tweets,
    countIf(predicted_sentiment = 'positive') as positive_tweets,
    countIf(predicted_sentiment = 'neutral') as neutral_tweets,
    countIf(predicted_sentiment = 'negative') as negative_tweets,
    avg(sentiment_positive) as avg_positive_score,
    avg(sentiment_neutral) as avg_neutral_score,
    avg(sentiment_negative) as avg_negative_score,
    avg(confidence) as avg_confidence,
    sum(like_count) as total_likes,
    sum(retweet_count) as total_retweets,
    uniq(author_id) as unique_authors
FROM sentiment_analysis
GROUP BY hour_timestamp, date_partition;

-- Tabla para trending topics
CREATE TABLE IF NOT EXISTS trending_topics (
    date_partition Date,
    hour_timestamp DateTime,
    keyword String,
    mention_count UInt64,
    positive_mentions UInt64,
    neutral_mentions UInt64,
    negative_mentions UInt64,
    avg_sentiment_score Float64
) ENGINE = SummingMergeTree()
PARTITION BY date_partition
ORDER BY (date_partition, hour_timestamp, keyword)
SETTINGS index_granularity = 8192;

-- Tabla para métricas de autores influyentes
CREATE TABLE IF NOT EXISTS author_metrics (
    date_partition Date,
    author_id String,
    total_tweets UInt64,
    total_likes UInt64,
    total_retweets UInt64,
    avg_sentiment_score Float64,
    follower_impact_score Float64
) ENGINE = ReplacingMergeTree()
PARTITION BY date_partition
ORDER BY (date_partition, author_id)
SETTINGS index_granularity = 8192;

-- Índices para optimizar consultas
-- Índice para búsquedas por sentimiento
ALTER TABLE sentiment_analysis ADD INDEX idx_sentiment predicted_sentiment TYPE set(0) GRANULARITY 1;

-- Índice para búsquedas por idioma
ALTER TABLE sentiment_analysis ADD INDEX idx_lang lang TYPE set(0) GRANULARITY 1;

-- Índice para búsquedas por texto (para análisis de palabras clave)
ALTER TABLE sentiment_analysis ADD INDEX idx_text_bloom text TYPE bloom_filter(0.01) GRANULARITY 1;

-- Crear usuario para Grafana (opcional)
CREATE USER IF NOT EXISTS grafana_user IDENTIFIED BY 'grafana_password';
GRANT SELECT ON sentiment_db.* TO grafana_user;

-- Insertar datos de ejemplo para testing
INSERT INTO sentiment_analysis VALUES
('1234567890', 'I love this new crypto project! Amazing technology 🚀', '2024-01-15 10:30:00', 'user123', 'en', 5, 25, 3, 1, 0.85, 0.10, 0.05, 'positive', 0.85, now(), '2024-01-15'),
('1234567891', 'This market crash is terrible. Lost so much money 😰', '2024-01-15 11:15:00', 'user456', 'en', 12, 8, 15, 2, 0.05, 0.15, 0.80, 'negative', 0.80, now(), '2024-01-15'),
('1234567892', 'Bitcoin price is stable today, nothing much happening', '2024-01-15 12:00:00', 'user789', 'en', 2, 5, 1, 0, 0.20, 0.70, 0.10, 'neutral', 0.70, now(), '2024-01-15');

-- Comentarios para documentación
COMMENT ON TABLE sentiment_analysis IS 'Tabla principal que almacena tweets procesados con análisis de sentimientos';
COMMENT ON TABLE sentiment_hourly_agg IS 'Agregaciones por hora para dashboards y métricas rápidas';
COMMENT ON TABLE trending_topics IS 'Temas trending basados en menciones y sentimientos';
COMMENT ON TABLE author_metrics IS 'Métricas de autores influyentes y su impacto';