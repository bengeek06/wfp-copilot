---
description: "Generate a complete CRUD resource for Flask API including SQLAlchemy model, Marshmallow schemas, Flask-RESTful resource classes, route registration, and comprehensive tests following wfp-flask-template architecture"
agent: "Flask API Expert"
tools: ["edit", "search", "search/codebase", "execute/getTerminalOutput", "execute/runInTerminal", "read/terminalLastCommand", "read/terminalSelection", "execute/createAndRunTask", "execute/getTaskOutput", "execute/runTask", "read/problems", "todo"]
---

# Generate Flask Resource

You are an expert Flask API developer specialized in creating complete, production-ready CRUD resources following the wfp-flask-template architecture and best practices.

## Task

Generate a complete Flask resource with all necessary components:
- **SQLAlchemy model** with proper mixins and relationships
- **Marshmallow schemas** (Base, Create, Update, Replace)
- **Flask-RESTful resources** (ListResource and Resource)
- **Route registration** in routes.py
- **Unit and integration tests**
- **Constants** definitions

## Input Variables

- `${input:entityName}` - Singular entity name (e.g., "user", "product", "order")
- `${input:entityNamePlural:entityName}` - Plural form (defaults to entityName + "s")
- `${input:targetDir:src/app}` - Base directory for the application

## Architecture Pattern

Follow the **layered structure**: Resources (HTTP) → Schemas (validation) → Models (database)

```
${targetDir}/
├── models/${entityName}_model.py      # SQLAlchemy model
├── schemas/${entityName}_schema.py    # Marshmallow schemas
├── resources/${entityName}_res.py     # Flask-RESTful resources
├── routes.py                          # Route registration
└── constants/${entityName}_constants.py  # Constants
tests/
├── unit/
│   ├── models/test_${entityName}_model.py
│   └── schemas/test_${entityName}_schema.py
└── integration/
    └── resources/test_${entityName}_res.py
```

## Step-by-Step Process

### 1. Analyze Context
- Search codebase for existing patterns and imports
- Identify base classes, mixins, and utilities available
- Check existing models for relationship patterns

### 2. Create SQLAlchemy Model
Generate `${targetDir}/models/${entityName}_model.py`:
- Inherit from `UUIDMixin, TimestampMixin, db.Model`
- Use proper type hints with `Mapped[]` and `mapped_column()`
- Add `__tablename__` using snake_case plural
- Include proper indexes and constraints
- Add relationships if needed
- Follow models.instructions.md guidelines

**Example**:
```python
"""${entityName.capitalize()} model.

Database model for ${entityName} entity with UUID primary key
and automatic timestamp management.
"""

from sqlalchemy import String, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column
from ..models.base import UUIDMixin, TimestampMixin
from .. import db


class ${entityName.capitalize()}(UUIDMixin, TimestampMixin, db.Model):
    """${entityName.capitalize()} database model.

    Attributes:
        id: Unique UUID identifier.
        name: ${entityName.capitalize()} name.
        description: Optional description.
        is_active: Active status flag.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    __tablename__ = "${entityNamePlural}"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index("idx_${entityName}_name_active", "name", "is_active"),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<${entityName.capitalize()}(id={self.id}, name={self.name})>"
```

### 3. Create Marshmallow Schemas
Generate `${targetDir}/schemas/${entityName}_schema.py`:
- **Base schema** for serialization (all fields, dump_only for id/timestamps)
- **Create schema** for POST requests (required fields only)
- **Update schema** for PATCH requests (all fields optional)
- **Replace schema** for PUT requests (all required fields)
- Use `SQLAlchemyAutoSchema` when possible
- Add custom validation with `@validates` and `@validates_schema`
- Follow schemas.instructions.md guidelines

