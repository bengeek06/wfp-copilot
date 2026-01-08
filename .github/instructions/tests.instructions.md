---
applyTo: "tests/**/*.py"
excludeAgent: []
description: "Instructions for creating and maintaining test files in the project."
---

# Tests Instructions

## Purpose
Tests ensure code quality, catch regressions, and document expected behavior. Every module must have corresponding tests with >80% coverage. Use pytest for all testing with clear Given-When-Then structure.

## Test Organization

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/                          # Unit tests (isolated)
│   ├── models/
│   │   ├── test_user.py
│   │   └── test_order.py
│   ├── services/
│   │   ├── test_user.py
│   │   └── test_order.py
│   └── schemas/
│       ├── test_user.py
│       └── test_order.py
└── integration/                   # Integration tests (with DB/API)
    └── resources/
        ├── test_user.py
        └── test_order.py
```

## Naming Conventions

- **File name**: `test_<module_name>.py` (e.g., `test_user.py`)
- **Test class**: `Test<ClassName>` (e.g., `TestUserService`)
- **Test method**: `test_<what_it_tests>` (e.g., `test_create_user_success`)
- **Fixture name**: Descriptive, lowercase with underscores (e.g., `db_session`, `sample_user`)

## Test Structure (Given-When-Then)

Every test MUST follow this structure in docstring:

```python
def test_create_user_success(self, user_service, db_session):
    """Test successful user creation.

    Given: Valid user data
    When: create() is called
    Then: User is created and persisted to database
    """
    # Arrange (Given)
    data = {"email": "test@example.com", "username": "testuser"}

    # Act (When)
    user = user_service.create(data)

    # Assert (Then)
    assert user.id is not None
    assert user.email == "test@example.com"
    db_session.commit.assert_called_once()
```

## conftest.py Configuration

```python
"""Shared test fixtures and configuration.

This module provides common fixtures used across all tests
including database sessions, test clients, and sample data.
"""

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.api import create_app, db
from src.api.models.user import User


@pytest.fixture(scope="session")
def app() -> Flask:
    """Create Flask application for testing.

    Returns:
        Configured Flask test application.
    """
    app = create_app("testing")

    # Push application context
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture(scope="function")
def client(app: Flask) -> FlaskClient:
    """Create Flask test client.

    Args:
        app: Flask application fixture.

    Yields:
        Test client for making requests.
    """
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app: Flask) -> Session:
    """Create database session for testing.

    Args:
        app: Flask application fixture.

    Yields:
        Database session with automatic rollback.
    """
    connection = db.engine.connect()
    transaction = connection.begin()
    session = db.create_scoped_session(
        options={"bind": connection, "binds": {}}
    )

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Create a sample user for testing.

    Args:
        db_session: Database session fixture.

    Returns:
        Created user instance.
    """
    user = User(
        email="test@example.com",
        username="testuser",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_headers() -> dict:
    """Create authentication headers for testing.

    Returns:
        Dictionary with Authorization header.
    """
    return {
        "Authorization": "Bearer test-token-12345",
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_email_service():
    """Create mock email service.

    Returns:
        Mock email service for testing.
    """
    from unittest.mock import Mock
    service = Mock()
    service.send_email.return_value = True
    return service
```

## Unit Tests

### Testing Models

```python
"""Unit tests for User model."""

import pytest
from datetime import datetime
from src.api.models.user import User


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self, db_session):
        """Test creating a user instance.

        Given: Valid user data
        When: User instance is created
        Then: User has correct attributes
        """
        user = User(
            email="test@example.com",
            username="testuser"
        )

        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)

    def test_user_repr(self):
        """Test user string representation.

        Given: User instance with id and email
        When: repr() is called
        Then: Returns formatted string
        """
        user = User(id=1, email="test@example.com", username="test")

        result = repr(user)

        assert result == "<User(id=1, email='test@example.com')>"

    def test_user_email_uniqueness(self, db_session):
        """Test email uniqueness constraint.

        Given: User with email already exists
        When: Creating another user with same email
        Then: IntegrityError is raised
        """
        from sqlalchemy.exc import IntegrityError

        user1 = User(email="test@example.com", username="user1")
        db_session.add(user1)
        db_session.commit()

        user2 = User(email="test@example.com", username="user2")
        db_session.add(user2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_timestamps_on_update(self, db_session):
        """Test updated_at timestamp changes on update.

        Given: Existing user
        When: User is updated
        Then: updated_at timestamp is changed
        """
        user = User(email="test@example.com", username="testuser")
        db_session.add(user)
        db_session.commit()

        original_updated = user.updated_at

        # Update user
        user.username = "newusername"
        db_session.commit()

        assert user.updated_at > original_updated
```

### Testing Services

```python
"""Unit tests for UserService."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.api.services.user import UserService
from src.api.models.user import User
from src.api.utils.exceptions import NotFoundError, ConflictError


