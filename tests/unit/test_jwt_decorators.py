# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Tests for JWT authentication decorators.

Tests JWT token validation, claim extraction, and error handling
for the @require_jwt_auth decorator.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock, patch

import jwt
import pytest
from flask import Flask, g, jsonify

from app.services.guardian_service import Operation
from app.utils.jwt_decorators import (
    JWTError,
    access_required,
    get_current_company_id,
    get_current_user_email,
    get_current_user_id,
    require_jwt_auth,
)


@pytest.fixture
def app() -> Flask:
    """Fixture providing a Flask app with JWT configuration.

    Returns:
        Configured Flask app instance.
    """
    test_app = Flask(__name__)
    test_app.config.update(
        {
            "JWT_SECRET_KEY": "test-secret-key",
            "JWT_ALGORITHM": "HS256",
            "JWT_COOKIE_NAME": "access_token",
            "JWT_ACCESS_TOKEN_EXPIRES": timedelta(hours=1),
            "TESTING": True,
        }
    )

    @test_app.route("/protected")
    @require_jwt_auth
    def protected_route() -> tuple[dict[str, Any], int]:
        """Test route requiring JWT authentication."""
        return jsonify(
            {
                "user_id": g.user_id,
                "company_id": g.company_id,
                "email": g.email,
            }
        ), 200

    @test_app.route("/public")
    def public_route() -> tuple[dict[str, Any], int]:
        """Test route without authentication."""
        return jsonify({"message": "public"}), 200

    return test_app


@pytest.fixture
def client(app: Flask) -> Any:
    """Fixture providing a test client.

    Args:
        app: Flask app instance.

    Returns:
        Flask test client.
    """
    return app.test_client()


def generate_valid_token(
    app: Flask,
    user_id: str = "user-123",
    company_id: str = "company-456",
    email: str = "test@example.com",
    exp_delta: timedelta | None = None,
) -> str:
    """Generate a valid JWT token for testing.

    Args:
        app: Flask app with JWT configuration.
        user_id: User identifier.
        company_id: Company identifier.
        email: User email.
        exp_delta: Expiration time delta (default: 1 hour).

    Returns:
        Encoded JWT token string.
    """
    if exp_delta is None:
        exp_delta = timedelta(hours=1)

    payload = {
        "user_id": user_id,
        "company_id": company_id,
        "email": email,
        "exp": datetime.now(UTC) + exp_delta,
        "iat": datetime.now(UTC),
    }

    return jwt.encode(
        payload, app.config["JWT_SECRET_KEY"], algorithm=app.config["JWT_ALGORITHM"]
    )


class TestJWTError:
    """Tests for JWTError exception."""

    def test_jwt_error_has_message(self) -> None:
        """Test that JWTError stores error message.

        Given: An error message
        When: JWTError is raised
        Then: Error has correct message
        """
        error = JWTError("Test error")
        assert error.message == "Test error"
        assert str(error) == "Test error"

    def test_jwt_error_default_status_code(self) -> None:
        """Test that JWTError has default 401 status code.

        Given: JWTError without status code
        When: Error is created
        Then: Status code is 401
        """
        error = JWTError("Test error")
        assert error.status_code == 401

    def test_jwt_error_custom_status_code(self) -> None:
        """Test that JWTError accepts custom status code.

        Given: Custom status code
        When: JWTError is created
        Then: Status code is set correctly
        """
        error = JWTError("Test error", status_code=403)
        assert error.status_code == 403


