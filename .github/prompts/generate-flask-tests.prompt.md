---
description: "Generate comprehensive unit and integration tests for Flask resources, models, schemas, and services following wfp-flask-template testing conventions"
agent: "Flask API Expert"
tools: ["edit", "search", "search/codebase", "read/problems", "execute/getTerminalOutput","execute/runInTerminal","read/terminalLastCommand","read/terminalSelection"]
---

# Generate Flask Tests

You are an expert in Python testing with pytest, creating comprehensive test suites for Flask applications that ensure code quality, correctness, and maintainability following wfp-flask-template testing standards.

## Task

Generate complete test files:
- **Unit tests** for models, schemas, and services (fast, isolated, mocked)
- **Integration tests** for resources/endpoints (with test database)
- Proper fixtures and test data
- Comprehensive coverage of happy paths and error cases
- Following Given-When-Then pattern

## Input Variables

- `${input:entityName}` - Singular entity name (e.g., "user", "project")
- `${input:entityNamePlural:entityName + 's'}` - Plural form
- `${input:testType:all}` - Test type: "unit", "integration", or "all"
- `${input:targetDir:tests}` - Base test directory

## File Structure

```
tests/
├── unit/
│   ├── models/
│   │   └── test_${entityName}_model.py
│   ├── schemas/
│   │   └── test_${entityName}_schema.py
│   └── services/
│       └── test_${entityName}_service.py  # If applicable
└── integration/
    └── resources/
        └── test_${entityName}_res.py
```

## Unit Tests - Model

Generate: `${targetDir}/unit/models/test_${entityName}_model.py`

```python
"""Unit tests for ${entityName.capitalize()} model.

Tests model creation, validation, relationships, and business logic
without database dependencies.
"""

import pytest
from datetime import datetime
from uuid import UUID

from src.app.models.${entityName}_model import ${entityName.capitalize()}


class Test${entityName.capitalize()}Model:
    """Test suite for ${entityName.capitalize()} model."""

    def test_create_${entityName}_with_required_fields(self, db_session):
        """Test creating ${entityName} with required fields only.

        Given: Valid required field data
        When: ${entityName.capitalize()} instance is created
        Then: Instance is created with correct attributes and defaults
        """
        ${entityName} = ${entityName.capitalize()}(
            name="Test ${entityName.capitalize()}"
        )
        db_session.add(${entityName})
        db_session.commit()

        assert ${entityName}.id is not None
        assert isinstance(${entityName}.id, UUID)
        assert ${entityName}.name == "Test ${entityName.capitalize()}"
        assert ${entityName}.is_active is True  # Default value
        assert ${entityName}.created_at is not None
        assert isinstance(${entityName}.created_at, datetime)
        assert ${entityName}.updated_at is not None

    def test_create_${entityName}_with_all_fields(self, db_session):
        """Test creating ${entityName} with all fields.

        Given: Complete field data
        When: ${entityName.capitalize()} instance is created
        Then: All fields are set correctly
        """
        ${entityName} = ${entityName.capitalize()}(
            name="Complete ${entityName.capitalize()}",
            description="Test description",
            is_active=False
        )
        db_session.add(${entityName})
        db_session.commit()

        assert ${entityName}.name == "Complete ${entityName.capitalize()}"
        assert ${entityName}.description == "Test description"
        assert ${entityName}.is_active is False

    def test_${entityName}_repr(self, db_session):
        """Test string representation.

        Given: ${entityName.capitalize()} instance
        When: __repr__ is called
        Then: Returns human-readable string with key attributes
        """
        ${entityName} = ${entityName.capitalize()}(name="Test ${entityName.capitalize()}")
        db_session.add(${entityName})
        db_session.commit()

        repr_str = repr(${entityName})

        assert "Test ${entityName.capitalize()}" in repr_str
        assert str(${entityName}.id) in repr_str
        assert "${entityName.capitalize()}" in repr_str

    def test_${entityName}_timestamps_auto_update(self, db_session):
        """Test timestamp automatic updates.

        Given: Existing ${entityName}
        When: ${entityName.capitalize()} is updated
        Then: updated_at timestamp changes, created_at remains same
        """
        ${entityName} = ${entityName.capitalize()}(name="Original Name")
        db_session.add(${entityName})
        db_session.commit()

        original_created_at = ${entityName}.created_at
        original_updated_at = ${entityName}.updated_at

        # Update
        ${entityName}.name = "Updated Name"
        db_session.commit()

        assert ${entityName}.created_at == original_created_at
        assert ${entityName}.updated_at > original_updated_at

    def test_validate_name(self, db_session):
        """Test name validation method.

        Given: ${entityName.capitalize()} with various name values
        When: validate_name is called
        Then: Returns appropriate validation result
        """
        valid_${entityName} = ${entityName.capitalize()}(name="Valid Name")
        assert valid_${entityName}.validate_name() is True

        empty_${entityName} = ${entityName.capitalize()}(name="")
        assert empty_${entityName}.validate_name() is False

        whitespace_${entityName} = ${entityName.capitalize()}(name="   ")
        assert whitespace_${entityName}.validate_name() is False


@pytest.fixture
def sample_${entityName}(db_session):
    """Fixture providing a sample ${entityName} for testing.

    Args:
        db_session: Test database session.

    Yields:
        Sample ${entityName.capitalize()} instance.
    """
    ${entityName} = ${entityName.capitalize()}(
        name="Sample ${entityName.capitalize()}",
        description="Sample for testing",
        is_active=True
    )
    db_session.add(${entityName})
    db_session.commit()

    yield ${entityName}

    # Cleanup
    db_session.delete(${entityName})
    db_session.commit()
```

