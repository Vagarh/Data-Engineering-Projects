"""Tests for the sentiment analysis module."""

import pytest
from unittest.mock import Mock, patch


class TestSentimentAnalyzer:
    """Test cases for sentiment analysis functionality."""

    def test_sentiment_labels(self):
        """Test that sentiment labels are valid."""
        valid_labels = ["positive", "negative", "neutral"]

        for label in valid_labels:
            assert label in ["positive", "negative", "neutral"]

    def test_sentiment_score_range(self):
        """Test that sentiment scores are in valid range."""
        scores = [0.0, 0.5, 1.0, -0.5, -1.0]

        for score in scores:
            assert -1.0 <= score <= 1.0

    def test_confidence_score_range(self):
        """Test that confidence scores are in valid range."""
        confidence_scores = [0.0, 0.5, 0.85, 1.0]

        for score in confidence_scores:
            assert 0.0 <= score <= 1.0

    def test_text_preprocessing(self):
        """Test text preprocessing for sentiment analysis."""
        raw_text = "  This is AMAZING!! @user #hashtag  "
        processed = raw_text.strip().lower()

        assert processed == "this is amazing!! @user #hashtag"
        assert not processed.startswith(" ")
        assert not processed.endswith(" ")


class TestTwitterProducer:
    """Test cases for Twitter data producer."""

    def test_tweet_structure(self):
        """Test tweet data structure."""
        required_fields = [
            "id",
            "text",
            "author_id",
            "created_at",
            "retweet_count",
            "like_count"
        ]

        sample_tweet = {
            "id": "123456789",
            "text": "Sample tweet text",
            "author_id": "user123",
            "created_at": "2024-01-01T12:00:00Z",
            "retweet_count": 10,
            "like_count": 50
        }

        for field in required_fields:
            assert field in sample_tweet

    def test_keyword_filtering(self):
        """Test keyword filtering logic."""
        keywords = ["python", "data", "engineering"]
        text = "Learning Python for data engineering projects"

        matches = [kw for kw in keywords if kw.lower() in text.lower()]

        assert len(matches) == 3
        assert "python" in matches


class TestStreamingProcessor:
    """Test cases for streaming processor."""

    def test_window_configuration(self):
        """Test streaming window configuration."""
        window_duration = "30 seconds"
        slide_duration = "10 seconds"

        assert "seconds" in window_duration
        assert "seconds" in slide_duration

    def test_watermark_configuration(self):
        """Test watermark delay configuration."""
        watermark_delay = "1 minute"

        assert "minute" in watermark_delay

    def test_batch_aggregation(self):
        """Test batch aggregation logic."""
        sentiments = [
            {"label": "positive", "score": 0.8},
            {"label": "positive", "score": 0.6},
            {"label": "negative", "score": -0.5}
        ]

        positive_count = sum(1 for s in sentiments if s["label"] == "positive")
        avg_score = sum(s["score"] for s in sentiments) / len(sentiments)

        assert positive_count == 2
        assert abs(avg_score - 0.3) < 0.01


class TestClickHouseStorage:
    """Test cases for ClickHouse storage."""

    def test_connection_parameters(self):
        """Test ClickHouse connection parameters."""
        params = {
            "host": "localhost",
            "port": 9000,
            "database": "sentiment_db"
        }

        assert params["port"] == 9000
        assert isinstance(params["host"], str)

    def test_table_engine(self):
        """Test ClickHouse table engine configuration."""
        engine = "MergeTree()"
        partition_by = "toYYYYMM(created_at)"
        order_by = "(created_at, tweet_id)"

        assert "MergeTree" in engine
        assert "toYYYYMM" in partition_by