class TestUserService:
    """Tests for UserService."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session.

        Returns:
            Mock session object.
        """
        return Mock()

    @pytest.fixture
    def user_service(self, mock_db_session):
        """Create UserService with mocked dependencies.

        Args:
            mock_db_session: Mock database session.

        Returns:
            UserService instance.
        """
        return UserService(mock_db_session)

    def test_create_user_success(self, user_service, mock_db_session):
        """Test successful user creation.

        Given: Valid user data
        When: create() is called
        Then: User is created and committed
        """
        data = {
            "email": "test@example.com",
            "username": "testuser"
        }

        # Mock that email doesn't exist
        user_service.get_by_email = Mock(return_value=None)

        result = user_service.create(data)

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    def test_create_user_duplicate_email(self, user_service):
        """Test creating user with existing email.

        Given: Email already exists
        When: create() is called
        Then: ConflictError is raised
        """
        data = {"email": "existing@example.com", "username": "test"}

        # Mock that email exists
        existing_user = User(email="existing@example.com")
        user_service.get_by_email = Mock(return_value=existing_user)

        with pytest.raises(ConflictError) as exc:
            user_service.create(data)

        assert "already exists" in str(exc.value)

    def test_get_by_id_success(self, user_service, mock_db_session):
        """Test retrieving user by ID.

        Given: User exists in database
        When: get_by_id() is called
        Then: User is returned
        """
        user = User(id=1, email="test@example.com", username="test")
        mock_db_session.get.return_value = user

        result = user_service.get_by_id(1)

        assert result == user
        mock_db_session.get.assert_called_once_with(User, 1)

    def test_get_by_id_not_found(self, user_service, mock_db_session):
        """Test retrieving non-existent user.

        Given: User does not exist
        When: get_by_id() is called
        Then: NotFoundError is raised
        """
        mock_db_session.get.return_value = None

        with pytest.raises(NotFoundError) as exc:
            user_service.get_by_id(999)

        assert "not found" in str(exc.value)

    def test_list_with_pagination(self, user_service, mock_db_session):
        """Test listing users with pagination.

        Given: Multiple users exist
        When: list() is called with pagination
        Then: Paginated results are returned
        """
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.count.return_value = 50
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [User(), User()]

        users, total = user_service.list(page=2, per_page=20)

        assert len(users) == 2
        assert total == 50
        mock_query.offset.assert_called_with(20)
        mock_query.limit.assert_called_with(20)

    def test_update_user_success(self, user_service, mock_db_session):
        """Test updating a user.

        Given: User exists and valid update data
        When: update() is called
        Then: User is updated
        """
        user = User(id=1, email="old@example.com", username="old")
        user_service.get_by_id = Mock(return_value=user)
        user_service.get_by_email = Mock(return_value=None)

        data = {"email": "new@example.com"}
        result = user_service.update(1, data)

        assert user.email == "new@example.com"
        mock_db_session.commit.assert_called_once()

    def test_delete_user_success(self, user_service, mock_db_session):
        """Test deleting a user.

        Given: User exists
        When: delete() is called
        Then: User is deleted
        """
        user = User(id=1, email="test@example.com", username="test")
        user_service.get_by_id = Mock(return_value=user)

        user_service.delete(1)

        mock_db_session.delete.assert_called_once_with(user)
        mock_db_session.commit.assert_called_once()
