"""Airflow DAG for Feature Store pipeline."""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "feature_store_pipeline",
    default_args=default_args,
    description="Pipeline for computing and materializing ML features",
    schedule_interval="0 */6 * * *",  # Every 6 hours
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["feature-store", "ml"],
)


def compute_user_features():
    """Compute user features from transactions."""
    import pandas as pd
    import numpy as np
    from datetime import datetime

    # Simulated feature computation
    num_users = 1000

    data = {
        "user_id": [f"user_{i}" for i in range(num_users)],
        "total_purchases": np.random.randint(1, 100, num_users),
        "total_spend": np.random.uniform(50, 5000, num_users).round(2),
        "avg_purchase_value": np.random.uniform(10, 200, num_users).round(2),
        "days_since_last_purchase": np.random.randint(0, 365, num_users),
        "purchase_frequency": np.random.uniform(0.1, 5, num_users).round(2),
        "event_timestamp": [datetime.utcnow()] * num_users,
    }

    df = pd.DataFrame(data)
    df.to_parquet("/app/feature_repo/data/user_features.parquet", index=False)

    print(f"Computed features for {num_users} users")
    return num_users


def compute_product_features():
    """Compute product features from catalog."""
    import pandas as pd
    import numpy as np
    from datetime import datetime

    num_products = 500
    categories = ["Electronics", "Clothing", "Home", "Sports", "Books"]

    data = {
        "product_id": [f"product_{i}" for i in range(num_products)],
        "price": np.random.uniform(10, 500, num_products).round(2),
        "category": np.random.choice(categories, num_products),
        "avg_rating": np.random.uniform(1, 5, num_products).round(1),
        "total_sales": np.random.randint(0, 5000, num_products),
        "stock_level": np.random.randint(0, 200, num_products),
        "event_timestamp": [datetime.utcnow()] * num_products,
    }

    df = pd.DataFrame(data)
    df.to_parquet("/app/feature_repo/data/product_features.parquet", index=False)

    print(f"Computed features for {num_products} products")
    return num_products


# Tasks
compute_user_features_task = PythonOperator(
    task_id="compute_user_features",
    python_callable=compute_user_features,
    dag=dag,
)

compute_product_features_task = PythonOperator(
    task_id="compute_product_features",
    python_callable=compute_product_features,
    dag=dag,
)

apply_feast_definitions = BashOperator(
    task_id="apply_feast_definitions",
    bash_command="cd /app/feature_repo && feast apply",
    dag=dag,
)

materialize_features = BashOperator(
    task_id="materialize_features",
    bash_command=(
        "cd /app/feature_repo && "
        "feast materialize-incremental $(date -u +%Y-%m-%dT%H:%M:%S)"
    ),
    dag=dag,
)

# Task dependencies
[compute_user_features_task, compute_product_features_task] >> apply_feast_definitions
apply_feast_definitions >> materialize_features
