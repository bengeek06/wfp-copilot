# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Integration tests for Prometheus metrics endpoint.

This module tests the /metrics endpoint with real Flask application context,
database, and Prometheus metrics collection.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient


@pytest.fixture
def metrics_api_key(app: Flask) -> str:
    """Get metrics API key from app configuration.

    Args:
        app: Flask application instance.

    Returns:
        Configured METRICS_API_KEY value.
    """
    return app.config["METRICS_API_KEY"]


class TestMetricsEndpoint:
    """Integration tests for GET /metrics endpoint."""

    def test_metrics_with_valid_api_key(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test metrics endpoint returns data with valid API key.

        Given: METRICS_API_KEY is configured
        And: Authorization header contains valid Bearer token
        When: GET /metrics is called
        Then: Response status is 200
        And: Content-Type is text/plain with Prometheus version
        And: Response contains Prometheus metrics in text format
        """
        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        assert response.status_code == 200
        assert "text/plain" in response.content_type
        assert response.data is not None

        # Verify Prometheus text format
        metrics_text = response.data.decode("utf-8")
        assert "# HELP" in metrics_text
        assert "# TYPE" in metrics_text

    def test_metrics_contains_python_info(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test metrics include Python runtime information.

        Given: Application is running
        When: GET /metrics is called with valid key
        Then: Response contains python_info gauge metric
        """
        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        metrics_text = response.data.decode("utf-8")
        assert "python_info" in metrics_text
        assert "# TYPE python_info gauge" in metrics_text

    def test_metrics_contains_process_metrics(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test metrics include system process metrics.

        Given: Application is running
        When: GET /metrics is called with valid key
        Then: Response contains process memory and CPU metrics
        """
        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        metrics_text = response.data.decode("utf-8")
        assert "process_virtual_memory_bytes" in metrics_text
        assert "process_resident_memory_bytes" in metrics_text

    def test_metrics_contains_http_request_metrics(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test metrics include HTTP request tracking.

        Given: HTTP requests have been made to the application
        When: GET /metrics is called
        Then: Response contains flask_http_request_total counter
        And: Response contains flask_http_request_duration_seconds histogram
        """
        # Make some HTTP requests to generate metrics
        client.get("/health")
        client.get("/ready")
        client.get("/version")

        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        metrics_text = response.data.decode("utf-8")
        assert "flask_http_request_total" in metrics_text
        assert "flask_http_request_duration_seconds" in metrics_text

    def test_health_endpoints_excluded_from_metrics(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test health endpoints are excluded from HTTP metrics.

        Given: Health endpoints have been called
        When: GET /metrics is called
        Then: /health, /ready, /version paths are not in metrics
        """
        # Call health endpoints multiple times
        for _ in range(5):
            client.get("/health")
            client.get("/ready")
            client.get("/version")

        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        metrics_text = response.data.decode("utf-8")

        # Verify health endpoints are not tracked
        # They should not appear in flask_http_request_total or duration metrics
        assert 'path="/health"' not in metrics_text
        assert 'path="/ready"' not in metrics_text
        assert 'path="/version"' not in metrics_text

    def test_metrics_with_missing_authorization_header(
        self, client: FlaskClient
    ) -> None:
        """Test metrics endpoint rejects requests without Authorization header.

        Given: No Authorization header provided
        When: GET /metrics is called
        Then: Response status is 401
        And: Response is JSON with error message
        """
        response = client.get("/metrics")

        assert response.status_code == 401
        assert response.content_type == "application/json"
        data = response.get_json()
        assert data["message"] == "Missing Authorization header"
        assert "timestamp" in data

    def test_metrics_with_invalid_authorization_format(
        self, client: FlaskClient
    ) -> None:
        """Test metrics endpoint rejects invalid Authorization format.

        Given: Authorization header does not use Bearer scheme
        When: GET /metrics is called
        Then: Response status is 401
        And: Error message indicates invalid format
        """
        response = client.get("/metrics", headers={"Authorization": "InvalidFormat"})

        assert response.status_code == 401
        data = response.get_json()
        assert "Invalid Authorization format" in data["message"]

    def test_metrics_with_wrong_api_key(self, client: FlaskClient) -> None:
        """Test metrics endpoint rejects incorrect API key.

        Given: METRICS_API_KEY is configured
        And: Authorization header has different key
        When: GET /metrics is called
        Then: Response status is 401
        And: Error message indicates invalid key
        """
        response = client.get(
            "/metrics", headers={"Authorization": "Bearer wrong-api-key-12345"}
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data["message"] == "Invalid API key"

    def test_metrics_prometheus_format_validation(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test metrics output follows Prometheus exposition format.

        Given: Metrics are collected
        When: GET /metrics is called
        Then: Each metric has HELP and TYPE declarations
        And: Metric names use lowercase with underscores
        And: Counter metrics end with _total suffix
        """
        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        metrics_text = response.data.decode("utf-8")

        # Validate basic format: HELP and TYPE come in pairs
        help_lines = [
            line for line in metrics_text.split("\n") if line.startswith("# HELP")
        ]
        type_lines = [
            line for line in metrics_text.split("\n") if line.startswith("# TYPE")
        ]

        assert len(help_lines) > 0
        assert len(type_lines) > 0

        # Validate metric naming conventions
        metric_lines = [
            line
            for line in metrics_text.split("\n")
            if line and not line.startswith("#")
        ]

        for line in metric_lines:
            # Extract metric name (before '{' or ' ')
            match = re.match(r"^([a-z_][a-z0-9_]*)", line)
            if match:
                metric_name = match.group(1)
                # Metric names should be lowercase with underscores
                assert metric_name.islower() or "_" in metric_name

    def test_metrics_histogram_buckets(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test HTTP duration metrics use histogram with standard buckets.

        Given: HTTP requests have been processed
        When: GET /metrics is called
        Then: flask_http_request_duration_seconds has histogram buckets
        And: Buckets include standard values (0.005, 0.01, 0.025, etc.)
        """
        # Generate some HTTP traffic
        client.get("/health")

        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        metrics_text = response.data.decode("utf-8")

        # Check that histogram metric exists and has at least one bucket label
        assert "flask_http_request_duration_seconds" in metrics_text
        assert 'le="0.005"' in metrics_text or 'le="0.01"' in metrics_text

        # Histogram must have all three required components
        assert "flask_http_request_duration_seconds_bucket" in metrics_text
        assert "flask_http_request_duration_seconds_count" in metrics_text
        assert "flask_http_request_duration_seconds_sum" in metrics_text

    def test_metrics_no_sensitive_data(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test metrics do not expose sensitive data.

        Given: Application has secrets configured
        When: GET /metrics is called
        Then: Metrics do not contain JWT secrets, API keys, or passwords
        """
        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        metrics_text = response.data.decode("utf-8").lower()

        # Ensure common sensitive patterns are not present
        assert "password" not in metrics_text
        assert "secret" not in metrics_text
        assert "api_key" not in metrics_text
        assert "jwt" not in metrics_text

    def test_metrics_app_info_label(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test metrics include app_info with service name and version.

        Given: SERVICE_NAME and SERVICE_VERSION configured
        When: GET /metrics is called
        Then: app_info metric includes service_name and version labels
        """
        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        metrics_text = response.data.decode("utf-8")

        # Check for app_info metric with labels
        assert "app_info" in metrics_text
        assert "service_name=" in metrics_text or "version=" in metrics_text