## Unit Tests - Schemas

Generate: `${targetDir}/unit/schemas/test_${entityName}_schema.py`

```python
"""Unit tests for ${entityName.capitalize()} schemas.

Tests schema validation, serialization, and deserialization
for all CRUD operations.
"""

import pytest
from marshmallow import ValidationError

from src.app.schemas.${entityName}_schema import (
    ${entityName.capitalize()}Schema,
    ${entityName.capitalize()}CreateSchema,
    ${entityName.capitalize()}UpdateSchema,
    ${entityName.capitalize()}ReplaceSchema
)


class Test${entityName.capitalize()}CreateSchema:
    """Tests for ${entityName.capitalize()}CreateSchema."""

    @pytest.fixture
    def schema(self):
        """Create schema instance.

        Returns:
            ${entityName.capitalize()}CreateSchema instance.
        """
        return ${entityName.capitalize()}CreateSchema()

    def test_valid_data(self, schema):
        """Test schema with valid complete data.

        Given: Valid ${entityName} creation data
        When: load() is called
        Then: Data is validated and returned successfully
        """
        data = {
            "name": "Test ${entityName.capitalize()}",
            "description": "Test description",
            "is_active": True
        }

        result = schema.load(data)

        assert result["name"] == "Test ${entityName.capitalize()}"
        assert result["description"] == "Test description"
        assert result["is_active"] is True

    def test_valid_data_with_defaults(self, schema):
        """Test schema with minimal required data.

        Given: Only required fields provided
        When: load() is called
        Then: Data is validated with default values applied
        """
        data = {"name": "Test ${entityName.capitalize()}"}

        result = schema.load(data)

        assert result["name"] == "Test ${entityName.capitalize()}"
        assert result["is_active"] is True  # Default value

    def test_missing_required_name(self, schema):
        """Test schema with missing required name field.

        Given: Data without required name field
        When: load() is called
        Then: ValidationError is raised with appropriate message
        """
        data = {"description": "Missing name"}

        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)

        assert "name" in exc_info.value.messages
        assert "required" in str(exc_info.value.messages["name"]).lower()

    def test_name_too_short(self, schema):
        """Test name length validation (minimum).

        Given: Name shorter than minimum length
        When: load() is called
        Then: ValidationError is raised
        """
        data = {"name": ""}

        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)

        assert "name" in exc_info.value.messages

    def test_name_too_long(self, schema):
        """Test name length validation (maximum).

        Given: Name longer than maximum length
        When: load() is called
        Then: ValidationError is raised
        """
        data = {"name": "x" * 256}  # Exceeds 255 char limit

        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)

        assert "name" in exc_info.value.messages

    def test_name_whitespace_only(self, schema):
        """Test name validation rejects whitespace-only values.

        Given: Name with only whitespace
        When: load() is called
        Then: ValidationError is raised
        """
        data = {"name": "   "}

        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)

        assert "name" in exc_info.value.messages

    def test_invalid_field_type(self, schema):
        """Test validation with incorrect field types.

        Given: Field with wrong type
        When: load() is called
        Then: ValidationError is raised
        """
        data = {
            "name": "Test",
            "is_active": "not-a-boolean"
        }

        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)

        assert "is_active" in exc_info.value.messages


class Test${entityName.capitalize()}UpdateSchema:
    """Tests for ${entityName.capitalize()}UpdateSchema."""

    @pytest.fixture
    def schema(self):
        """Create schema instance."""
        return ${entityName.capitalize()}UpdateSchema()

    def test_valid_partial_update(self, schema):
        """Test schema with partial data.

        Given: Only some fields provided
        When: load() is called with partial=True
        Then: Only provided fields are validated
        """
        data = {"name": "Updated Name"}

        result = schema.load(data, partial=True)

        assert result["name"] == "Updated Name"
        assert "description" not in result

    def test_empty_data_rejected(self, schema):
        """Test that empty update is rejected.

        Given: No fields provided
        When: load() is called
        Then: ValidationError is raised
        """
        data = {}

        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)

        assert "at least one field" in str(exc_info.value.messages).lower()

    def test_all_fields_optional(self, schema):
        """Test that all fields are optional in update.

        Given: Any single field
        When: load() is called
        Then: Validation succeeds
        """
        # Test each field individually
        assert schema.load({"name": "Test"})
        assert schema.load({"description": "Test"})
        assert schema.load({"is_active": False})


class Test${entityName.capitalize()}ReplaceSchema:
    """Tests for ${entityName.capitalize()}ReplaceSchema."""

    @pytest.fixture
    def schema(self):
        """Create schema instance."""
        return ${entityName.capitalize()}ReplaceSchema()

    def test_valid_complete_data(self, schema):
        """Test schema with all required fields.

        Given: All required fields for replacement
        When: load() is called
        Then: Data is validated successfully
        """
        data = {
            "name": "Replaced Name",
            "description": "New description",
            "is_active": False
        }

        result = schema.load(data)

        assert result["name"] == "Replaced Name"
        assert result["is_active"] is False

    def test_missing_required_fields(self, schema):
        """Test schema rejects incomplete data.

        Given: Missing required fields
        When: load() is called
        Then: ValidationError is raised
        """
        data = {"name": "Test"}  # Missing is_active

        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)

        assert "is_active" in exc_info.value.messages


class Test${entityName.capitalize()}Schema:
    """Tests for ${entityName.capitalize()}Schema (serialization)."""

    @pytest.fixture
    def schema(self):
        """Create schema instance."""
        return ${entityName.capitalize()}Schema()

    def test_serialize_${entityName}(self, schema, sample_${entityName}):
        """Test serialization of model instance.

        Given: ${entityName.capitalize()} model instance
        When: dump() is called
        Then: Returns dictionary with all fields
        """
        result = schema.dump(sample_${entityName})

        assert result["id"] == str(sample_${entityName}.id)
        assert result["name"] == sample_${entityName}.name
        assert result["is_active"] == sample_${entityName}.is_active
        assert "created_at" in result
        assert "updated_at" in result

    def test_readonly_fields_not_loaded(self, schema):
        """Test that readonly fields are ignored during load.

        Given: Data including readonly fields
        When: load() is attempted
        Then: Readonly fields are ignored or cause error
        """
        data = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "Test",
            "created_at": "2024-01-01T00:00:00Z"
        }

        # Should either ignore or raise error for readonly fields
        # Behavior depends on schema configuration
        pass  # Implement based on your schema config


@pytest.fixture
def sample_${entityName}(db_session):
    """Fixture for sample ${entityName} instance."""
    from src.app.models.${entityName}_model import ${entityName.capitalize()}

    ${entityName} = ${entityName.capitalize()}(
        name="Sample ${entityName.capitalize()}",
        description="For testing",
        is_active=True
    )
    db_session.add(${entityName})
    db_session.commit()

    yield ${entityName}
```

