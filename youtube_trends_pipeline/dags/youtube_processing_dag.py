from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.postgres.hooks.postgres import PostgresHook
import io
import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Define a function for loading data from MinIO to Postgres
def load_minio_to_postgres() -> None:
    """Load raw YouTube data from MinIO to the Postgres data warehouse."""

    try:
        s3_hook = S3Hook(aws_conn_id="minio_s3_conn")  # MinIO connection
        postgres_hook = PostgresHook(postgres_conn_id="postgres_dwh_conn")

        # For simplicity, assuming USvideos.csv is the file
        file_content = s3_hook.read_key(key="USvideos.csv", bucket_name="raw-data")
        df = pd.read_csv(io.StringIO(file_content))

        df.to_sql(
            "raw_youtube_videos",
            postgres_hook.get_sqlalchemy_engine(),
            if_exists="replace",
            index=False,
        )
        logger.info("Data loaded from MinIO to PostgreSQL successfully")
    except Exception:
        logger.exception("Failed to load data from MinIO to PostgreSQL")
        raise


with DAG(
    dag_id='youtube_daily_pipeline',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None, # Run manually for now
    catchup=False,
    tags=['youtube', 'data_engineering', 'dbt'],
) as dag:

    ingest_task = BashOperator(
        task_id='ingest_raw_data',
        bash_command='python /opt/airflow/scripts/ingest_data.py',
        # Ensure the script has access to MinIO env vars if needed, or configure in Airflow connections
    )

    load_to_dwh_task = PythonOperator(
        task_id='load_minio_to_dwh',
        python_callable=load_minio_to_postgres,
    )

    dbt_run_task = BashOperator(
        task_id='run_dbt_models',
        bash_command='dbt run --project-dir /opt/airflow/dbt_youtube --profiles-dir /opt/airflow/dbt_youtube',
    )

    dbt_test_task = BashOperator(
        task_id='test_dbt_models',
        bash_command='dbt test --project-dir /opt/airflow/dbt_youtube --profiles-dir /opt/airflow/dbt_youtube',
    )

    ingest_task >> load_to_dwh_task >> dbt_run_task >> dbt_test_task
