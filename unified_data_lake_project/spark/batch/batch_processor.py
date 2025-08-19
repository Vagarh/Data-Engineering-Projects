
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit
from delta.tables import DeltaTable

if __name__ == "__main__":
    spark = (
        SparkSession.builder.appName("BatchProcessor")
        .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )

    # Path to the unified Delta table, same as the streaming job
    DELTA_TABLE_PATH = "/opt/bitnami/spark/data/delta/price_events"
    
    # Path to the historical data
    CSV_PATH = "/opt/bitnami/spark/data/batch_csvs/*.csv"

    print(f"Reading historical data from {CSV_PATH}")

    # Read the CSV data
    batch_df = spark.read.format("csv").option("header", "true").option("inferSchema", "true").load(CSV_PATH)

    # Transform the data to match the Delta table schema
    # and add the source column
    transformed_df = (
        batch_df.withColumnRenamed("coin_name", "coin")
        .withColumnRenamed("price_usd", "price")
        .withColumnRenamed("trade_timestamp", "event_timestamp")
        .withColumn("source", lit("batch"))
    )

    print("Checking if Delta table exists...")
    # Check if the Delta table already exists
    if DeltaTable.isDeltaTable(spark, DELTA_TABLE_PATH):
        print("Delta table found. Merging data...")
        delta_table = DeltaTable.forPath(spark, DELTA_TABLE_PATH)

        # --- MERGE Operation --- #
        # This is the core of the integration. It ensures idempotency.
        # If a record from the batch source with the same trade_id already exists,
        # it will NOT be inserted again.
        # The schema will be automatically evolved to include trade_id if it doesn't exist.
        (
            delta_table.alias("target")
            .merge(
                transformed_df.alias("source"),
                "target.source = 'batch' AND target.trade_id = source.trade_id"
            )
            .whenNotMatchedInsertAll()
            .execute()
        )
        print("Merge operation completed.")
    else:
        print("Delta table not found. Creating new table...")
        # If the table doesn't exist, create it for the first time
        transformed_df.write.format("delta").mode("overwrite").save(DELTA_TABLE_PATH)
        print("New Delta table created.")

    print("Batch processing job finished.")
    spark.stop()
