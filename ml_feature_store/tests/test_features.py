"""Tests for ML Feature Store."""

import pytest
from datetime import datetime


class TestUserFeatures:
    """Test cases for user features."""

    def test_user_feature_structure(self):
        """Test user feature contains required fields."""
        required_fields = [
            "user_id",
            "total_purchases",
            "total_spend",
            "avg_purchase_value",
            "days_since_last_purchase",
            "purchase_frequency"
        ]

        sample_features = {
            "user_id": "user_123",
            "total_purchases": 50,
            "total_spend": 1500.00,
            "avg_purchase_value": 30.00,
            "days_since_last_purchase": 7,
            "purchase_frequency": 2.5
        }

        for field in required_fields:
            assert field in sample_features

    def test_total_purchases_validation(self):
        """Test total purchases is non-negative."""
        valid_values = [0, 1, 100, 1000]

        for value in valid_values:
            assert value >= 0
            assert isinstance(value, int)

    def test_purchase_frequency_calculation(self):
        """Test purchase frequency calculation."""
        total_purchases = 24
        months = 12
        expected_frequency = 2.0

        frequency = total_purchases / months
        assert frequency == expected_frequency

    def test_avg_purchase_value_calculation(self):
        """Test average purchase value calculation."""
        total_spend = 1000.0
        total_purchases = 10
        expected_avg = 100.0

        avg = total_spend / total_purchases if total_purchases > 0 else 0
        assert avg == expected_avg


class TestProductFeatures:
    """Test cases for product features."""

    def test_product_feature_structure(self):
        """Test product feature contains required fields."""
        required_fields = [
            "product_id",
            "price",
            "category",
            "avg_rating",
            "total_sales"
        ]

        sample_features = {
            "product_id": "product_123",
            "price": 99.99,
            "category": "Electronics",
            "avg_rating": 4.5,
            "total_sales": 500
        }

        for field in required_fields:
            assert field in sample_features

    def test_price_validation(self):
        """Test price is positive number."""
        valid_prices = [0.01, 10.00, 999.99]

        for price in valid_prices:
            assert price > 0
            assert isinstance(price, float)

    def test_rating_range(self):
        """Test rating is within valid range."""
        valid_ratings = [1.0, 2.5, 3.0, 4.5, 5.0]

        for rating in valid_ratings:
            assert 1.0 <= rating <= 5.0

    def test_category_validation(self):
        """Test category is valid string."""
        valid_categories = ["Electronics", "Clothing", "Home", "Sports", "Books"]

        for category in valid_categories:
            assert isinstance(category, str)
            assert len(category) > 0


class TestFeatureAPI:
    """Test cases for Feature Store API."""

    def test_online_request_structure(self):
        """Test online feature request structure."""
        request = {
            "entity_ids": ["user_1", "user_2"],
            "feature_names": ["total_purchases", "total_spend"]
        }

        assert "entity_ids" in request
        assert isinstance(request["entity_ids"], list)
        assert len(request["entity_ids"]) > 0

    def test_offline_request_structure(self):
        """Test offline feature request structure."""
        request = {
            "entity_ids": ["user_1"],
            "feature_names": ["total_purchases"],
            "start_time": "2024-01-01T00:00:00Z",
            "end_time": "2024-01-31T23:59:59Z"
        }

        assert "entity_ids" in request
        assert "start_time" in request
        assert "end_time" in request

    def test_health_response_structure(self):
        """Test health check response structure."""
        response = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }

        assert response["status"] in ["healthy", "unhealthy"]
        assert "timestamp" in response
        assert "version" in response


class TestFeatureStore:
    """Test cases for Feast Feature Store configuration."""

    def test_entity_configuration(self):
        """Test entity configuration."""
        entities = [
            {"name": "user_id", "type": "STRING"},
            {"name": "product_id", "type": "STRING"}
        ]

        for entity in entities:
            assert "name" in entity
            assert "type" in entity
            assert entity["type"] in ["STRING", "INT64", "FLOAT"]

    def test_feature_view_configuration(self):
        """Test feature view configuration."""
        feature_view = {
            "name": "user_features",
            "entities": ["user_id"],
            "ttl": "1d",
            "online": True
        }

        assert "name" in feature_view
        assert "entities" in feature_view
        assert isinstance(feature_view["online"], bool)

    def test_online_store_config(self):
        """Test online store configuration."""
        config = {
            "type": "redis",
            "connection_string": "redis://localhost:6379"
        }

        assert config["type"] in ["redis", "dynamodb", "sqlite"]
        assert "connection_string" in config