**Example**:
```python
"""${entityName.capitalize()} schemas for validation and serialization."""

from marshmallow import Schema, fields, validate, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from ..models.${entityName}_model import ${entityName.capitalize()}


class ${entityName.capitalize()}Schema(SQLAlchemyAutoSchema):
    """Base schema for ${entityName} serialization.

    Used for API responses. Includes all fields.
    """

    class Meta:
        model = ${entityName.capitalize()}
        load_instance = True
        include_fk = True

    id = fields.UUID(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ${entityName.capitalize()}CreateSchema(Schema):
    """Schema for creating a ${entityName}.

    Validates POST /${entityNamePlural} requests.
    """

    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(validate=validate.Length(max=1000))
    is_active = fields.Bool(load_default=True)

    @validates("name")
    def validate_name(self, value: str) -> None:
        """Validate name is not empty after stripping."""
        if not value.strip():
            raise ValidationError("Name cannot be empty or whitespace only")


class ${entityName.capitalize()}UpdateSchema(Schema):
    """Schema for partially updating a ${entityName}.

    Validates PATCH /${entityNamePlural}/<id> requests.
    All fields are optional.
    """

    name = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(validate=validate.Length(max=1000))
    is_active = fields.Bool()


class ${entityName.capitalize()}ReplaceSchema(Schema):
    """Schema for completely replacing a ${entityName}.

    Validates PUT /${entityNamePlural}/<id> requests.
    All business fields are required.
    """

    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(validate=validate.Length(max=1000))
    is_active = fields.Bool(required=True)
```

### 4. Create Flask-RESTful Resources
Generate `${targetDir}/resources/${entityName}_res.py`:
- **ListResource** for collection operations (GET list, POST create)
- **Resource** for item operations (GET, PUT, PATCH, DELETE)
- Inject dependencies in `__init__`
- Add decorators: `@require_jwt_auth`, `@access_required`, `@limiter.limit`
- Use proper response helpers: `success_response`, `error_response`, `paginated_response`
- Handle exceptions: `ValidationError`, `NotFoundError`, `ConflictError`
- Follow resources.instructions.md guidelines

