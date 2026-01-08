# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Unit tests for metrics authentication utilities.

This module tests the API key authentication decorator for the metrics endpoint
without actually calling the Flask application or metrics endpoint.
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from app.utils.metrics_auth import require_metrics_api_key


@pytest.fixture
def app() -> Generator[Flask, None, None]:
    """Create Flask test app with METRICS_API_KEY configured.

    Yields:
        Configured Flask test application.
    """
    test_app = Flask(__name__)
    test_app.config["TESTING"] = True
    test_app.config["METRICS_API_KEY"] = "test-api-key-12345678901234567890"
    yield test_app


@pytest.fixture
def mock_request() -> MagicMock:
    """Create mock request object.

    Returns:
        Mock request with remote_addr and path attributes.
    """
    mock_req = MagicMock()
    mock_req.remote_addr = "127.0.0.1"
    mock_req.path = "/metrics"
    return mock_req


class TestRequireMetricsApiKey:
    """Tests for require_metrics_api_key decorator."""

    def test_decorator_with_valid_api_key(
        self, app: Flask, mock_request: MagicMock
    ) -> None:
        """Test decorator allows access with valid API key.

        Given: METRICS_API_KEY is configured
        And: Authorization header has valid Bearer token
        When: Decorated function is called
        Then: Function executes successfully
        """
        with app.app_context():
            mock_request.headers.get.return_value = (
                "Bearer test-api-key-12345678901234567890"
            )

            @require_metrics_api_key
            def protected_endpoint() -> str:
                return "metrics data"

            with patch("app.utils.metrics_auth.request", mock_request):
                result = protected_endpoint()

                assert result == "metrics data"

    def test_decorator_with_missing_api_key_config(
        self, mock_request: MagicMock
    ) -> None:
        """Test decorator returns 500 when API key not configured.

        Given: METRICS_API_KEY is not set in config
        When: Decorated function is called
        Then: Returns 500 with error message
        """
        app = Flask(__name__)
        app.config["TESTING"] = True
        # Intentionally not setting METRICS_API_KEY

        with app.app_context():
            mock_request.headers.get.return_value = "Bearer some-key"

            @require_metrics_api_key
            def protected_endpoint() -> str:
                return "metrics data"

            with patch("app.utils.metrics_auth.request", mock_request):
                response, status = protected_endpoint()

                assert status == 500
                assert response["message"] == "Metrics API key not configured"
                assert "timestamp" in response

    def test_decorator_with_missing_authorization_header(
        self, app: Flask, mock_request: MagicMock
    ) -> None:
        """Test decorator returns 401 when Authorization header missing.

        Given: METRICS_API_KEY is configured
        And: No Authorization header provided
        When: Decorated function is called
        Then: Returns 401 with error message
        """
        with app.app_context():
            mock_request.headers.get.return_value = ""

            @require_metrics_api_key
            def protected_endpoint() -> str:
                return "metrics data"

            with patch("app.utils.metrics_auth.request", mock_request):
                response, status = protected_endpoint()

                assert status == 401
                assert response["message"] == "Missing Authorization header"
                assert "timestamp" in response

    def test_decorator_with_invalid_authorization_format(
        self, app: Flask, mock_request: MagicMock
    ) -> None:
        """Test decorator returns 401 when Authorization format invalid.

        Given: METRICS_API_KEY is configured
        And: Authorization header does not start with 'Bearer '
        When: Decorated function is called
        Then: Returns 401 with format error message
        """
        with app.app_context():
            mock_request.headers.get.return_value = "InvalidFormat api-key"

            @require_metrics_api_key
            def protected_endpoint() -> str:
                return "metrics data"

            with patch("app.utils.metrics_auth.request", mock_request):
                response, status = protected_endpoint()

                assert status == 401
                assert "Invalid Authorization format" in response["message"]
                assert "timestamp" in response

    def test_decorator_with_wrong_api_key(
        self, app: Flask, mock_request: MagicMock
    ) -> None:
        """Test decorator returns 401 when API key is incorrect.

        Given: METRICS_API_KEY is "test-api-key-12345678901234567890"
        And: Authorization header has different key
        When: Decorated function is called
        Then: Returns 401 with invalid key message
        """
        with app.app_context():
            mock_request.headers.get.return_value = "Bearer wrong-api-key"

            @require_metrics_api_key
            def protected_endpoint() -> str:
                return "metrics data"

            with patch("app.utils.metrics_auth.request", mock_request):
                response, status = protected_endpoint()

                assert status == 401
                assert response["message"] == "Invalid API key"
                assert "timestamp" in response

    def test_decorator_logs_missing_header_warning(
        self, app: Flask, mock_request: MagicMock
    ) -> None:
        """Test decorator logs warning when header missing.

        Given: No Authorization header
        When: Decorated function is called
        Then: Warning is logged with IP and path
        """
        with app.app_context():
            mock_request.headers.get.return_value = ""

            @require_metrics_api_key
            def protected_endpoint() -> str:
                return "metrics data"

            with (
                patch("app.utils.metrics_auth.request", mock_request),
                patch("app.utils.metrics_auth.logger") as mock_logger,
            ):
                protected_endpoint()

                mock_logger.warning.assert_called_once()
                call_args = mock_logger.warning.call_args
                assert "without Authorization header" in call_args[0][0]

    def test_decorator_logs_invalid_key_warning(
        self, app: Flask, mock_request: MagicMock
    ) -> None:
        """Test decorator logs warning when API key invalid.

        Given: Wrong API key provided
        When: Decorated function is called
        Then: Warning is logged with IP and path
        """
        with app.app_context():
            mock_request.headers.get.return_value = "Bearer wrong-key"

            @require_metrics_api_key
            def protected_endpoint() -> str:
                return "metrics data"

            with (
                patch("app.utils.metrics_auth.request", mock_request),
                patch("app.utils.metrics_auth.logger") as mock_logger,
            ):
                protected_endpoint()

                mock_logger.warning.assert_called_once()
                call_args = mock_logger.warning.call_args
                assert "Invalid metrics API key" in call_args[0][0]

    def test_timestamp_format(self, app: Flask, mock_request: MagicMock) -> None:
        """Test error responses include valid ISO 8601 timestamp.

        Given: Authentication fails
        When: Error response is returned
        Then: Timestamp is valid ISO 8601 format in UTC
        """
        with app.app_context():
            mock_request.headers.get.return_value = ""

            @require_metrics_api_key
            def protected_endpoint() -> str:
                return "metrics data"

            with patch("app.utils.metrics_auth.request", mock_request):
                response, _ = protected_endpoint()

                # Verify timestamp can be parsed
                timestamp = response["timestamp"]
                parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                assert parsed.tzinfo is not None

    def test_decorator_preserves_function_metadata(self) -> None:
        """Test decorator preserves wrapped function metadata.

        Given: Function with docstring and name
        When: Decorator is applied
        Then: Function metadata is preserved via @wraps
        """

        @require_metrics_api_key
        def my_endpoint() -> str:
            """My endpoint docstring."""
            return "data"

        assert my_endpoint.__name__ == "my_endpoint"
        assert my_endpoint.__doc__ == "My endpoint docstring."
