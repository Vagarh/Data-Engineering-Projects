import pandas as pd
import s3fs
import os

# MinIO connection details
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = "raw-data"
LOCAL_CSV_FILE = "/opt/airflow/scripts/USvideos.csv" # Assuming the file is here for now

def ingest_data_to_minio():
    print(f"Attempting to ingest data from {LOCAL_CSV_FILE} to MinIO bucket {MINIO_BUCKET}")

    # Ensure the local CSV file exists (for testing purposes)
    if not os.path.exists(LOCAL_CSV_FILE):
        print(f"Error: Local CSV file not found at {LOCAL_CSV_FILE}. Please place a sample CSV there.")
        # For a real pipeline, you'd add logic to download from Kaggle here.
        # For now, we'll create a dummy file if it doesn't exist for demonstration.
        print("Creating a dummy CSV file for demonstration.")
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
        print("Dummy CSV created.")


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
        print(f"Successfully read {len(df)} rows from {LOCAL_CSV_FILE}")

        # Write the DataFrame to MinIO
        with fs.open(minio_path, 'wb') as f:
            df.to_csv(f, index=False)
        print(f"Successfully uploaded {LOCAL_CSV_FILE} to MinIO at s3://{minio_path}")

    except Exception as e:
        print(f"Error during data ingestion: {e}")

if __name__ == "__main__":
    ingest_data_to_minio()