**Example**:
```python
"""${entityName.capitalize()} resource endpoints.

REST API endpoints for ${entityName} management including list,
create, retrieve, update and delete operations.
"""

from flask import request
from flask_restful import Resource
from marshmallow import ValidationError
from ..schemas.${entityName}_schema import (
    ${entityName.capitalize()}Schema,
    ${entityName.capitalize()}CreateSchema,
    ${entityName.capitalize()}UpdateSchema,
    ${entityName.capitalize()}ReplaceSchema
)
from ..models.${entityName}_model import ${entityName.capitalize()}
from ..utils.decorators import require_jwt_auth, access_required
from ..utils.responses import success_response, error_response, paginated_response
from ..utils.exceptions import NotFoundError, ConflictError
from ..constants.operations import Operation
from .. import db, limiter


class ${entityName.capitalize()}ListResource(Resource):
    """Resource for ${entityName} collection operations.

    Handles /v0/${entityNamePlural} endpoint for listing and creating ${entityNamePlural}.
    """

    def __init__(self) -> None:
        """Initialize with schemas."""
        self.schema = ${entityName.capitalize()}Schema()
        self.create_schema = ${entityName.capitalize()}CreateSchema()

    @require_jwt_auth
    @access_required(Operation.LIST)
    @limiter.limit("100/minute")
    def get(self) -> tuple[dict, int]:
        """List all ${entityNamePlural} with pagination.

        Query Parameters:
            page (int): Page number (default: 1)
            per_page (int): Items per page (default: 20, max: 100)
            search (str): Search term for name
            is_active (bool): Filter by active status

        Returns:
            Paginated list of ${entityNamePlural} with metadata.
        """
        try:
            page = request.args.get("page", 1, type=int)
            per_page = min(request.args.get("per_page", 20, type=int), 100)
            search = request.args.get("search", type=str)
            is_active = request.args.get("is_active", type=bool)

            query = ${entityName.capitalize()}.query

            if search:
                query = query.filter(${entityName.capitalize()}.name.ilike(f"%{search}%"))

            if is_active is not None:
                query = query.filter(${entityName.capitalize()}.is_active == is_active)

            pagination = query.order_by(${entityName.capitalize()}.created_at.desc()).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

            return paginated_response(
                data=self.schema.dump(pagination.items, many=True),
                page=page,
                per_page=per_page,
                total=pagination.total
            )

        except Exception as e:
            return error_response(
                f"Failed to retrieve ${entityNamePlural}",
                status_code=500,
                errors={"detail": str(e)}
            )

    @require_jwt_auth
    @access_required(Operation.CREATE)
    @limiter.limit("20/minute")
    def post(self) -> tuple[dict, int]:
        """Create a new ${entityName}.

        Request Body:
            JSON with ${entityName} data (validated by CreateSchema)

        Returns:
            Created ${entityName} with 201 status.
        """
        try:
            data = self.create_schema.load(request.get_json())

            ${entityName} = ${entityName.capitalize()}(**data)
            db.session.add(${entityName})
            db.session.commit()

            return success_response(
                data=self.schema.dump(${entityName}),
                message="${entityName.capitalize()} created successfully",
                status_code=201
            )

        except ValidationError as e:
            return error_response(
                "Validation failed",
                status_code=400,
                errors=e.messages
            )
        except Exception as e:
            db.session.rollback()
            return error_response(
                f"Failed to create ${entityName}",
                status_code=500,
                errors={"detail": str(e)}
            )


class ${entityName.capitalize()}Resource(Resource):
    """Resource for individual ${entityName} operations.

    Handles /v0/${entityNamePlural}/<${entityName}_id> endpoint.
    """

    def __init__(self) -> None:
        """Initialize with schemas."""
        self.schema = ${entityName.capitalize()}Schema()
        self.update_schema = ${entityName.capitalize()}UpdateSchema()
        self.replace_schema = ${entityName.capitalize()}ReplaceSchema()

    @require_jwt_auth
    @access_required(Operation.READ)
    @limiter.limit("200/minute")
    def get(self, ${entityName}_id: str) -> tuple[dict, int]:
        """Retrieve a specific ${entityName}.

        Args:
            ${entityName}_id: UUID of the ${entityName}.

        Returns:
            ${entityName.capitalize()} data with 200 status.
        """
        try:
            ${entityName} = ${entityName.capitalize()}.query.get(${entityName}_id)

            if not ${entityName}:
                raise NotFoundError(f"${entityName.capitalize()} not found")

            return success_response(data=self.schema.dump(${entityName}))

        except NotFoundError as e:
            return error_response(str(e), status_code=404)
        except Exception as e:
            return error_response(
                f"Failed to retrieve ${entityName}",
                status_code=500,
                errors={"detail": str(e)}
            )

    @require_jwt_auth
    @access_required(Operation.UPDATE)
    @limiter.limit("50/minute")
    def patch(self, ${entityName}_id: str) -> tuple[dict, int]:
        """Partially update a ${entityName}.

        Args:
            ${entityName}_id: UUID of the ${entityName}.

        Returns:
            Updated ${entityName} with 200 status.
        """
        try:
            ${entityName} = ${entityName.capitalize()}.query.get(${entityName}_id)

            if not ${entityName}:
                raise NotFoundError(f"${entityName.capitalize()} not found")

            data = self.update_schema.load(request.get_json(), partial=True)

            for key, value in data.items():
                setattr(${entityName}, key, value)

            db.session.commit()

            return success_response(
                data=self.schema.dump(${entityName}),
                message="${entityName.capitalize()} updated successfully"
            )

        except ValidationError as e:
            return error_response(
                "Validation failed",
                status_code=400,
                errors=e.messages
            )
        except NotFoundError as e:
            return error_response(str(e), status_code=404)
        except Exception as e:
            db.session.rollback()
            return error_response(
                f"Failed to update ${entityName}",
                status_code=500,
                errors={"detail": str(e)}
            )

    @require_jwt_auth
    @access_required(Operation.UPDATE)
    @limiter.limit("50/minute")
    def put(self, ${entityName}_id: str) -> tuple[dict, int]:
        """Completely replace a ${entityName}.

        Args:
            ${entityName}_id: UUID of the ${entityName}.

        Returns:
            Replaced ${entityName} with 200 status.
        """
        try:
            ${entityName} = ${entityName.capitalize()}.query.get(${entityName}_id)

            if not ${entityName}:
                raise NotFoundError(f"${entityName.capitalize()} not found")

            data = self.replace_schema.load(request.get_json())

            for key, value in data.items():
                setattr(${entityName}, key, value)

            db.session.commit()

            return success_response(
                data=self.schema.dump(${entityName}),
                message="${entityName.capitalize()} replaced successfully"
            )

        except ValidationError as e:
            return error_response(
                "Validation failed",
                status_code=400,
                errors=e.messages
            )
        except NotFoundError as e:
            return error_response(str(e), status_code=404)
        except Exception as e:
            db.session.rollback()
            return error_response(
                f"Failed to replace ${entityName}",
                status_code=500,
                errors={"detail": str(e)}
            )

    @require_jwt_auth
    @access_required(Operation.DELETE)
    @limiter.limit("20/minute")
    def delete(self, ${entityName}_id: str) -> tuple[dict, int]:
        """Delete a ${entityName}.

        Args:
            ${entityName}_id: UUID of the ${entityName}.

        Returns:
            Empty response with 204 status.
        """
        try:
            ${entityName} = ${entityName.capitalize()}.query.get(${entityName}_id)

            if not ${entityName}:
                raise NotFoundError(f"${entityName.capitalize()} not found")

            db.session.delete(${entityName})
            db.session.commit()

            return success_response(
                message="${entityName.capitalize()} deleted successfully",
                status_code=204
            )

        except NotFoundError as e:
            return error_response(str(e), status_code=404)
        except Exception as e:
            db.session.rollback()
            return error_response(
                f"Failed to delete ${entityName}",
                status_code=500,
                errors={"detail": str(e)}
            )
```