```

### Testing Schemas

```python
"""Unit tests for user schemas."""

import pytest
from marshmallow import ValidationError
from src.api.schemas.user import (
    UserSchema,
    UserCreateSchema,
    UserUpdateSchema
)


class TestUserCreateSchema:
    """Tests for UserCreateSchema."""

    @pytest.fixture
    def schema(self):
        """Create schema instance.

        Returns:
            UserCreateSchema instance.
        """
        return UserCreateSchema()

    def test_valid_data(self, schema):
        """Test schema with valid data.

        Given: Valid user data
        When: load() is called
        Then: Data is validated successfully
        """
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }

        result = schema.load(data)

        assert result["email"] == "test@example.com"
        assert result["username"] == "testuser"
        assert "password" in result

    def test_missing_required_email(self, schema):
        """Test missing required field.

        Given: Data without email
        When: load() is called
        Then: ValidationError is raised
        """
        data = {"username": "test", "password": "SecurePass123!"}

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "email" in exc.value.messages

    def test_invalid_email_format(self, schema):
        """Test invalid email format.

        Given: Malformed email
        When: load() is called
        Then: ValidationError is raised
        """
        data = {
            "email": "not-an-email",
            "username": "test",
            "password": "SecurePass123!"
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "email" in exc.value.messages

    def test_weak_password(self, schema):
        """Test weak password validation.

        Given: Password without required characters
        When: load() is called
        Then: ValidationError is raised
        """
        data = {
            "email": "test@example.com",
            "username": "test",
            "password": "weak"
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "password" in exc.value.messages

    def test_username_too_short(self, schema):
        """Test username length validation.

        Given: Username shorter than 3 characters
        When: load() is called
        Then: ValidationError is raised
        """
        data = {
            "email": "test@example.com",
            "username": "ab",
            "password": "SecurePass123!"
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "username" in exc.value.messages

    def test_username_invalid_characters(self, schema):
        """Test username character validation.

        Given: Username with invalid characters
        When: load() is called
        Then: ValidationError is raised
        """
        data = {
            "email": "test@example.com",
            "username": "test user!",
            "password": "SecurePass123!"
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "username" in exc.value.messages
```

## Integration Tests

### Testing Resources (API Endpoints)

```python
"""Integration tests for user resources."""

import pytest
from flask.testing import FlaskClient
from src.api.models.user import User


class TestUserListResource:
    """Tests for UserListResource."""

    def test_get_users_empty_list(self, client: FlaskClient):
        """Test retrieving empty user list.

        Given: No users in database
        When: GET /users is called
        Then: Returns 200 with empty list
        """
        response = client.get("/users")

        assert response.status_code == 200
        assert response.json["data"] == []
        assert response.json["total"] == 0

    def test_get_users_with_data(self, client: FlaskClient, sample_user):
        """Test retrieving user list with data.

        Given: Users exist in database
        When: GET /users is called
        Then: Returns 200 with user list
        """
        response = client.get("/users")

        assert response.status_code == 200
        assert len(response.json["data"]) > 0
        assert response.json["total"] > 0

    def test_get_users_pagination(self, client: FlaskClient):
        """Test user list pagination.

        Given: Multiple users exist
        When: GET /users with page and per_page
        Then: Returns correct page of results
        """
        response = client.get("/users?page=1&per_page=5")

        assert response.status_code == 200
        assert response.json["page"] == 1
        assert response.json["per_page"] == 5

    def test_get_users_invalid_pagination(self, client: FlaskClient):
        """Test invalid pagination parameters.

        Given: Invalid page number
        When: GET /users with page=0
        Then: Returns 400 error
        """
        response = client.get("/users?page=0")

        assert response.status_code == 400
        assert "error" in response.json or "message" in response.json

    def test_create_user_success(self, client: FlaskClient, auth_headers):
        """Test creating a new user.

        Given: Valid user data and authentication
        When: POST /users is called
        Then: Returns 201 with created user
        """
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePass123!"
        }

        response = client.post("/users", json=data, headers=auth_headers)

        assert response.status_code == 201
        assert response.json["data"]["email"] == data["email"]
        assert "password" not in response.json["data"]

    def test_create_user_validation_error(self, client: FlaskClient, auth_headers):
        """Test creating user with invalid data.

        Given: Invalid email format
        When: POST /users is called
        Then: Returns 400 with validation errors
        """
        data = {
            "email": "invalid",
            "username": "test",
            "password": "SecurePass123!"
        }

        response = client.post("/users", json=data, headers=auth_headers)

        assert response.status_code == 400
        assert "errors" in response.json

    def test_create_user_duplicate_email(
        self,
        client: FlaskClient,
        auth_headers,
        sample_user
    ):
        """Test creating user with existing email.

        Given: Email already exists
        When: POST /users is called
        Then: Returns 409 conflict error
        """
        data = {
            "email": sample_user.email,
            "username": "different",
            "password": "SecurePass123!"
        }

        response = client.post("/users", json=data, headers=auth_headers)

        assert response.status_code == 409

    def test_create_user_unauthorized(self, client: FlaskClient):
        """Test creating user without authentication.

        Given: No authentication token
        When: POST /users is called
        Then: Returns 401 unauthorized
        """
        data = {
            "email": "test@example.com",
            "username": "test",
            "password": "SecurePass123!"
        }

        response = client.post("/users", json=data)

        assert response.status_code == 401


class TestUserResource:
    """Tests for UserResource."""

    def test_get_user_success(self, client: FlaskClient, sample_user):
        """Test retrieving existing user.

        Given: User exists in database
        When: GET /users/<id> is called
        Then: Returns 200 with user data
        """
        response = client.get(f"/users/{sample_user.id}")

        assert response.status_code == 200
        assert response.json["data"]["id"] == sample_user.id
        assert response.json["data"]["email"] == sample_user.email

    def test_get_user_not_found(self, client: FlaskClient):
        """Test retrieving non-existent user.

        Given: User ID does not exist
        When: GET /users/<id> is called
        Then: Returns 404 not found
        """
        response = client.get("/users/99999")

        assert response.status_code == 404

    def test_update_user_success(
        self,
        client: FlaskClient,
        auth_headers,
        sample_user
    ):
        """Test updating a user.

        Given: Valid update data and authentication
        When: PUT /users/<id> is called
        Then: Returns 200 with updated user
        """
        data = {"username": "updated_name"}

        response = client.put(
            f"/users/{sample_user.id}",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json["data"]["username"] == "updated_name"

    def test_update_user_not_found(self, client: FlaskClient, auth_headers):
        """Test updating non-existent user.

        Given: User ID does not exist
        When: PUT /users/<id> is called
        Then: Returns 404 not found
        """
        data = {"username": "test"}

        response = client.put("/users/99999", json=data, headers=auth_headers)

        assert response.status_code == 404

    def test_partial_update_user(
        self,
        client: FlaskClient,
        auth_headers,
        sample_user
    ):
        """Test partial user update.

        Given: Only some fields to update
        When: PATCH /users/<id> is called
        Then: Returns 200 with updated fields
        """
        data = {"username": "patched_name"}

        response = client.patch(
            f"/users/{sample_user.id}",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json["data"]["username"] == "patched_name"
        # Email should remain unchanged
        assert response.json["data"]["email"] == sample_user.email

    def test_delete_user_success(
        self,
        client: FlaskClient,
        auth_headers,
        sample_user
    ):
        """Test deleting a user.

        Given: User exists and valid authentication
        When: DELETE /users/<id> is called
        Then: Returns 204 no content
        """
        response = client.delete(
            f"/users/{sample_user.id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify user is deleted
        get_response = client.get(f"/users/{sample_user.id}")
        assert get_response.status_code == 404

    def test_delete_user_unauthorized(self, client: FlaskClient, sample_user):
        """Test deleting user without authentication.

        Given: No authentication token
        When: DELETE /users/<id> is called
        Then: Returns 401 unauthorized
        """
        response = client.delete(f"/users/{sample_user.id}")

        assert response.status_code == 401
```

## Advanced Testing Patterns

### Parametrized Tests

```python
@pytest.mark.parametrize("email,expected", [
    ("test@example.com", True),
    ("invalid", False),
    ("test@", False),
    ("@example.com", False),
])
def test_email_validation(email, expected):
    """Test email validation with multiple inputs.

    Given: Various email formats
    When: Validation is performed
    Then: Returns expected result
    """
    from src.api.utils.validators import validate_email
    result = validate_email(email)
    assert result == expected
```

### Testing Exceptions

```python
def test_service_raises_not_found():
    """Test service raises correct exception.

    Given: Non-existent user ID
    When: get_by_id() is called
    Then: NotFoundError is raised with correct message
    """
    service = UserService(mock_session)

    with pytest.raises(NotFoundError) as exc:
        service.get_by_id(999)

    assert "User with id 999 not found" in str(exc.value)
```

### Mocking External Services

```python
@patch('src.api.services.user.send_email')
def test_user_creation_sends_email(mock_send_email, user_service):
    """Test email is sent on user creation.

    Given: Valid user data
    When: User is created
    Then: Welcome email is sent
    """
    data = {"email": "test@example.com", "username": "test"}

    user_service.create(data)

    mock_send_email.assert_called_once()
    call_args = mock_send_email.call_args
    assert call_args[0][0] == "test@example.com"
```

## Test Coverage

### Running Tests with Coverage

```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/unit/services/test_user.py -v

# Run with specific marker
pytest -m unit

# Run with coverage threshold
pytest --cov=src --cov-fail-under=80
```

### Coverage Requirements

- **Overall coverage**: Minimum 80%
- **Critical paths**: 100% (authentication, payment, data modification)
- **New code**: Must maintain or improve coverage

## What NOT to Do

- ❌ Tests without docstrings
- ❌ Missing Given-When-Then structure
- ❌ Testing implementation details instead of behavior
- ❌ Dependent tests (test order matters)
- ❌ Shared mutable state between tests
- ❌ Testing multiple things in one test
- ❌ Incomplete test names (test_user instead of test_create_user_success)
- ❌ French docstrings or test names
- ❌ Leaving commented-out tests
- ❌ Tests without assertions

## Pytest Markers

Define custom markers in `pytest.ini` or `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow-running tests",
    "db: Tests requiring database",
]
```

Use markers in tests:

```python
@pytest.mark.unit
def test_user_validation():
    """Unit test for user validation."""
    pass

@pytest.mark.integration
@pytest.mark.db
def test_user_creation_with_db():
    """Integration test with database."""
    pass
```

## Test Documentation

Every test must have:
1. Descriptive name explaining what is tested
2. Docstring with Given-When-Then structure
3. Clear assertions with helpful failure messages

```python
def test_create_user_with_invalid_email_format(self, user_service):
    """Test user creation fails with invalid email.

    Given: User data with malformed email address
    When: create() method is called
    Then: ValidationError is raised with clear message
    """
    data = {"email": "not-an-email", "username": "test"}

    with pytest.raises(ValidationError) as exc:
        user_service.create(data)

    assert "email" in str(exc.value), "Error should mention email field"
    assert "invalid" in str(exc.value).lower(), "Error should indicate invalidity"
```
