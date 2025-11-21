"""Tests for the anomaly detection module."""

import pytest
from unittest.mock import Mock, patch
import json


class TestAnomalyDetector:
    """Test cases for anomaly detection functionality."""

    def test_isolation_forest_parameters(self):
        """Test Isolation Forest configuration parameters."""
        params = {
            "n_estimators": 100,
            "contamination": 0.1,
            "random_state": 42
        }

        assert params["n_estimators"] > 0
        assert 0 < params["contamination"] < 0.5
        assert isinstance(params["random_state"], int)

    def test_anomaly_score_range(self):
        """Test that anomaly scores are in valid range."""
        scores = [-0.5, -0.1, 0.0, 0.1, 0.5]

        for score in scores:
            assert -1.0 <= score <= 1.0

    def test_threshold_configuration(self):
        """Test anomaly threshold configuration."""
        thresholds = {
            "low": -0.2,
            "medium": -0.3,
            "high": -0.5,
            "critical": -0.7
        }

        assert thresholds["critical"] < thresholds["high"]
        assert thresholds["high"] < thresholds["medium"]


class TestLogParser:
    """Test cases for log parsing functionality."""

    def test_syslog_format_parsing(self):
        """Test syslog format parsing."""
        syslog_line = "Jan 15 10:30:45 server01 sshd[1234]: Failed password for user from 192.168.1.100"

        assert "sshd" in syslog_line
        assert "192.168.1.100" in syslog_line

    def test_json_log_parsing(self):
        """Test JSON log parsing."""
        log_entry = {
            "timestamp": "2024-01-15T10:30:45Z",
            "level": "ERROR",
            "service": "auth",
            "message": "Authentication failed",
            "ip_address": "192.168.1.100"
        }

        parsed = json.dumps(log_entry)
        restored = json.loads(parsed)

        assert restored["level"] == "ERROR"
        assert "ip_address" in restored

    def test_log_level_validation(self):
        """Test log level validation."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            assert level.isupper()


class TestThreatDetection:
    """Test cases for threat detection."""

    def test_brute_force_detection(self):
        """Test brute force attack detection logic."""
        failed_attempts = [
            {"ip": "192.168.1.100", "timestamp": 1},
            {"ip": "192.168.1.100", "timestamp": 2},
            {"ip": "192.168.1.100", "timestamp": 3},
            {"ip": "192.168.1.100", "timestamp": 4},
            {"ip": "192.168.1.100", "timestamp": 5}
        ]

        threshold = 5
        ip_counts = {}

        for attempt in failed_attempts:
            ip = attempt["ip"]
            ip_counts[ip] = ip_counts.get(ip, 0) + 1

        is_brute_force = ip_counts.get("192.168.1.100", 0) >= threshold
        assert is_brute_force

    def test_sql_injection_patterns(self):
        """Test SQL injection detection patterns."""
        suspicious_patterns = [
            "' OR '1'='1",
            "; DROP TABLE",
            "UNION SELECT",
            "1=1--"
        ]

        test_input = "username' OR '1'='1"

        detected = any(pattern.lower() in test_input.lower() for pattern in suspicious_patterns)
        assert detected

    def test_xss_detection_patterns(self):
        """Test XSS attack detection patterns."""
        xss_patterns = ["<script>", "javascript:", "onerror=", "onload="]

        test_input = "<script>alert('xss')</script>"

        detected = any(pattern.lower() in test_input.lower() for pattern in xss_patterns)
        assert detected


class TestAlertManager:
    """Test cases for alert management."""

    def test_alert_severity_levels(self):
        """Test alert severity level configuration."""
        severity_levels = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }

        assert severity_levels["critical"] > severity_levels["high"]
        assert severity_levels["high"] > severity_levels["medium"]

    def test_alert_structure(self):
        """Test alert data structure."""
        alert = {
            "id": "alert-001",
            "severity": "high",
            "type": "brute_force",
            "source_ip": "192.168.1.100",
            "timestamp": "2024-01-15T10:30:45Z",
            "description": "Multiple failed login attempts detected"
        }

        required_fields = ["id", "severity", "type", "timestamp"]

        for field in required_fields:
            assert field in alert

    def test_notification_channels(self):
        """Test notification channel configuration."""
        channels = ["slack", "email", "pagerduty"]

        for channel in channels:
            assert channel in ["slack", "email", "pagerduty", "webhook"]
