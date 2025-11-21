"""Product feature engineering module."""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional
import structlog

logger = structlog.get_logger()


class ProductFeatureEngineer:
    """Engineer features for product entities."""

    def __init__(self, products_df: Optional[pd.DataFrame] = None):
        """Initialize with product data."""
        self.products_df = products_df

    def compute_product_features(self, product_id: str) -> dict:
        """Compute all features for a single product."""
        if self.products_df is None:
            return self._get_default_features(product_id)

        product = self.products_df[
            self.products_df["product_id"] == product_id
        ]

        if product.empty:
            return self._get_default_features(product_id)

        row = product.iloc[0]

        return {
            "product_id": product_id,
            "price": float(row.get("price", 0)),
            "category": str(row.get("category", "unknown")),
            "avg_rating": float(row.get("avg_rating", 0)),
            "total_reviews": int(row.get("total_reviews", 0)),
            "total_sales": int(row.get("total_sales", 0)),
            "days_since_launch": self._days_since_launch(row),
            "stock_level": int(row.get("stock_level", 0)),
            "is_active": bool(row.get("is_active", True)),
            "event_timestamp": datetime.utcnow(),
        }

    def compute_batch_features(self, product_ids: list) -> pd.DataFrame:
        """Compute features for multiple products."""
        features = [self.compute_product_features(pid) for pid in product_ids]
        return pd.DataFrame(features)

    def _get_default_features(self, product_id: str) -> dict:
        """Return default features for unknown products."""
        return {
            "product_id": product_id,
            "price": 0.0,
            "category": "unknown",
            "avg_rating": 0.0,
            "total_reviews": 0,
            "total_sales": 0,
            "days_since_launch": -1,
            "stock_level": 0,
            "is_active": False,
            "event_timestamp": datetime.utcnow(),
        }

    def _days_since_launch(self, row: pd.Series) -> int:
        """Calculate days since product launch."""
        launch_date = row.get("launch_date")
        if pd.isna(launch_date):
            return -1
        return (datetime.utcnow() - pd.to_datetime(launch_date)).days


def generate_sample_product_features(num_products: int = 50) -> pd.DataFrame:
    """Generate sample product features for testing."""
    np.random.seed(42)

    categories = ["Electronics", "Clothing", "Home", "Sports", "Books"]

    data = {
        "product_id": [f"product_{i}" for i in range(num_products)],
        "price": np.random.uniform(10, 500, num_products).round(2),
        "category": np.random.choice(categories, num_products),
        "avg_rating": np.random.uniform(1, 5, num_products).round(1),
        "total_reviews": np.random.randint(0, 1000, num_products),
        "total_sales": np.random.randint(0, 5000, num_products),
        "stock_level": np.random.randint(0, 200, num_products),
        "is_active": np.random.choice([True, False], num_products, p=[0.9, 0.1]),
        "event_timestamp": [datetime.utcnow()] * num_products,
    }

    return pd.DataFrame(data)
