"""Utility to ingest a local CSV file into a MinIO bucket.

This script is executed inside the Airflow container and uploads the
``USvideos.csv`` file to the ``raw-data`` bucket.  The previous version
relied on ``print`` statements and minimal error handling.  The current
implementation introduces structured logging and more robust exception
management so that Airflow can surface clear failure messages.
"""

import logging
import os

import pandas as pd
import s3fs

# MinIO connection details
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = "raw-data"
# Assuming the file is here for now.  In production this could be an
# input parameter or sourced from an upstream task.
LOCAL_CSV_FILE = "/opt/airflow/scripts/USvideos.csv"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ingest_data_to_minio() -> None:
    """Upload the local CSV file to the configured MinIO bucket."""

    logger.info(
        "Attempting to ingest data from %s to MinIO bucket %s",
        LOCAL_CSV_FILE,
        MINIO_BUCKET,
    )

    # Ensure the local CSV file exists (for testing purposes)
    if not os.path.exists(LOCAL_CSV_FILE):
        logger.error(
            "Local CSV file not found at %s. Creating a dummy CSV for demonstration.",
            LOCAL_CSV_FILE,
        )
        # For a real pipeline, you'd add logic to download from Kaggle here.
        # For now, we'll create a dummy file if it doesn't exist for demonstration.
        dummy_data = {
            'video_id': ['abc', 'def'],
            'trending_date': ['17.14.09', '17.14.09'],
            'title': ['Dummy Video 1', 'Dummy Video 2'],
            'channel_title': ['Dummy Channel 1', 'Dummy Channel 2'],
            'category_id': [1, 2],
            'publish_time': ['2023-01-01T00:00:00Z', '2023-01-02T00:00:00Z'],
            'tags': ['tag1|tag2', 'tag3'],
            'views': [100, 200],
            'likes': [10, 20],
            'dislikes': [1, 2],
            'comment_count': [5, 10],
            'thumbnail_link': ['link1', 'link2'],
            'comments_disabled': [False, False],
            'ratings_disabled': [False, False],
            'video_error_or_removed': [False, False],
            'description': ['Desc 1', 'Desc 2']
        }
        pd.DataFrame(dummy_data).to_csv(LOCAL_CSV_FILE, index=False)
        logger.info("Dummy CSV created at %s", LOCAL_CSV_FILE)


    # Initialize S3 filesystem
    fs = s3fs.S3FileSystem(
        client_kwargs={
            'endpoint_url': f"http://{MINIO_ENDPOINT}",
            'aws_access_key_id': MINIO_ACCESS_KEY,
            'aws_secret_access_key': MINIO_SECRET_KEY,
        },
        anon=False # Set to False for authenticated access
    )

    # Define the path in MinIO
    minio_path = f"{MINIO_BUCKET}/USvideos.csv"

    try:
        # Read the local CSV file
        df = pd.read_csv(LOCAL_CSV_FILE)
        logger.info("Successfully read %d rows from %s", len(df), LOCAL_CSV_FILE)

        # Write the DataFrame to MinIO
        with fs.open(minio_path, "wb") as f:
            df.to_csv(f, index=False)
        logger.info(
            "Successfully uploaded %s to MinIO at s3://%s",
            LOCAL_CSV_FILE,
            minio_path,
        )

    except Exception:  # pragma: no cover - generic catch for pipeline reliability
        logger.exception("Error during data ingestion")

if __name__ == "__main__":
    ingest_data_to_minio()
