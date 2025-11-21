"""Feast feature definitions for user features."""

from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float32, Int64, String


# Entity definitions
user = Entity(
    name="user_id",
    description="Unique identifier for users",
)

product = Entity(
    name="product_id",
    description="Unique identifier for products",
)


# Data sources
user_source = FileSource(
    name="user_features_source",
    path="data/user_features.parquet",
    timestamp_field="event_timestamp",
)

product_source = FileSource(
    name="product_features_source",
    path="data/product_features.parquet",
    timestamp_field="event_timestamp",
)


# Feature views
user_features = FeatureView(
    name="user_features",
    entities=[user],
    ttl=timedelta(days=1),
    schema=[
        Field(name="total_purchases", dtype=Int64),
        Field(name="total_spend", dtype=Float32),
        Field(name="avg_purchase_value", dtype=Float32),
        Field(name="days_since_last_purchase", dtype=Int64),
        Field(name="purchase_frequency", dtype=Float32),
    ],
    source=user_source,
    online=True,
    description="User purchase behavior features",
)

product_features = FeatureView(
    name="product_features",
    entities=[product],
    ttl=timedelta(days=1),
    schema=[
        Field(name="price", dtype=Float32),
        Field(name="category", dtype=String),
        Field(name="avg_rating", dtype=Float32),
        Field(name="total_sales", dtype=Int64),
        Field(name="stock_level", dtype=Int64),
    ],
    source=product_source,
    online=True,
    description="Product catalog features",
)