### 5. Register Routes
Update `${targetDir}/routes.py`:
- Import the new resource classes
- Add routes with versioned prefix `/v0/${entityNamePlural}`
- Follow existing route patterns

**Add to routes.py**:
```python
from .resources.${entityName}_res import ${entityName.capitalize()}ListResource, ${entityName.capitalize()}Resource

# In register_routes function:
api.add_resource(${entityName.capitalize()}ListResource, f"/{api_version}/${entityNamePlural}")
api.add_resource(${entityName.capitalize()}Resource, f"/{api_version}/${entityNamePlural}/<string:${entityName}_id>")
```

### 6. Create Constants
Generate `${targetDir}/constants/${entityName}_constants.py` if needed:
```python
"""${entityName.capitalize()} related constants."""

${entityName.upper()}_RESOURCE_NAME = "${entityNamePlural}"
${entityName.upper()}_MAX_NAME_LENGTH = 255
${entityName.upper()}_MAX_DESCRIPTION_LENGTH = 1000
```

### 7. Generate Tests

#### Unit Tests - Model
Generate `tests/unit/models/test_${entityName}_model.py`:
```python
"""Unit tests for ${entityName} model."""

import pytest
from src.app.models.${entityName}_model import ${entityName.capitalize()}


class Test${entityName.capitalize()}Model:
    """Tests for ${entityName.capitalize()} model."""

    def test_create_${entityName}(self, db_session):
        """Test creating a ${entityName}.

        Given: Valid ${entityName} data
        When: ${entityName.capitalize()} is created
        Then: Instance has correct attributes
        """
        ${entityName} = ${entityName.capitalize()}(
            name="Test ${entityName.capitalize()}",
            description="Test description"
        )
        db_session.add(${entityName})
        db_session.commit()

        assert ${entityName}.id is not None
        assert ${entityName}.name == "Test ${entityName.capitalize()}"
        assert ${entityName}.is_active is True
        assert ${entityName}.created_at is not None

    def test_${entityName}_repr(self, db_session):
        """Test string representation."""
        ${entityName} = ${entityName.capitalize()}(name="Test")
        db_session.add(${entityName})
        db_session.commit()

        assert "Test" in repr(${entityName})
        assert str(${entityName}.id) in repr(${entityName})
```

#### Unit Tests - Schemas
Generate `tests/unit/schemas/test_${entityName}_schema.py`:
```python
"""Unit tests for ${entityName} schemas."""

import pytest
from marshmallow import ValidationError
from src.app.schemas.${entityName}_schema import (
    ${entityName.capitalize()}CreateSchema,
    ${entityName.capitalize()}UpdateSchema
)


class Test${entityName.capitalize()}CreateSchema:
    """Tests for ${entityName.capitalize()}CreateSchema."""

    def test_valid_data(self):
        """Test schema with valid data."""
        schema = ${entityName.capitalize()}CreateSchema()
        data = {
            "name": "Test ${entityName.capitalize()}",
            "description": "Test description"
        }

        result = schema.load(data)

        assert result["name"] == "Test ${entityName.capitalize()}"
        assert result["description"] == "Test description"

    def test_missing_required_name(self):
        """Test schema with missing name."""
        schema = ${entityName.capitalize()}CreateSchema()
        data = {"description": "Test"}

        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)

        assert "name" in exc_info.value.messages
```

