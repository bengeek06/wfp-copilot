# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Unit tests for health endpoints.

Tests health check logic with mocked dependencies to verify correct
behavior without requiring actual database or external service connections.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.resources.health import (
    HealthResource,
    ReadyResource,
    VersionResource,
    _check_database,
    _get_version_info,
)


class TestCheckDatabase:
    """Tests for _check_database helper function."""

    @patch("app.resources.health.db.session")
    @patch("app.resources.health.time.time")
    def test_database_check_success(self, mock_time, mock_session):
        """Test successful database connectivity check.

        Given: Database is operational
        When: _check_database is called
        Then: Returns status 'ok' with response time
        """
        # Mock time progression
        mock_time.side_effect = [0.0, 0.015]  # 15ms elapsed

        # Mock successful query execution
        mock_session.execute.return_value = None

        result = _check_database()

        assert result["status"] == "ok"
        assert result["response_time_ms"] == 15
        assert "error" not in result
        mock_session.execute.assert_called_once()

    @patch("app.resources.health.db.session")
    @patch("app.resources.health.time.time")
    def test_database_check_failure(self, mock_time, mock_session, app):
        """Test database check when connection fails.

        Given: Database is unavailable
        When: _check_database is called
        Then: Returns status 'error' with error message
        """
        # Mock time progression - add extra values for logging's time.time() calls
        mock_time.side_effect = [0.0, 3.0, 3.0, 3.0]  # Extra values for logging

        # Mock database connection error
        mock_session.execute.side_effect = Exception("Connection refused")

        with app.app_context():
            result = _check_database()

        assert result["status"] == "error"
        assert result["response_time_ms"] == 3000
        assert result["error"] == "Connection refused"


class TestGetVersionInfo:
    """Tests for _get_version_info helper function."""

    @patch("app.resources.health.Path")
    def test_get_version_info_success(self, mock_path):
        """Test reading version information from VERSION file.

        Given: VERSION file exists with valid content
        When: _get_version_info is called
        Then: Returns version information dictionary
        """
        # Mock VERSION file
        mock_version_file = MagicMock()
        mock_version_file.exists.return_value = True
        mock_version_file.read_text.return_value = "1.2.3\n"
        mock_path.return_value.parent.parent.parent.__truediv__.return_value = (
            mock_version_file
        )

        result = _get_version_info()

        assert result["version"] == "1.2.3"
        assert "commit" in result
        assert "build_date" in result
        assert "environment" in result

    @patch("app.resources.health.Path")
    def test_get_version_info_file_not_found(self, mock_path):
        """Test version reading when VERSION file is missing.

        Given: VERSION file does not exist
        When: _get_version_info is called
        Then: Raises FileNotFoundError
        """
        # Mock missing VERSION file
        mock_version_file = MagicMock()
        mock_version_file.exists.return_value = False
        mock_path.return_value.parent.parent.parent.__truediv__.return_value = (
            mock_version_file
        )

        with pytest.raises(FileNotFoundError, match="VERSION file not found"):
            _get_version_info()

    @patch("app.resources.health.Path")
    def test_get_version_info_empty_file(self, mock_path):
        """Test version reading when VERSION file is empty.

        Given: VERSION file exists but is empty
        When: _get_version_info is called
        Then: Raises ValueError
        """
        # Mock empty VERSION file
        mock_version_file = MagicMock()
        mock_version_file.exists.return_value = True
        mock_version_file.read_text.return_value = ""
        mock_path.return_value.parent.parent.parent.__truediv__.return_value = (
            mock_version_file
        )

        with pytest.raises(ValueError, match="VERSION file is empty"):
            _get_version_info()


