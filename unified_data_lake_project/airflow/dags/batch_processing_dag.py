
from airflow.decorators import dag
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
import pendulum

@dag(
    dag_id="daily_batch_processing_dag",
    schedule="@daily",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    doc_md="""
    This DAG orchestrates the daily execution of the Spark batch processing job.
    It submits the batch_processor.py script to the Spark cluster.
    """,
    tags=["data-engineering", "spark", "batch"],
)
def daily_batch_processing_dag():
    """
    ### Batch Processing DAG

    This DAG is responsible for running the daily Spark job that processes historical data.
    It relies on a Spark connection configured in the Airflow UI.
    **Connection ID:** `spark_default`
    **Connection Type:** `Spark`
    **Host:** `spark://spark-master`
    **Port:** `7077`
    """
    SparkSubmitOperator(
        task_id="submit_batch_job_to_spark",
        application="/opt/bitnami/spark/jobs/batch/batch_processor.py",
        conn_id="spark_default",
        packages="io.delta:delta-spark_2.12:3.1.0",
        verbose=True,
    )

daily_batch_processing_dag()
