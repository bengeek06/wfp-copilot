# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Unit tests for Prometheus metrics authentication module.

Tests the require_metrics_api_key function directly with various
authentication scenarios: valid keys, missing keys, invalid keys, invalid format.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.utils.metrics_auth import require_metrics_api_key

if TYPE_CHECKING:
    from flask import Flask


@pytest.fixture
def metrics_api_key() -> str:
    """Metrics API key for testing.

    Returns:
        Test API key matching the one in conftest.py.
    """
    return "test-metrics-api-key-integration-12345678"


class TestMetricsAuth:
    """Unit tests for metrics endpoint authentication."""

    def test_require_metrics_api_key_valid(
        self, app: Flask, metrics_api_key: str
    ) -> None:
        """Test authentication succeeds with valid API key.

        Given: Valid API key in Authorization header
        When: require_metrics_api_key is called
        Then: Returns None (no error)
        """
        with app.test_request_context(
            headers={"Authorization": f"Bearer {metrics_api_key}"}
        ):
            result = require_metrics_api_key()
            assert result is None

    def test_require_metrics_api_key_missing(self, app: Flask) -> None:
        """Test authentication fails without Authorization header.

        Given: No Authorization header
        When: require_metrics_api_key is called
        Then: Returns tuple with JSON error and 401 status
        """
        with app.test_request_context():
            result = require_metrics_api_key()
            assert result is not None
            response, status_code = result
            assert status_code == 401
            data = response.get_json()
            assert "message" in data
            assert "Missing Authorization header" in data["message"]
            assert "timestamp" in data

    def test_require_metrics_api_key_invalid(self, app: Flask) -> None:
        """Test authentication fails with invalid API key.

        Given: Invalid API key in Authorization header
        When: require_metrics_api_key is called
        Then: Returns tuple with JSON error and 401 status
        """
        with app.test_request_context(
            headers={"Authorization": "Bearer wrong-key-12345678"}
        ):
            result = require_metrics_api_key()
            assert result is not None
            response, status_code = result
            assert status_code == 401
            data = response.get_json()
            assert "message" in data
            assert "Invalid API key" in data["message"]

    def test_require_metrics_api_key_invalid_format_no_bearer(
        self, app: Flask, metrics_api_key: str
    ) -> None:
        """Test authentication fails with missing 'Bearer' prefix.

        Given: Authorization header without 'Bearer' prefix
        When: require_metrics_api_key is called
        Then: Returns tuple with format error and 401 status
        """
        with app.test_request_context(headers={"Authorization": metrics_api_key}):
            result = require_metrics_api_key()
            assert result is not None
            response, status_code = result
            assert status_code == 401
            data = response.get_json()
            assert "message" in data
            assert "Invalid Authorization format" in data["message"]
            assert "Expected: Bearer <token>" in data["message"]

    def test_require_metrics_api_key_invalid_format_empty_token(
        self, app: Flask
    ) -> None:
        """Test authentication fails with empty token.

        Given: Authorization header with 'Bearer' but no token
        When: require_metrics_api_key is called
        Then: Returns tuple with format error and 401 status
        """
        with app.test_request_context(headers={"Authorization": "Bearer "}):
            result = require_metrics_api_key()
            assert result is not None
            response, status_code = result
            assert status_code == 401
            data = response.get_json()
            assert "message" in data
            assert "Invalid Authorization format" in data["message"]

    def test_require_metrics_api_key_invalid_format_only_bearer(
        self, app: Flask
    ) -> None:
        """Test authentication fails with only 'Bearer' keyword.

        Given: Authorization header with only 'Bearer' (no space/token)
        When: require_metrics_api_key is called
        Then: Returns tuple with format error and 401 status
        """
        with app.test_request_context(headers={"Authorization": "Bearer"}):
            result = require_metrics_api_key()
            assert result is not None
            response, status_code = result
            assert status_code == 401
            data = response.get_json()
            assert "message" in data
            assert "Invalid Authorization format" in data["message"]
