"""User feature engineering module."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional
import structlog

logger = structlog.get_logger()


class UserFeatureEngineer:
    """Engineer features for user entities."""

    def __init__(self, transactions_df: Optional[pd.DataFrame] = None):
        """Initialize with transaction data."""
        self.transactions_df = transactions_df

    def compute_user_features(self, user_id: str) -> dict:
        """Compute all features for a single user."""
        if self.transactions_df is None:
            return self._get_default_features(user_id)

        user_txns = self.transactions_df[
            self.transactions_df["user_id"] == user_id
        ]

        if user_txns.empty:
            return self._get_default_features(user_id)

        return {
            "user_id": user_id,
            "total_purchases": len(user_txns),
            "total_spend": float(user_txns["amount"].sum()),
            "avg_purchase_value": float(user_txns["amount"].mean()),
            "max_purchase_value": float(user_txns["amount"].max()),
            "min_purchase_value": float(user_txns["amount"].min()),
            "days_since_first_purchase": self._days_since_first(user_txns),
            "days_since_last_purchase": self._days_since_last(user_txns),
            "purchase_frequency": self._purchase_frequency(user_txns),
            "event_timestamp": datetime.utcnow(),
        }

    def compute_batch_features(self, user_ids: list) -> pd.DataFrame:
        """Compute features for multiple users."""
        features = [self.compute_user_features(uid) for uid in user_ids]
        return pd.DataFrame(features)

    def _get_default_features(self, user_id: str) -> dict:
        """Return default features for unknown users."""
        return {
            "user_id": user_id,
            "total_purchases": 0,
            "total_spend": 0.0,
            "avg_purchase_value": 0.0,
            "max_purchase_value": 0.0,
            "min_purchase_value": 0.0,
            "days_since_first_purchase": -1,
            "days_since_last_purchase": -1,
            "purchase_frequency": 0.0,
            "event_timestamp": datetime.utcnow(),
        }

    def _days_since_first(self, user_txns: pd.DataFrame) -> int:
        """Calculate days since first purchase."""
        first_date = user_txns["timestamp"].min()
        if pd.isna(first_date):
            return -1
        return (datetime.utcnow() - pd.to_datetime(first_date)).days

    def _days_since_last(self, user_txns: pd.DataFrame) -> int:
        """Calculate days since last purchase."""
        last_date = user_txns["timestamp"].max()
        if pd.isna(last_date):
            return -1
        return (datetime.utcnow() - pd.to_datetime(last_date)).days

    def _purchase_frequency(self, user_txns: pd.DataFrame) -> float:
        """Calculate purchases per month."""
        if len(user_txns) < 2:
            return 0.0

        first_date = pd.to_datetime(user_txns["timestamp"].min())
        last_date = pd.to_datetime(user_txns["timestamp"].max())
        months = max((last_date - first_date).days / 30, 1)

        return len(user_txns) / months


def generate_sample_user_features(num_users: int = 100) -> pd.DataFrame:
    """Generate sample user features for testing."""
    np.random.seed(42)

    data = {
        "user_id": [f"user_{i}" for i in range(num_users)],
        "total_purchases": np.random.randint(1, 100, num_users),
        "total_spend": np.random.uniform(50, 5000, num_users).round(2),
        "avg_purchase_value": np.random.uniform(10, 200, num_users).round(2),
        "days_since_last_purchase": np.random.randint(0, 365, num_users),
        "purchase_frequency": np.random.uniform(0.1, 5, num_users).round(2),
        "event_timestamp": [datetime.utcnow()] * num_users,
    }

    return pd.DataFrame(data)
