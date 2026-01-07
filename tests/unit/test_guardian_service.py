# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Tests for Guardian RBAC service client.

Tests Guardian service communication, permission checks,
and error handling for RBAC authorization.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests
from flask import Flask

from app.services.guardian_service import (
    GuardianError,
    GuardianService,
    Operation,
)


@pytest.fixture
def app() -> Flask:
    """Fixture providing a Flask app with Guardian configuration.

    Returns:
        Configured Flask app instance.
    """
    test_app = Flask(__name__)
    test_app.config.update(
        {
            "GUARDIAN_SERVICE_URL": "http://guardian:5001",
            "GUARDIAN_SERVICE_TIMEOUT": 5,
            "GUARDIAN_SERVICE_API_KEY": "test-api-key",
            "SERVICE_NAME": "test-service",
            "TESTING": True,
        }
    )
    return test_app


class TestOperation:
    """Tests for Operation enum."""

    def test_operation_enum_has_all_values(self) -> None:
        """Test that Operation enum has all required values.

        Given: Operation enum
        When: Checking values
        Then: All CRUD operations are present
        """
        assert Operation.LIST.value == "LIST"
        assert Operation.CREATE.value == "CREATE"
        assert Operation.READ.value == "READ"
        assert Operation.UPDATE.value == "UPDATE"
        assert Operation.DELETE.value == "DELETE"

    def test_operation_is_string_enum(self) -> None:
        """Test that Operation values are strings.

        Given: Operation enum
        When: Checking value types
        Then: All values are strings
        """
        assert isinstance(Operation.READ.value, str)
        assert isinstance(Operation.CREATE.value, str)


class TestGuardianError:
    """Tests for GuardianError exception."""

    def test_guardian_error_has_message(self) -> None:
        """Test that GuardianError stores error message.

        Given: An error message
        When: GuardianError is raised
        Then: Error has correct message
        """
        error = GuardianError("Guardian unavailable")
        assert error.message == "Guardian unavailable"
        assert str(error) == "Guardian unavailable"

    def test_guardian_error_default_status_code(self) -> None:
        """Test that GuardianError has default 503 status code.

        Given: GuardianError without status code
        When: Error is created
        Then: Status code is 503
        """
        error = GuardianError("Guardian unavailable")
        assert error.status_code == 503

    def test_guardian_error_custom_status_code(self) -> None:
        """Test that GuardianError accepts custom status code.

        Given: Custom status code
        When: GuardianError is created
        Then: Status code is set correctly
        """
        error = GuardianError("Bad request", status_code=400)
        assert error.status_code == 400


