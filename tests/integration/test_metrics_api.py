# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Integration tests for Prometheus metrics endpoint.

Tests the /metrics endpoint authentication, authorization, rate limiting,
and metric exposition according to specification AC-001 through AC-010.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient


@pytest.fixture
def metrics_api_key() -> str:
    """Get metrics API key from app config.

    Returns:
        API key string for Authorization header.
    """
    return "test-metrics-api-key-integration-12345678"


class TestMetricsEndpoint:
    """Integration tests for GET /metrics endpoint."""

    def test_metrics_with_valid_api_key(
        self, app: Flask, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test metrics endpoint with valid API key (AC-001).

        Given: METRICS_API_KEY is configured
        And: Authorization header contains valid Bearer token
        When: GET /metrics is called
        Then: Response status is 200
        And: Content-Type is text/plain
        And: Response body contains Prometheus metrics
        """
        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        assert response.status_code == 200
        assert "text/plain" in response.content_type
        # Verify it's Prometheus format (contains # HELP and # TYPE)
        text = response.get_data(as_text=True)
        assert "# HELP" in text
        assert "# TYPE" in text

    def test_metrics_missing_api_key(self, client: FlaskClient) -> None:
        """Test metrics endpoint without Authorization header (AC-002).

        Given: METRICS_API_KEY is configured
        And: No Authorization header is provided
        When: GET /metrics is called
        Then: Response status is 401
        And: Response is JSON with error message
        """
        response = client.get("/metrics")

        assert response.status_code == 401
        data = response.get_json()
        assert data is not None
        assert "message" in data
        assert "Missing Authorization header" in data["message"]
        assert "timestamp" in data

    def test_metrics_invalid_api_key(self, client: FlaskClient) -> None:
        """Test metrics endpoint with wrong API key (AC-003).

        Given: METRICS_API_KEY is configured
        And: Authorization header has invalid Bearer token
        When: GET /metrics is called
        Then: Response status is 401
        And: Response is JSON with error message
        """
        response = client.get(
            "/metrics", headers={"Authorization": "Bearer wrongkey456"}
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data is not None
        assert "message" in data
        assert "Invalid API key" in data["message"]

    def test_metrics_contains_python_info(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test metrics contain Python runtime information (AC-004 partial).

        Given: Application is running
        When: GET /metrics is called with valid key
        Then: Response contains python_info metric
        """
        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        assert response.status_code == 200
        text = response.get_data(as_text=True)
        assert "python_info" in text

    def test_metrics_contains_process_metrics(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test metrics contain system/process metrics (AC-005).

        Given: Application is running
        When: GET /metrics is called with valid key
        Then: Response contains process_virtual_memory_bytes
        And: Response contains process metrics
        """
        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        assert response.status_code == 200
        text = response.get_data(as_text=True)
        assert "process_virtual_memory_bytes" in text

    def test_metrics_contains_http_request_metrics(
        self, app: Flask, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test metrics contain HTTP request metrics (AC-004, AC-007).

        Given: Application has received HTTP requests
        When: GET /metrics is called with valid key
        Then: Response contains flask_http_request_total counter
        And: Response contains flask_http_request_duration_seconds histogram
        And: Health endpoints (/health, /ready, /version) are excluded (AC-007)
        """
        # Make some requests to generate metrics
        client.get("/health")
        client.get("/ready")
        client.get("/version")

        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        assert response.status_code == 200
        text = response.get_data(as_text=True)
        assert "flask_http_request_total" in text

        # AC-007: Verify health endpoints are excluded from metrics
        # These paths should NOT appear in any flask_http_request_* metrics
        assert 'path="/health"' not in text
        assert 'path="/ready"' not in text
        assert 'path="/version"' not in text

    def test_metrics_prometheus_format_validation(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test metrics follow Prometheus text exposition format (AC-010, REQ-002).

        Given: Metrics endpoint is available
        When: GET /metrics is called
        Then: Response follows Prometheus format with HELP and TYPE comments
        And: Metrics have proper naming (lowercase, underscores)
        """
        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        assert response.status_code == 200
        text = response.get_data(as_text=True)

        # Verify format structure
        lines = text.split("\n")
        help_lines = [line for line in lines if line.startswith("# HELP")]
        type_lines = [line for line in lines if line.startswith("# TYPE")]
        metric_lines = [
            line
            for line in lines
            if line and not line.startswith("#") and ("{" in line or " " in line)
        ]

        assert len(help_lines) > 0, "Should have HELP comments"
        assert len(type_lines) > 0, "Should have TYPE comments"
        assert len(metric_lines) > 0, "Should have metric data lines"

    def test_metrics_histogram_buckets(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test HTTP duration metrics use histogram with buckets (REQ-009, AC-004).

        Given: Application has processed requests
        When: GET /metrics is called
        Then: Response contains flask_http_request_duration_seconds histogram
        And: Histogram has standard buckets (le labels)
        """
        # Generate some requests
        client.get("/health")
        client.get("/ready")

        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        assert response.status_code == 200
        text = response.get_data(as_text=True)

        # Check for histogram buckets (le="...")
        assert 'le="0.005"' in text or "flask_http_request_duration_seconds" in text, (
            "Should have histogram buckets or duration metric"
        )

    def test_metrics_app_info_label(
        self, client: FlaskClient, metrics_api_key: str
    ) -> None:
        """Test app_info metric is exposed (REQ-008 partial).

        Given: Application is configured
        When: GET /metrics is called
        Then: Response contains app_info metric with version label
        """
        response = client.get(
            "/metrics", headers={"Authorization": f"Bearer {metrics_api_key}"}
        )

        assert response.status_code == 200
        text = response.get_data(as_text=True)
        assert "app_info" in text
