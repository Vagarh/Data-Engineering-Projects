from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, expr, lit
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

# Schema for the incoming JSON data from Kafka
schema = StructType([
    StructField("bitcoin", StructType([
        StructField("usd", DoubleType(), True)
    ]), True),
    StructField("dogecoin", StructType([
        StructField("usd", DoubleType(), True)
    ]), True),
    StructField("ethereum", StructType([
        StructField("usd", DoubleType(), True)
    ]), True),
    StructField("timestamp", DoubleType(), True)
])

if __name__ == "__main__":
    spark = (
        SparkSession.builder.appName("StreamProcessorRefactored")
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,io.delta:delta-spark_2.12:3.1.0")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )

    # Read from Kafka
    kafka_df = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", "kafka:29092")
        .option("subscribe", "crypto_prices")
        .option("startingOffsets", "latest")
        .load()
    )

    # Parse the JSON data from Kafka
    parsed_df = kafka_df.select(
        from_json(col("value").cast("string"), schema).alias("data")
    ).select("data.*")

    # --- Refactoring for a Scalable Schema ---
    # Unpivot the data to transform it from a wide to a long format.
    # This is a much more scalable approach for adding new coins in the future.
    unpivoted_df = parsed_df.select(
        col("timestamp").alias("event_timestamp"),
        expr("stack(3, 'bitcoin', bitcoin.usd, 'ethereum', ethereum.usd, 'dogecoin', dogecoin.usd) as (coin, price)")
    ).where(col("price").isNotNull())

    # Add a source column to identify the data's origin
    final_df = unpivoted_df.withColumn("source", lit("streaming"))

    # Define the paths for the refactored Delta table and its checkpoint
    DELTA_TABLE_PATH = "/opt/bitnami/spark/data/delta/price_events"
    CHECKPOINT_PATH = "/opt/bitnami/spark/data/checkpoints/price_events"

    # Write the transformed data to the Delta Lake table
    query = (
        final_df.writeStream
        .outputMode("append")
        .format("delta")
        .option("path", DELTA_TABLE_PATH)
        .option("checkpointLocation", CHECKPOINT_PATH)
        .start()
    )

    print(f"Streaming to Delta table {DELTA_TABLE_PATH} started...")
    query.awaitTermination()