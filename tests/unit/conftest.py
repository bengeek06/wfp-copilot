# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro
"""Pytest fixtures for unit tests.

This module provides common fixtures for unit testing following factory
patterns, including application instances, test clients, mock services,
and authentication helpers.
"""

import os
import uuid
from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import Mock, patch

import jwt
import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app

# === Constants ===

# Mock patch targets
GUARDIAN_CHECK_ACCESS_PATH = "app.services.guardian.GuardianService.check_access"

# === Application & Database ===


@pytest.fixture(scope="session")
def app() -> Generator[Flask, None, None]:
    """Create Flask application instance for testing session.

    Application is created once per test session for efficiency.
    Uses TestingConfig with in-memory SQLite database.

    Yields:
        Flask application configured with TestingConfig.
    """
    os.environ["TESTING"] = "true"
    app = create_app("app.config.TestingConfig")

    with app.app_context():
        yield app


@pytest.fixture(scope="function")
def client(app: Flask) -> FlaskClient:
    """Create Flask test client for making HTTP requests.

    Recreated for each test function to ensure isolation.

    Args:
        app: Flask application fixture.

    Returns:
        Flask test client for making HTTP requests.
    """
    return app.test_client()


@pytest.fixture
def runner(app: Flask):
    """Create Flask CLI test runner for testing commands.

    Args:
        app: Flask application fixture.

    Returns:
        Flask CLI test runner for testing CLI commands.
    """
    return app.test_cli_runner()


# === Helpers ===


@pytest.fixture
def api_url() -> Callable[[str, str], str]:
    """Generate versioned API URLs.

    Returns:
        Function that generates versioned API URLs.

    Examples:
        >>> url = api_url('projects')
        '/v0/projects'
        >>> url = api_url('tasks', version='v1')
        '/v1/tasks'
    """

    def _url(endpoint: str, version: str = "v0") -> str:
        return f"/{version}/{endpoint.lstrip('/')}"

    return _url


@pytest.fixture
def assert_response() -> Callable:
    """Helper to assert common response patterns.

    Returns:
        Function that asserts response status and structure.

    Examples:
        >>> data = assert_response(response, status_code=200)
        >>> assert 'items' in data
    """

    def _assert(
        response, status_code: int = 200, has_data: bool = True, has_error: bool = False
    ) -> dict[str, Any]:
        assert response.status_code == status_code
        data = response.get_json()

        if has_data:
            assert data is not None

        if has_error:
            assert "error" in data or "errors" in data
        else:
            assert "error" not in data

        return data

    return _assert


# === Authentication Fixtures ===


@pytest.fixture
def jwt_secret(app: Flask) -> str:
    """JWT secret key from application config.

    Args:
        app: Flask application fixture.

    Returns:
        JWT secret key for token generation.
    """
    return app.config["JWT_SECRET_KEY"]


@pytest.fixture
def generate_uuid() -> Callable[[], str]:
    """Factory to generate UUIDs for test data.

    Returns:
        Function that generates UUID strings.
    """

    def _generate() -> str:
        return str(uuid.uuid4())

    return _generate


@pytest.fixture
def company_id(generate_uuid: Callable) -> str:
    """Generate test company ID.

    Args:
        generate_uuid: UUID generator fixture.

    Returns:
        UUID string for company.
    """
    return generate_uuid()


@pytest.fixture
def user_claims(company_id: str, generate_uuid: Callable) -> dict[str, Any]:
    """Standard user JWT claims for testing.

    Args:
        company_id: Company ID fixture.
        generate_uuid: UUID generator fixture.

    Returns:
        JWT claims dictionary with user information.
    """
    return {
        "user_id": generate_uuid(),
        "company_id": company_id,
        "email": "test@example.com",
        "roles": ["user"],
        "exp": datetime.now(UTC) + timedelta(hours=1),
        "iat": datetime.now(UTC),
    }


@pytest.fixture
def admin_claims(company_id: str, generate_uuid: Callable) -> dict[str, Any]:
    """Admin user JWT claims for testing.

    Args:
        company_id: Company ID fixture.
        generate_uuid: UUID generator fixture.

    Returns:
        JWT claims dictionary with admin roles.
    """
    return {
        "user_id": generate_uuid(),
        "company_id": company_id,
        "email": "admin@example.com",
        "roles": ["admin", "user"],
        "exp": datetime.now(UTC) + timedelta(hours=1),
        "iat": datetime.now(UTC),
    }


@pytest.fixture
def expired_claims(company_id: str, generate_uuid: Callable) -> dict[str, Any]:
    """Expired JWT claims for testing authentication failures.

    Args:
        company_id: Company ID fixture.
        generate_uuid: UUID generator fixture.

    Returns:
        JWT claims dictionary with expired timestamp.
    """
    return {
        "user_id": generate_uuid(),
        "company_id": company_id,
        "email": "expired@example.com",
        "roles": ["user"],
        "exp": datetime.now(UTC) - timedelta(hours=1),
        "iat": datetime.now(UTC) - timedelta(hours=2),
    }