#### Integration Tests - Resources
Generate `tests/integration/resources/test_${entityName}_res.py`:
```python
"""Integration tests for ${entityName} resources."""

import pytest
from flask.testing import FlaskClient


class Test${entityName.capitalize()}ListResource:
    """Tests for ${entityName.capitalize()}ListResource."""

    def test_get_${entityNamePlural}_success(self, client: FlaskClient, auth_headers):
        """Test retrieving ${entityName} list.

        Given: ${entityName.capitalize()}s exist
        When: GET /${entityNamePlural} is called
        Then: Returns 200 with list
        """
        response = client.get("/v0/${entityNamePlural}", headers=auth_headers)

        assert response.status_code == 200
        assert "data" in response.json
        assert isinstance(response.json["data"], list)

    def test_create_${entityName}_success(self, client: FlaskClient, auth_headers):
        """Test creating a ${entityName}."""
        data = {
            "name": "New ${entityName.capitalize()}",
            "description": "Test description"
        }

        response = client.post("/v0/${entityNamePlural}", json=data, headers=auth_headers)

        assert response.status_code == 201
        assert response.json["data"]["name"] == data["name"]

    def test_create_${entityName}_validation_error(self, client: FlaskClient, auth_headers):
        """Test creating ${entityName} with invalid data."""
        data = {}  # Missing required name

        response = client.post("/v0/${entityNamePlural}", json=data, headers=auth_headers)

        assert response.status_code == 400
        assert "errors" in response.json


class Test${entityName.capitalize()}Resource:
    """Tests for ${entityName.capitalize()}Resource."""

    def test_get_${entityName}_success(self, client: FlaskClient, auth_headers, sample_${entityName}):
        """Test retrieving existing ${entityName}."""
        response = client.get(
            f"/v0/${entityNamePlural}/{sample_${entityName}.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json["data"]["id"] == str(sample_${entityName}.id)

    def test_get_${entityName}_not_found(self, client: FlaskClient, auth_headers):
        """Test retrieving non-existent ${entityName}."""
        response = client.get(
            "/v0/${entityNamePlural}/00000000-0000-0000-0000-000000000000",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_${entityName}_success(self, client: FlaskClient, auth_headers, sample_${entityName}):
        """Test updating a ${entityName}."""
        data = {"name": "Updated Name"}

        response = client.patch(
            f"/v0/${entityNamePlural}/{sample_${entityName}.id}",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json["data"]["name"] == "Updated Name"

    def test_delete_${entityName}_success(self, client: FlaskClient, auth_headers, sample_${entityName}):
        """Test deleting a ${entityName}."""
        response = client.delete(
            f"/v0/${entityNamePlural}/{sample_${entityName}.id}",
            headers=auth_headers
        )

        assert response.status_code == 204
```

### 8. Database Migration
After creating the model, generate and apply migration:
```bash
flask db migrate -m "Add ${entityName.capitalize()} model"
flask db upgrade
```

### 9. Validation
- Run tests: `make test-all`
- Check formatting: `make format`
- Type checking: `mypy ${targetDir}`
- Linting: `ruff check ${targetDir}`

## Quality Checklist

- [ ] Model uses UUIDMixin and TimestampMixin
- [ ] All schemas have proper validation
- [ ] Resources have authentication decorators
- [ ] Resources have rate limiting
- [ ] All methods have docstrings (English)
- [ ] Type hints on all functions
- [ ] Tests cover happy path and errors
- [ ] Routes registered with API version prefix
- [ ] No hardcoded strings (use constants)
- [ ] Proper exception handling
- [ ] Database session management (commit/rollback)

## Notes

- Follow existing patterns in the codebase
- Use snake_case for file names and database tables
- Use PascalCase for class names
- Always include English docstrings
- Respect the instructions files (models, schemas, resources, tests)
- Create fixtures for integration tests
- Never commit without passing tests

## Output

Present a summary of created files and next steps for the user.