class TestRequireJWTAuth:
    """Tests for @require_jwt_auth decorator."""

    def test_require_jwt_auth_allows_valid_token(self, app: Flask, client: Any) -> None:
        """Test that valid JWT token allows access.

        Given: Valid JWT token in cookie
        When: Protected route is accessed
        Then: Status is 200 and claims are in context
        """
        token = generate_valid_token(app)
        client.set_cookie("access_token", token)

        response = client.get("/protected")

        assert response.status_code == 200
        data = response.get_json()
        assert data["user_id"] == "user-123"
        assert data["company_id"] == "company-456"
        assert data["email"] == "test@example.com"

    def test_require_jwt_auth_rejects_missing_token(
        self, app: Flask, client: Any
    ) -> None:
        """Test that missing token returns 401.

        Given: No JWT token
        When: Protected route is accessed
        Then: Status is 401 with error message
        """
        response = client.get("/protected")

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "Unauthorized"
        assert "No token provided" in data["message"]

    def test_require_jwt_auth_rejects_expired_token(
        self, app: Flask, client: Any
    ) -> None:
        """Test that expired token returns 401.

        Given: Expired JWT token
        When: Protected route is accessed
        Then: Status is 401 with expiration error
        """
        # Generate token that expired 1 hour ago
        token = generate_valid_token(app, exp_delta=timedelta(hours=-1))
        client.set_cookie("access_token", token)

        response = client.get("/protected")

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "Unauthorized"
        assert "expired" in data["message"].lower()

    def test_require_jwt_auth_rejects_invalid_signature(
        self, app: Flask, client: Any
    ) -> None:
        """Test that token with invalid signature returns 401.

        Given: JWT token with wrong signature
        When: Protected route is accessed
        Then: Status is 401 with validation error
        """
        # Generate token with different secret
        payload = {
            "user_id": "user-123",
            "company_id": "company-456",
            "email": "test@example.com",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        client.set_cookie("access_token", token)

        response = client.get("/protected")

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "Unauthorized"

    def test_require_jwt_auth_rejects_malformed_token(
        self, app: Flask, client: Any
    ) -> None:
        """Test that malformed token returns 401.

        Given: Invalid JWT format
        When: Protected route is accessed
        Then: Status is 401 with decode error
        """
        client.set_cookie("access_token", "not.a.valid.jwt.token")

        response = client.get("/protected")

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "Unauthorized"

    def test_require_jwt_auth_rejects_missing_user_id(
        self, app: Flask, client: Any
    ) -> None:
        """Test that token without user_id returns 401.

        Given: JWT token missing user_id claim
        When: Protected route is accessed
        Then: Status is 401 with missing claims error
        """
        payload = {
            "company_id": "company-456",
            "email": "test@example.com",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = jwt.encode(
            payload, app.config["JWT_SECRET_KEY"], algorithm=app.config["JWT_ALGORITHM"]
        )
        client.set_cookie("access_token", token)

        response = client.get("/protected")

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "Unauthorized"
        assert "missing required claims" in data["message"].lower()

    def test_require_jwt_auth_rejects_missing_company_id(
        self, app: Flask, client: Any
    ) -> None:
        """Test that token without company_id returns 401.

        Given: JWT token missing company_id claim
        When: Protected route is accessed
        Then: Status is 401 with missing claims error
        """
        payload = {
            "user_id": "user-123",
            "email": "test@example.com",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = jwt.encode(
            payload, app.config["JWT_SECRET_KEY"], algorithm=app.config["JWT_ALGORITHM"]
        )
        client.set_cookie("access_token", token)

        response = client.get("/protected")

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "Unauthorized"
        assert "missing required claims" in data["message"].lower()

    def test_require_jwt_auth_allows_missing_email(
        self, app: Flask, client: Any
    ) -> None:
        """Test that token without email is still valid.

        Given: JWT token without email claim
        When: Protected route is accessed
        Then: Status is 200 and email is None
        """
        payload = {
            "user_id": "user-123",
            "company_id": "company-456",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = jwt.encode(
            payload, app.config["JWT_SECRET_KEY"], algorithm=app.config["JWT_ALGORITHM"]
        )
        client.set_cookie("access_token", token)

        response = client.get("/protected")

        assert response.status_code == 200
        data = response.get_json()
        assert data["user_id"] == "user-123"
        assert data["company_id"] == "company-456"
        assert data["email"] is None

    def test_require_jwt_auth_logs_success(self, app: Flask, client: Any) -> None:
        """Test that successful authentication is logged.

        Given: Valid JWT token
        When: Protected route is accessed
        Then: Success is logged with user context
        """
        token = generate_valid_token(app)
        client.set_cookie("access_token", token)

        with patch.object(app.logger, "debug") as mock_log:
            response = client.get("/protected")

            assert response.status_code == 200
            # Check that debug log was called
            assert mock_log.called

    def test_require_jwt_auth_logs_missing_token(self, app: Flask, client: Any) -> None:
        """Test that missing token is logged.

        Given: No JWT token
        When: Protected route is accessed
        Then: Warning is logged
        """
        with patch.object(app.logger, "warning") as mock_log:
            response = client.get("/protected")

            assert response.status_code == 401
            # Check that warning log was called
            assert mock_log.called

    def test_require_jwt_auth_logs_expired_token(self, app: Flask, client: Any) -> None:
        """Test that expired token is logged.

        Given: Expired JWT token
        When: Protected route is accessed
        Then: Warning is logged
        """
        token = generate_valid_token(app, exp_delta=timedelta(hours=-1))
        client.set_cookie("access_token", token)

        with patch.object(app.logger, "warning") as mock_log:
            response = client.get("/protected")

            assert response.status_code == 401
            # Check that warning log was called
            assert mock_log.called

    def test_public_route_works_without_token(self, app: Flask, client: Any) -> None:
        """Test that public route works without authentication.

        Given: No JWT token
        When: Public route is accessed
        Then: Status is 200
        """
        response = client.get("/public")

        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "public"


class TestContextHelpers:
    """Tests for context helper functions."""

    def test_get_current_user_id_returns_user_id(self, app: Flask) -> None:
        """Test that get_current_user_id returns user_id from context.

        Given: user_id in Flask g context
        When: get_current_user_id is called
        Then: Returns correct user_id
        """
        with app.test_request_context():
            g.user_id = "test-user-123"
            assert get_current_user_id() == "test-user-123"

    def test_get_current_user_id_returns_none_when_missing(self, app: Flask) -> None:
        """Test that get_current_user_id returns None when not set.

        Given: No user_id in context
        When: get_current_user_id is called
        Then: Returns None
        """
        with app.test_request_context():
            assert get_current_user_id() is None

    def test_get_current_company_id_returns_company_id(self, app: Flask) -> None:
        """Test that get_current_company_id returns company_id from context.

        Given: company_id in Flask g context
        When: get_current_company_id is called
        Then: Returns correct company_id
        """
        with app.test_request_context():
            g.company_id = "test-company-456"
            assert get_current_company_id() == "test-company-456"

    def test_get_current_company_id_returns_none_when_missing(self, app: Flask) -> None:
        """Test that get_current_company_id returns None when not set.

        Given: No company_id in context
        When: get_current_company_id is called
        Then: Returns None
        """
        with app.test_request_context():
            assert get_current_company_id() is None

    def test_get_current_user_email_returns_email(self, app: Flask) -> None:
        """Test that get_current_user_email returns email from context.

        Given: email in Flask g context
        When: get_current_user_email is called
        Then: Returns correct email
        """
        with app.test_request_context():
            g.email = "test@example.com"
            assert get_current_user_email() == "test@example.com"

    def test_get_current_user_email_returns_none_when_missing(self, app: Flask) -> None:
        """Test that get_current_user_email returns None when not set.

        Given: No email in context
        When: get_current_user_email is called
        Then: Returns None
        """
        with app.test_request_context():
            assert get_current_user_email() is None


class TestAccessRequired:
    """Tests for @access_required decorator."""

    @pytest.fixture
    def guardian_app(self) -> Flask:
        """Fixture providing Flask app with Guardian and JWT config.

        Returns:
            Configured Flask app instance.
        """
        test_app = Flask(__name__)
        test_app.config.update(
            {
                "JWT_SECRET_KEY": "test-secret-key",
                "JWT_ALGORITHM": "HS256",
                "JWT_COOKIE_NAME": "access_token",
                "GUARDIAN_SERVICE_URL": "http://guardian:5001",
                "GUARDIAN_SERVICE_TIMEOUT": 5,
                "GUARDIAN_SERVICE_API_KEY": "test-key",
                "SERVICE_NAME": "test-service",
                "TESTING": True,
            }
        )

        @test_app.route("/projects/<project_id>")
        @require_jwt_auth
        @access_required(Operation.READ, "projects")
        def get_project(project_id: str) -> tuple[dict[str, Any], int]:
            """Test route with access control."""
            return jsonify({"id": project_id}), 200

        @test_app.route("/projects", methods=["POST"])
        @require_jwt_auth
        @access_required(Operation.CREATE, "projects")
        def create_project() -> tuple[dict[str, Any], int]:
            """Test route for creating projects."""
            return jsonify({"created": True}), 201

        @test_app.route("/users/<user_id>", methods=["DELETE"])
        @require_jwt_auth
        @access_required(Operation.DELETE, "users")
        def delete_user(user_id: str) -> tuple[dict[str, Any], int]:
            """Test route for deleting users."""
            return jsonify({"deleted": user_id}), 200

        return test_app

    @patch("app.services.guardian_service.requests.post")
    def test_access_required_grants_access(
        self, mock_post: Any, guardian_app: Flask
    ) -> None:
        """Test that access_required allows access when Guardian grants it.

        Given: Guardian grants access
        When: Protected route is accessed
        Then: Status is 200 and function executes
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_granted": True, "reason": "granted"}
        mock_post.return_value = mock_response

        with guardian_app.test_client() as client:
            token = jwt.encode(
                {
                    "user_id": "user-123",
                    "company_id": "company-456",
                    "email": "test@example.com",
                    "exp": datetime.now(UTC) + timedelta(hours=1),
                },
                guardian_app.config["JWT_SECRET_KEY"],
                algorithm=guardian_app.config["JWT_ALGORITHM"],
            )
            client.set_cookie("access_token", token)

            response = client.get("/projects/proj-789")

        assert response.status_code == 200
        assert response.get_json()["id"] == "proj-789"

    @patch("app.services.guardian_service.requests.post")
    def test_access_required_denies_access(
        self, mock_post: Any, guardian_app: Flask
    ) -> None:
        """Test that access_required denies access when Guardian denies it.

        Given: Guardian denies access
        When: Protected route is accessed
        Then: Status is 403
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_granted": False,
            "reason": "no_permission",
        }
        mock_post.return_value = mock_response

        with guardian_app.test_client() as client:
            token = jwt.encode(
                {
                    "user_id": "user-123",
                    "company_id": "company-456",
                    "exp": datetime.now(UTC) + timedelta(hours=1),
                },
                guardian_app.config["JWT_SECRET_KEY"],
                algorithm=guardian_app.config["JWT_ALGORITHM"],
            )
            client.set_cookie("access_token", token)

            response = client.get("/projects/proj-789")

        assert response.status_code == 403
        data = response.get_json()
        assert data["error"] == "Forbidden"
        assert "no_permission" in data["message"]

    @patch("app.services.guardian_service.requests.post")
    def test_access_required_passes_context(
        self, mock_post: Any, guardian_app: Flask
    ) -> None:
        """Test that access_required passes route kwargs as context.

        Given: Route with parameters
        When: Protected route is accessed
        Then: Parameters are sent as context to Guardian
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_granted": True, "reason": "granted"}
        mock_post.return_value = mock_response

        with guardian_app.test_client() as client:
            token = jwt.encode(
                {
                    "user_id": "user-123",
                    "company_id": "company-456",
                    "exp": datetime.now(UTC) + timedelta(hours=1),
                },
                guardian_app.config["JWT_SECRET_KEY"],
                algorithm=guardian_app.config["JWT_ALGORITHM"],
            )
            client.set_cookie("access_token", token)

            client.get("/projects/proj-789")

        call_args = mock_post.call_args
        assert call_args[1]["json"]["context"] == {"project_id": "proj-789"}

    def test_access_required_without_jwt_auth(self, guardian_app: Flask) -> None:
        """Test that access_required requires JWT context.

        Given: No JWT authentication (missing user_id/company_id)
        When: Protected route is accessed
        Then: Status is 401
        """

        # Create route without @require_jwt_auth
        @guardian_app.route("/test-no-jwt")
        @access_required(Operation.READ, "test")
        def test_route() -> tuple[dict[str, Any], int]:
            return jsonify({"test": True}), 200

        with guardian_app.test_client() as client:
            response = client.get("/test-no-jwt")

        assert response.status_code == 401
        data = response.get_json()
        assert "User context missing" in data["message"]

    @patch("app.services.guardian_service.requests.post")
    def test_access_required_handles_guardian_error(
        self, mock_post: Any, guardian_app: Flask
    ) -> None:
        """Test that access_required handles Guardian service errors.

        Given: Guardian service returns error
        When: Protected route is accessed
        Then: Status is 503
        """
        from requests.exceptions import ConnectionError

        mock_post.side_effect = ConnectionError()

        with guardian_app.test_client() as client:
            token = jwt.encode(
                {
                    "user_id": "user-123",
                    "company_id": "company-456",
                    "exp": datetime.now(UTC) + timedelta(hours=1),
                },
                guardian_app.config["JWT_SECRET_KEY"],
                algorithm=guardian_app.config["JWT_ALGORITHM"],
            )
            client.set_cookie("access_token", token)

            response = client.get("/projects/proj-789")

        assert response.status_code == 503
        data = response.get_json()
        assert data["error"] == "Service Unavailable"

    @patch("app.services.guardian_service.requests.post")
    def test_access_required_logs_access_denied(
        self, mock_post: Any, guardian_app: Flask
    ) -> None:
        """Test that access_required logs when access is denied.

        Given: Guardian denies access
        When: Protected route is accessed
        Then: Warning is logged
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_granted": False,
            "reason": "no_permission",
        }
        mock_post.return_value = mock_response

        with guardian_app.test_client() as client:
            token = jwt.encode(
                {
                    "user_id": "user-123",
                    "company_id": "company-456",
                    "exp": datetime.now(UTC) + timedelta(hours=1),
                },
                guardian_app.config["JWT_SECRET_KEY"],
                algorithm=guardian_app.config["JWT_ALGORITHM"],
            )
            client.set_cookie("access_token", token)

            with patch.object(guardian_app.logger, "warning") as mock_log:
                client.get("/projects/proj-789")

            assert mock_log.called

    @patch("app.services.guardian_service.requests.post")
    def test_access_required_logs_guardian_error(
        self, mock_post: Any, guardian_app: Flask
    ) -> None:
        """Test that access_required logs Guardian errors.

        Given: Guardian service fails
        When: Protected route is accessed
        Then: Error is logged
        """
        from requests.exceptions import Timeout

        mock_post.side_effect = Timeout()

        with guardian_app.test_client() as client:
            token = jwt.encode(
                {
                    "user_id": "user-123",
                    "company_id": "company-456",
                    "exp": datetime.now(UTC) + timedelta(hours=1),
                },
                guardian_app.config["JWT_SECRET_KEY"],
                algorithm=guardian_app.config["JWT_ALGORITHM"],
            )
            client.set_cookie("access_token", token)

            with patch.object(guardian_app.logger, "error") as mock_log:
                client.get("/projects/proj-789")

            assert mock_log.called

    @patch("app.services.guardian_service.requests.post")
    def test_access_required_with_different_operations(
        self, mock_post: Any, guardian_app: Flask
    ) -> None:
        """Test that access_required works with different operations.

        Given: Routes with different operations
        When: Protected routes are accessed
        Then: Correct operation is sent to Guardian
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_granted": True, "reason": "granted"}
        mock_post.return_value = mock_response

        with guardian_app.test_client() as client:
            token = jwt.encode(
                {
                    "user_id": "user-123",
                    "company_id": "company-456",
                    "exp": datetime.now(UTC) + timedelta(hours=1),
                },
                guardian_app.config["JWT_SECRET_KEY"],
                algorithm=guardian_app.config["JWT_ALGORITHM"],
            )
            client.set_cookie("access_token", token)

            # Test CREATE operation
            response = client.post("/projects")
            assert response.status_code == 201
            # First call should be CREATE
            first_call = mock_post.call_args_list[0]
            assert first_call[1]["json"]["operation"] == "CREATE"

            # Test DELETE operation
            response = client.delete("/users/user-123")
            assert response.status_code == 200
            # Second call should be DELETE
            second_call = mock_post.call_args_list[1]
            assert second_call[1]["json"]["operation"] == "DELETE"