## Integration Tests - Resources

Generate: `${targetDir}/integration/resources/test_${entityName}_res.py`

```python
"""Integration tests for ${entityName.capitalize()} resources.

Tests complete request/response cycle for ${entityName} endpoints
with real database and authentication.
"""

import pytest
from flask.testing import FlaskClient


class Test${entityName.capitalize()}ListResource:
    """Integration tests for ${entityName.capitalize()}ListResource."""

    def test_get_${entityNamePlural}_success(
        self,
        client: FlaskClient,
        auth_headers: dict
    ):
        """Test retrieving ${entityName} list.

        Given: Authenticated user with LIST permission
        When: GET /${entityNamePlural} is called
        Then: Returns 200 with paginated ${entityName} list
        """
        response = client.get("/v0/${entityNamePlural}", headers=auth_headers)

        assert response.status_code == 200
        assert "data" in response.json
        assert isinstance(response.json["data"], list)
        assert "page" in response.json
        assert "per_page" in response.json
        assert "total" in response.json

    def test_get_${entityNamePlural}_with_pagination(
        self,
        client: FlaskClient,
        auth_headers: dict
    ):
        """Test ${entityName} list with pagination parameters.

        Given: Pagination query parameters
        When: GET /${entityNamePlural}?page=1&per_page=10 is called
        Then: Returns paginated results with correct page info
        """
        response = client.get(
            "/v0/${entityNamePlural}?page=1&per_page=10",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json["page"] == 1
        assert response.json["per_page"] == 10

    def test_get_${entityNamePlural}_with_search(
        self,
        client: FlaskClient,
        auth_headers: dict,
        sample_${entityName}
    ):
        """Test ${entityName} list with search filter.

        Given: Search query parameter
        When: GET /${entityNamePlural}?search=test is called
        Then: Returns filtered results matching search term
        """
        response = client.get(
            f"/v0/${entityNamePlural}?search={sample_${entityName}.name}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert len(response.json["data"]) >= 1

    def test_get_${entityNamePlural}_unauthorized(self, client: FlaskClient):
        """Test ${entityName} list without authentication.

        Given: No authentication token
        When: GET /${entityNamePlural} is called
        Then: Returns 401 Unauthorized
        """
        response = client.get("/v0/${entityNamePlural}")

        assert response.status_code == 401

    def test_create_${entityName}_success(
        self,
        client: FlaskClient,
        auth_headers: dict
    ):
        """Test creating a new ${entityName}.

        Given: Valid ${entityName} data and CREATE permission
        When: POST /${entityNamePlural} is called
        Then: Returns 201 with created ${entityName}
        """
        data = {
            "name": "New ${entityName.capitalize()}",
            "description": "Integration test ${entityName}",
            "is_active": True
        }

        response = client.post(
            "/v0/${entityNamePlural}",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 201
        assert response.json["data"]["name"] == data["name"]
        assert response.json["data"]["description"] == data["description"]
        assert "id" in response.json["data"]
        assert "created_at" in response.json["data"]

    def test_create_${entityName}_validation_error(
        self,
        client: FlaskClient,
        auth_headers: dict
    ):
        """Test creating ${entityName} with invalid data.

        Given: Invalid ${entityName} data (missing required field)
        When: POST /${entityNamePlural} is called
        Then: Returns 400 with validation errors
        """
        data = {"description": "Missing name"}

        response = client.post(
            "/v0/${entityNamePlural}",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "errors" in response.json
        assert "name" in response.json["errors"]

    def test_create_${entityName}_unauthorized(self, client: FlaskClient):
        """Test creating ${entityName} without authentication.

        Given: No authentication token
        When: POST /${entityNamePlural} is called
        Then: Returns 401 Unauthorized
        """
        data = {"name": "Test ${entityName.capitalize()}"}

        response = client.post("/v0/${entityNamePlural}", json=data)

        assert response.status_code == 401


class Test${entityName.capitalize()}Resource:
    """Integration tests for ${entityName.capitalize()}Resource."""

    def test_get_${entityName}_success(
        self,
        client: FlaskClient,
        auth_headers: dict,
        sample_${entityName}
    ):
        """Test retrieving existing ${entityName}.

        Given: Existing ${entityName} and READ permission
        When: GET /${entityNamePlural}/<id> is called
        Then: Returns 200 with ${entityName} data
        """
        response = client.get(
            f"/v0/${entityNamePlural}/{sample_${entityName}.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json["data"]["id"] == str(sample_${entityName}.id)
        assert response.json["data"]["name"] == sample_${entityName}.name

    def test_get_${entityName}_not_found(
        self,
        client: FlaskClient,
        auth_headers: dict
    ):
        """Test retrieving non-existent ${entityName}.

        Given: Non-existent ${entityName} ID
        When: GET /${entityNamePlural}/<id> is called
        Then: Returns 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(
            f"/v0/${entityNamePlural}/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_${entityName}_success(
        self,
        client: FlaskClient,
        auth_headers: dict,
        sample_${entityName}
    ):
        """Test updating a ${entityName}.

        Given: Existing ${entityName} and UPDATE permission
        When: PATCH /${entityNamePlural}/<id> is called
        Then: Returns 200 with updated ${entityName}
        """
        data = {"name": "Updated Name"}

        response = client.patch(
            f"/v0/${entityNamePlural}/{sample_${entityName}.id}",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json["data"]["name"] == "Updated Name"
        assert response.json["data"]["id"] == str(sample_${entityName}.id)

    def test_update_${entityName}_validation_error(
        self,
        client: FlaskClient,
        auth_headers: dict,
        sample_${entityName}
    ):
        """Test updating ${entityName} with invalid data.

        Given: Invalid update data
        When: PATCH /${entityNamePlural}/<id> is called
        Then: Returns 400 with validation errors
        """
        data = {"name": ""}  # Empty name invalid

        response = client.patch(
            f"/v0/${entityNamePlural}/{sample_${entityName}.id}",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_replace_${entityName}_success(
        self,
        client: FlaskClient,
        auth_headers: dict,
        sample_${entityName}
    ):
        """Test replacing a ${entityName}.

        Given: Complete replacement data and UPDATE permission
        When: PUT /${entityNamePlural}/<id> is called
        Then: Returns 200 with replaced ${entityName}
        """
        data = {
            "name": "Completely New Name",
            "description": "New description",
            "is_active": False
        }

        response = client.put(
            f"/v0/${entityNamePlural}/{sample_${entityName}.id}",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json["data"]["name"] == data["name"]
        assert response.json["data"]["is_active"] == data["is_active"]

    def test_delete_${entityName}_success(
        self,
        client: FlaskClient,
        auth_headers: dict,
        sample_${entityName}
    ):
        """Test deleting a ${entityName}.

        Given: Existing ${entityName} and DELETE permission
        When: DELETE /${entityNamePlural}/<id> is called
        Then: Returns 204 No Content
        """
        response = client.delete(
            f"/v0/${entityNamePlural}/{sample_${entityName}.id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(
            f"/v0/${entityNamePlural}/{sample_${entityName}.id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_delete_${entityName}_not_found(
        self,
        client: FlaskClient,
        auth_headers: dict
    ):
        """Test deleting non-existent ${entityName}.

        Given: Non-existent ${entityName} ID
        When: DELETE /${entityNamePlural}/<id> is called
        Then: Returns 404 Not Found
        """
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = client.delete(
            f"/v0/${entityNamePlural}/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404


@pytest.fixture
def sample_${entityName}(app, db_session):
    """Fixture providing sample ${entityName} for testing.

    Args:
        app: Flask application instance.
        db_session: Test database session.

    Yields:
        Sample ${entityName.capitalize()} instance.
    """
    from src.app.models.${entityName}_model import ${entityName.capitalize()}

    ${entityName} = ${entityName.capitalize()}(
        name="Sample ${entityName.capitalize()}",
        description="For integration testing",
        is_active=True
    )

    with app.app_context():
        db_session.add(${entityName})
        db_session.commit()

        yield ${entityName}

        # Cleanup
        try:
            db_session.delete(${entityName})
            db_session.commit()
        except:
            db_session.rollback()


@pytest.fixture
def auth_headers(app):
    """Fixture providing authentication headers.

    Args:
        app: Flask application instance.

    Returns:
        Dictionary with Authorization header.
    """
    # Generate valid JWT token for testing
    # Implementation depends on your auth setup
    token = "valid-jwt-token"  # Replace with actual token generation

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
```

## Quality Checklist

- [ ] Unit tests use mocks and fixtures
- [ ] Integration tests use real database
- [ ] All tests follow Given-When-Then pattern
- [ ] Comprehensive docstrings on test methods
- [ ] Tests cover happy path and error cases
- [ ] Fixtures properly clean up test data
- [ ] Authentication mocked/configured for integration tests
- [ ] Validation errors tested
- [ ] Edge cases covered (empty, null, invalid types)
- [ ] Test names are descriptive and follow convention

## Running Tests

```bash
# All tests
make test-all

# Unit tests only (fast)
make test-unit

# Integration tests only
make test-integration

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/models/test_${entityName}_model.py -v
```

## Output

Present created test files and command to run them.