class TestGuardianServiceCheckAccess:
    """Tests for GuardianService.check_access method."""

    @patch("app.services.guardian_service.requests.post")
    def test_check_access_grants_permission(
        self, mock_post: MagicMock, app: Flask
    ) -> None:
        """Test that check_access returns True when permission granted.

        Given: Guardian returns access_granted=True
        When: check_access is called
        Then: Returns (True, reason)
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_granted": True,
            "reason": "granted",
        }
        mock_post.return_value = mock_response

        with app.app_context():
            access, reason = GuardianService.check_access(
                user_id="user-123",
                company_id="company-456",
                resource_name="projects",
                operation=Operation.READ,
            )

        assert access is True
        assert reason == "granted"
        mock_post.assert_called_once()

    @patch("app.services.guardian_service.requests.post")
    def test_check_access_denies_permission(
        self, mock_post: MagicMock, app: Flask
    ) -> None:
        """Test that check_access returns False when permission denied.

        Given: Guardian returns access_granted=False
        When: check_access is called
        Then: Returns (False, reason)
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_granted": False,
            "reason": "no_permission",
        }
        mock_post.return_value = mock_response

        with app.app_context():
            access, reason = GuardianService.check_access(
                user_id="user-123",
                company_id="company-456",
                resource_name="projects",
                operation=Operation.DELETE,
            )

        assert access is False
        assert reason == "no_permission"

    @patch("app.services.guardian_service.requests.post")
    def test_check_access_sends_correct_payload(
        self, mock_post: MagicMock, app: Flask
    ) -> None:
        """Test that check_access sends correct request payload.

        Given: Access check parameters
        When: check_access is called
        Then: Correct payload is sent to Guardian
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_granted": True,
            "reason": "granted",
        }
        mock_post.return_value = mock_response

        with app.app_context():
            GuardianService.check_access(
                user_id="user-123",
                company_id="company-456",
                resource_name="projects",
                operation=Operation.CREATE,
                context={"project_id": "proj-789"},
            )

        call_args = mock_post.call_args
        assert call_args[1]["json"]["service"] == "test-service"
        assert call_args[1]["json"]["user_id"] == "user-123"
        assert call_args[1]["json"]["company_id"] == "company-456"
        assert call_args[1]["json"]["resource_name"] == "projects"
        assert call_args[1]["json"]["operation"] == "CREATE"
        assert call_args[1]["json"]["context"] == {"project_id": "proj-789"}

    @patch("app.services.guardian_service.requests.post")
    def test_check_access_includes_api_key_header(
        self, mock_post: MagicMock, app: Flask
    ) -> None:
        """Test that check_access includes API key in headers.

        Given: Guardian API key configured
        When: check_access is called
        Then: X-API-Key header is included
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_granted": True,
            "reason": "granted",
        }
        mock_post.return_value = mock_response

        with app.app_context():
            GuardianService.check_access(
                user_id="user-123",
                company_id="company-456",
                resource_name="projects",
                operation=Operation.READ,
            )

        call_args = mock_post.call_args
        assert call_args[1]["headers"]["X-API-Key"] == "test-api-key"
        assert call_args[1]["headers"]["Content-Type"] == "application/json"

    @patch("app.services.guardian_service.requests.post")
    def test_check_access_without_context(
        self, mock_post: MagicMock, app: Flask
    ) -> None:
        """Test that check_access works without context parameter.

        Given: No context provided
        When: check_access is called
        Then: Context is not included in payload
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_granted": True,
            "reason": "granted",
        }
        mock_post.return_value = mock_response

        with app.app_context():
            GuardianService.check_access(
                user_id="user-123",
                company_id="company-456",
                resource_name="projects",
                operation=Operation.LIST,
            )

        call_args = mock_post.call_args
        assert "context" not in call_args[1]["json"]

    @patch("app.services.guardian_service.requests.post")
    def test_check_access_handles_guardian_error_status(
        self, mock_post: MagicMock, app: Flask
    ) -> None:
        """Test that check_access raises error on non-200 status.

        Given: Guardian returns error status code
        When: check_access is called
        Then: GuardianError is raised
        """
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with app.app_context(), pytest.raises(GuardianError) as exc_info:
            GuardianService.check_access(
                user_id="user-123",
                company_id="company-456",
                resource_name="projects",
                operation=Operation.READ,
            )

        assert exc_info.value.status_code == 503
        assert "Guardian service error" in exc_info.value.message

    @patch("app.services.guardian_service.requests.post")
    def test_check_access_handles_timeout(
        self, mock_post: MagicMock, app: Flask
    ) -> None:
        """Test that check_access handles timeout errors.

        Given: Guardian request times out
        When: check_access is called
        Then: GuardianError is raised with timeout message
        """
        mock_post.side_effect = requests.exceptions.Timeout()

        with app.app_context(), pytest.raises(GuardianError) as exc_info:
            GuardianService.check_access(
                user_id="user-123",
                company_id="company-456",
                resource_name="projects",
                operation=Operation.READ,
            )

        assert "timeout" in exc_info.value.message.lower()
        assert exc_info.value.status_code == 503

    @patch("app.services.guardian_service.requests.post")
    def test_check_access_handles_connection_error(
        self, mock_post: MagicMock, app: Flask
    ) -> None:
        """Test that check_access handles connection errors.

        Given: Cannot connect to Guardian
        When: check_access is called
        Then: GuardianError is raised with unavailable message
        """
        mock_post.side_effect = requests.exceptions.ConnectionError()

        with app.app_context(), pytest.raises(GuardianError) as exc_info:
            GuardianService.check_access(
                user_id="user-123",
                company_id="company-456",
                resource_name="projects",
                operation=Operation.READ,
            )

        assert "unavailable" in exc_info.value.message.lower()
        assert exc_info.value.status_code == 503

    @patch("app.services.guardian_service.requests.post")
    def test_check_access_handles_request_exception(
        self, mock_post: MagicMock, app: Flask
    ) -> None:
        """Test that check_access handles generic request errors.

        Given: Request raises generic exception
        When: check_access is called
        Then: GuardianError is raised
        """
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        with app.app_context(), pytest.raises(GuardianError) as exc_info:
            GuardianService.check_access(
                user_id="user-123",
                company_id="company-456",
                resource_name="projects",
                operation=Operation.READ,
            )

        assert "Network error" in exc_info.value.message
        assert exc_info.value.status_code == 503

    @patch("app.services.guardian_service.requests.post")
    def test_check_access_logs_debug_on_request(
        self, mock_post: MagicMock, app: Flask
    ) -> None:
        """Test that check_access logs debug info on request.

        Given: Valid access check request
        When: check_access is called
        Then: Debug log is written
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_granted": True,
            "reason": "granted",
        }
        mock_post.return_value = mock_response

        with app.app_context():
            with patch.object(app.logger, "debug") as mock_log:
                GuardianService.check_access(
                    user_id="user-123",
                    company_id="company-456",
                    resource_name="projects",
                    operation=Operation.READ,
                )

            assert mock_log.called

    @patch("app.services.guardian_service.requests.post")
    def test_check_access_logs_info_on_response(
        self, mock_post: MagicMock, app: Flask
    ) -> None:
        """Test that check_access logs info on successful response.

        Given: Guardian returns valid response
        When: check_access is called
        Then: Info log is written with result
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_granted": True,
            "reason": "granted",
        }
        mock_post.return_value = mock_response

        with app.app_context():
            with patch.object(app.logger, "info") as mock_log:
                GuardianService.check_access(
                    user_id="user-123",
                    company_id="company-456",
                    resource_name="projects",
                    operation=Operation.READ,
                )

            assert mock_log.called