@pytest.fixture
def generate_jwt(jwt_secret: str) -> Callable[[dict], str]:
    """Factory to generate JWT tokens with custom claims.

    Args:
        jwt_secret: JWT secret key fixture.

    Returns:
        Function that generates JWT tokens from claims.

    Examples:
        >>> token = generate_jwt({'user_id': '123', 'email': 'test@example.com'})
    """

    def _generate(claims: dict[str, Any]) -> str:
        return jwt.encode(claims, jwt_secret, algorithm="HS256")

    return _generate


@pytest.fixture
def user_token(user_claims: dict, generate_jwt: Callable) -> str:
    """Generate standard user JWT token.

    Args:
        user_claims: User claims fixture.
        generate_jwt: JWT generator fixture.

    Returns:
        Encoded JWT token string.
    """
    return generate_jwt(user_claims)


@pytest.fixture
def admin_token(admin_claims: dict, generate_jwt: Callable) -> str:
    """Generate admin JWT token.

    Args:
        admin_claims: Admin claims fixture.
        generate_jwt: JWT generator fixture.

    Returns:
        Encoded JWT token string with admin roles.
    """
    return generate_jwt(admin_claims)


@pytest.fixture
def expired_token(expired_claims: dict, generate_jwt: Callable) -> str:
    """Generate expired JWT token for testing.

    Args:
        expired_claims: Expired claims fixture.
        generate_jwt: JWT generator fixture.

    Returns:
        Encoded JWT token that is already expired.
    """
    return generate_jwt(expired_claims)


@pytest.fixture
def authenticated_client(client: FlaskClient, user_token: str) -> FlaskClient:
    """Test client with authentication cookie set.

    Args:
        client: Flask test client fixture.
        user_token: User JWT token fixture.

    Returns:
        Flask test client with access_token cookie.
    """
    client.set_cookie("access_token", user_token)
    return client


@pytest.fixture
def admin_client(client: FlaskClient, admin_token: str) -> FlaskClient:
    """Test client with admin authentication cookie set.

    Args:
        client: Flask test client fixture.
        admin_token: Admin JWT token fixture.

    Returns:
        Flask test client with admin access_token cookie.
    """
    client.set_cookie("access_token", admin_token)
    return client


# === Mock Service Fixtures ===


@pytest.fixture
def mock_guardian_granted() -> Generator[Mock, None, None]:
    """Mock Guardian service returning access granted.

    Yields:
        Mock GuardianService.check_access that returns granted.
    """
    with patch(GUARDIAN_CHECK_ACCESS_PATH) as mock:
        mock.return_value = {"access_granted": True, "reason": "granted"}
        yield mock


@pytest.fixture
def mock_guardian_denied() -> Generator[Mock, None, None]:
    """Mock Guardian service returning access denied.

    Yields:
        Mock GuardianService.check_access that returns denied.
    """
    with patch(GUARDIAN_CHECK_ACCESS_PATH) as mock:
        mock.return_value = {"access_granted": False, "reason": "no_permission"}
        yield mock


@pytest.fixture
def mock_guardian_error() -> Generator[Mock, None, None]:
    """Mock Guardian service throwing error.

    Yields:
        Mock GuardianService.check_access that raises exception.
    """
    with patch(GUARDIAN_CHECK_ACCESS_PATH) as mock:
        mock.side_effect = Exception("Guardian service unavailable")
        yield mock


@pytest.fixture
def mock_guardian_custom() -> Callable:
    """Factory to create Guardian mock with custom response.

    Returns:
        Function that creates Guardian mock with specified response.

    Examples:
        >>> with mock_guardian_custom(access_granted=False, reason='rate_limit'):
        ...     # Test with custom Guardian response
    """

    def _mock(access_granted: bool = True, reason: str = "granted") -> Mock:
        patcher = patch(GUARDIAN_CHECK_ACCESS_PATH)
        mock = patcher.start()
        mock.return_value = {"access_granted": access_granted, "reason": reason}
        return mock

    return _mock


@pytest.fixture
def mock_identity_service() -> Generator[Mock, None, None]:
    """Mock Identity service for user lookups.

    Yields:
        Mock IdentityService.get_user that returns test user data.
    """
    with patch("app.services.identity.IdentityService.get_user") as mock:
        mock.return_value = {
            "id": str(uuid.uuid4()),
            "email": "test@example.com",
            "name": "Test User",
            "company_id": str(uuid.uuid4()),
        }
        yield mock