class TestHealthResource:
    """Tests for HealthResource endpoint."""

    @patch("app.resources.health._check_database")
    def test_health_check_ok(self, mock_check_db):
        """Test health endpoint when all systems operational.

        Given: Database is up and responding
        When: GET /health is called
        Then: Returns 200 with status 'ok'
        """
        mock_check_db.return_value = {"status": "ok", "response_time_ms": 15}

        resource = HealthResource()
        response, status_code = resource.get()

        assert status_code == 200
        assert response["status"] == "ok"
        assert "timestamp" in response
        assert response["checks"]["database"]["status"] == "ok"

    @patch("app.resources.health._check_database")
    def test_health_check_degraded(self, mock_check_db):
        """Test health endpoint when database is down.

        Given: Database is unavailable
        When: GET /health is called
        Then: Returns 200 with status 'degraded'
        """
        mock_check_db.return_value = {
            "status": "error",
            "response_time_ms": 3000,
            "error": "Connection timeout",
        }

        resource = HealthResource()
        response, status_code = resource.get()

        assert status_code == 200  # Still returns 200 for liveness
        assert response["status"] == "degraded"
        assert "timestamp" in response
        assert response["checks"]["database"]["status"] == "error"
        assert response["checks"]["database"]["error"] == "Connection timeout"

    @patch("app.resources.health._check_database")
    def test_health_check_error(self, mock_check_db, app):
        """Test health endpoint when application itself fails.

        Given: Application encounters unexpected error
        When: GET /health is called
        Then: Returns 500 with error details
        """
        mock_check_db.side_effect = RuntimeError("Application broken")

        resource = HealthResource()
        with app.app_context():
            response, status_code = resource.get()

        assert status_code == 500
        assert response["status"] == "error"
        assert "error" in response


class TestReadyResource:
    """Tests for ReadyResource endpoint."""

    @patch("app.resources.health._check_database")
    def test_ready_check_ok(self, mock_check_db):
        """Test readiness endpoint when all dependencies operational.

        Given: All critical dependencies are up
        When: GET /ready is called
        Then: Returns 200 with status 'ready'
        """
        mock_check_db.return_value = {"status": "ok", "response_time_ms": 12}

        resource = ReadyResource()
        response, status_code = resource.get()

        assert status_code == 200
        assert response["status"] == "ready"
        assert "timestamp" in response
        assert response["checks"]["database"]["status"] == "ok"

    @patch("app.resources.health._check_database")
    def test_ready_check_not_ready(self, mock_check_db):
        """Test readiness endpoint when database is down.

        Given: Database is unavailable
        When: GET /ready is called
        Then: Returns 503 with status 'not_ready'
        """
        mock_check_db.return_value = {
            "status": "error",
            "response_time_ms": 3000,
            "error": "Connection refused",
        }

        resource = ReadyResource()
        response, status_code = resource.get()

        assert status_code == 503
        assert response["status"] == "not_ready"
        assert "timestamp" in response
        assert response["checks"]["database"]["status"] == "error"


class TestVersionResource:
    """Tests for VersionResource endpoint."""

    @patch("app.resources.health._get_version_info")
    def test_version_check_success(self, mock_get_version):
        """Test version endpoint with valid VERSION file.

        Given: VERSION file exists with valid content
        When: GET /version is called
        Then: Returns 200 with version information
        """
        mock_get_version.return_value = {
            "version": "1.2.3",
            "commit": "abc123",
            "build_date": "2026-01-07T08:00:00Z",
            "environment": "production",
        }

        resource = VersionResource()
        response, status_code = resource.get()

        assert status_code == 200
        assert response["version"] == "1.2.3"
        assert response["commit"] == "abc123"
        assert response["build_date"] == "2026-01-07T08:00:00Z"
        assert response["environment"] == "production"

    @patch("app.resources.health._get_version_info")
    def test_version_check_file_not_found(self, mock_get_version, app):
        """Test version endpoint when VERSION file is missing.

        Given: VERSION file does not exist
        When: GET /version is called
        Then: Returns 500 with error message
        """
        mock_get_version.side_effect = FileNotFoundError(
            "VERSION file not found at repository root"
        )

        resource = VersionResource()
        with app.app_context():
            response, status_code = resource.get()

        assert status_code == 500
        assert "error" in response
        assert "timestamp" in response
