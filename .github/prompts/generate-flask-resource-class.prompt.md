---
description: "Generate Flask-RESTful resource classes (ListResource and Resource) with authentication, authorization, rate limiting, and proper error handling"
agent: "Flask API Expert"
tools: ["edit", "search", "search/codebase", "read/problems"]
---

# Generate Flask-RESTful Resource Classes

You are an expert Flask-RESTful developer creating production-ready REST API resource classes with proper authentication, authorization, validation, and error handling following wfp-flask-template patterns.

## Task

Generate Flask-RESTful resource file containing:
- **ListResource** - Collection operations (GET list, POST create)
- **Resource** - Item operations (GET, PUT, PATCH, DELETE)
- Authentication and authorization decorators
- Rate limiting
- Comprehensive error handling
- Request validation
- Proper logging

## Input Variables

- `${input:entityName}` - Singular entity name (e.g., "user", "product")
- `${input:entityNamePlural:entityName + 's'}` - Plural form
- `${input:targetDir:src/app}` - Base directory
- `${input:hasService:false}` - Use service layer instead of direct DB access

## File Structure

Generate: `${targetDir}/resources/${entityName}_res.py`

**IMPORTANT**: File contains **TWO** resource classes:
1. `${entityName.capitalize()}ListResource` - For `/v0/${entityNamePlural}`
2. `${entityName.capitalize()}Resource` - For `/v0/${entityNamePlural}/<id>`

## Resource Template

```python
"""${entityName.capitalize()} resource endpoints.

REST API endpoints for ${entityName} management including list,
create, retrieve, update and delete operations.

Endpoints:
    GET    /v0/${entityNamePlural}         - List ${entityNamePlural} (paginated)
    POST   /v0/${entityNamePlural}         - Create ${entityName}
    GET    /v0/${entityNamePlural}/<id>    - Get specific ${entityName}
    PUT    /v0/${entityNamePlural}/<id>    - Replace ${entityName}
    PATCH  /v0/${entityNamePlural}/<id>    - Update ${entityName}
    DELETE /v0/${entityNamePlural}/<id>    - Delete ${entityName}
"""

import logging
from flask import request, g
from flask_restful import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from ..models.${entityName}_model import ${entityName.capitalize()}
from ..schemas.${entityName}_schema import (
    ${entityName.capitalize()}Schema,
    ${entityName.capitalize()}CreateSchema,
    ${entityName.capitalize()}UpdateSchema,
    ${entityName.capitalize()}ReplaceSchema
)
from ..utils.decorators import require_jwt_auth, access_required
from ..utils.responses import success_response, error_response, paginated_response
from ..utils.exceptions import NotFoundError, ConflictError
from ..constants.operations import Operation
from .. import db, limiter

logger = logging.getLogger(__name__)


class ${entityName.capitalize()}ListResource(Resource):
    """Resource for ${entityName} collection operations.

    Handles /v0/${entityNamePlural} endpoint for listing and creating ${entityNamePlural}.
    Implements pagination, filtering, and search capabilities.
    """

    def __init__(self) -> None:
        """Initialize resource with schemas.

        Initializes Marshmallow schemas for validation and serialization.
        """
        self.schema = ${entityName.capitalize()}Schema()
        self.create_schema = ${entityName.capitalize()}CreateSchema()

    @require_jwt_auth
    @access_required(Operation.LIST)
    @limiter.limit("100 per minute")
    def get(self) -> tuple[dict, int]:
        """List all ${entityNamePlural} with pagination and filtering.

        Query Parameters:
            page (int): Page number (default: 1, min: 1)
            per_page (int): Items per page (default: 20, max: 100)
            search (str): Search term for name field
            is_active (bool): Filter by active status
            sort_by (str): Field to sort by (default: created_at)
            sort_order (str): Sort direction - asc or desc (default: desc)

        Returns:
            Tuple of (response dict, HTTP status code).
            Response contains:
                - data: List of ${entityName} objects
                - page: Current page number
                - per_page: Items per page
                - total: Total number of items
                - total_pages: Total number of pages

        Responses:
            200: Success with paginated results
            400: Invalid query parameters
            401: Unauthorized (no valid JWT)
            403: Forbidden (insufficient permissions)
            500: Internal server error

        Examples:
            GET /v0/${entityNamePlural}?page=1&per_page=20
            GET /v0/${entityNamePlural}?search=test&is_active=true
        """
        try:
            # Parse and validate query parameters
            page = max(request.args.get("page", 1, type=int), 1)
            per_page = min(request.args.get("per_page", 20, type=int), 100)
            search = request.args.get("search", type=str)
            is_active = request.args.get("is_active", type=bool)
            sort_by = request.args.get("sort_by", "created_at", type=str)
            sort_order = request.args.get("sort_order", "desc", type=str)

            # Build query
            query = ${entityName.capitalize()}.query

            # Apply filters
            if search:
                query = query.filter(
                    ${entityName.capitalize()}.name.ilike(f"%{search}%")
                )

            if is_active is not None:
                query = query.filter(${entityName.capitalize()}.is_active == is_active)

            # Apply sorting
            sort_column = getattr(${entityName.capitalize()}, sort_by, ${entityName.capitalize()}.created_at)
            if sort_order.lower() == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())

            # Paginate
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

            logger.info(
                f"Listed ${entityNamePlural}",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "user_id": g.get("user_id"),
                    "page": page,
                    "per_page": per_page,
                    "total": pagination.total
                }
            )

            return paginated_response(
                data=self.schema.dump(pagination.items, many=True),
                page=page,
                per_page=per_page,
                total=pagination.total
            )

        except Exception as e:
            logger.error(
                f"Failed to list ${entityNamePlural}",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "error": str(e)
                },
                exc_info=True
            )
            return error_response(
                f"Failed to retrieve ${entityNamePlural}",
                status_code=500,
                errors={"detail": str(e)}
            )

    @require_jwt_auth
    @access_required(Operation.CREATE)
    @limiter.limit("20 per minute")
    def post(self) -> tuple[dict, int]:
        """Create a new ${entityName}.

        Request Body:
            JSON object with ${entityName} data validated by CreateSchema.
            See ${entityName.capitalize()}CreateSchema for required fields.

        Returns:
            Tuple of (response dict, HTTP status code).
            Response contains created ${entityName} data.

        Responses:
            201: ${entityName.capitalize()} created successfully
            400: Invalid request data (validation errors)
            401: Unauthorized (no valid JWT)
            403: Forbidden (insufficient permissions)
            409: Conflict (duplicate resource)
            500: Internal server error

        Examples:
            POST /v0/${entityNamePlural}
            Body: {"name": "Test ${entityName.capitalize()}", "description": "Test description"}
        """
        try:
            # Validate request data
            json_data = request.get_json()
            if not json_data:
                return error_response(
                    "No input data provided",
                    status_code=400
                )

            data = self.create_schema.load(json_data)

            # Create entity
            ${entityName} = ${entityName.capitalize()}(**data)
            db.session.add(${entityName})
            db.session.commit()

            logger.info(
                f"${entityName.capitalize()} created",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "user_id": g.get("user_id"),
                    "${entityName}_id": str(${entityName}.id)
                }
            )

            return success_response(
                data=self.schema.dump(${entityName}),
                message="${entityName.capitalize()} created successfully",
                status_code=201
            )

        except ValidationError as e:
            logger.warning(
                f"${entityName.capitalize()} creation validation failed",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "errors": e.messages
                }
            )
            return error_response(
                "Validation failed",
                status_code=400,
                errors=e.messages
            )
        except IntegrityError as e:
            db.session.rollback()
            logger.warning(
                f"${entityName.capitalize()} creation integrity error",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "error": str(e)
                }
            )
            return error_response(
                "Resource already exists or violates constraints",
                status_code=409,
                errors={"detail": "Duplicate resource or constraint violation"}
            )
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Failed to create ${entityName}",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "error": str(e)
                },
                exc_info=True
            )
            return error_response(
                f"Failed to create ${entityName}",
                status_code=500,
                errors={"detail": str(e)}
            )


class ${entityName.capitalize()}Resource(Resource):
    """Resource for individual ${entityName} operations.

    Handles /v0/${entityNamePlural}/<${entityName}_id> endpoint for operations
    on a specific ${entityName} instance.
    """

    def __init__(self) -> None:
        """Initialize resource with schemas."""
        self.schema = ${entityName.capitalize()}Schema()
        self.update_schema = ${entityName.capitalize()}UpdateSchema()
        self.replace_schema = ${entityName.capitalize()}ReplaceSchema()

    @require_jwt_auth
    @access_required(Operation.READ)
    @limiter.limit("200 per minute")
    def get(self, ${entityName}_id: str) -> tuple[dict, int]:
        """Retrieve a specific ${entityName} by ID.

        Path Parameters:
            ${entityName}_id (str): UUID of the ${entityName}

        Returns:
            Tuple of (response dict, HTTP status code).
            Response contains ${entityName} data.

        Responses:
            200: ${entityName.capitalize()} found and returned
            401: Unauthorized
            403: Forbidden
            404: ${entityName.capitalize()} not found
            500: Internal server error
        """
        try:
            ${entityName} = ${entityName.capitalize()}.query.get(${entityName}_id)

            if not ${entityName}:
                raise NotFoundError(f"${entityName.capitalize()} with id {${entityName}_id} not found")

            return success_response(data=self.schema.dump(${entityName}))

        except NotFoundError as e:
            logger.info(
                f"${entityName.capitalize()} not found",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "${entityName}_id": ${entityName}_id
                }
            )
            return error_response(str(e), status_code=404)
        except Exception as e:
            logger.error(
                f"Failed to retrieve ${entityName}",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "${entityName}_id": ${entityName}_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return error_response(
                f"Failed to retrieve ${entityName}",
                status_code=500,
                errors={"detail": str(e)}
            )

    @require_jwt_auth
    @access_required(Operation.UPDATE)
    @limiter.limit("50 per minute")
    def patch(self, ${entityName}_id: str) -> tuple[dict, int]:
        """Partially update a ${entityName}.

        Path Parameters:
            ${entityName}_id (str): UUID of the ${entityName}

        Request Body:
            JSON object with fields to update (all optional).

        Returns:
            Tuple of (response dict, HTTP status code).

        Responses:
            200: ${entityName.capitalize()} updated successfully
            400: Invalid request data
            401: Unauthorized
            403: Forbidden
            404: ${entityName.capitalize()} not found
            500: Internal server error
        """
        try:
            ${entityName} = ${entityName.capitalize()}.query.get(${entityName}_id)

            if not ${entityName}:
                raise NotFoundError(f"${entityName.capitalize()} with id {${entityName}_id} not found")

            # Validate partial data
            json_data = request.get_json()
            if not json_data:
                return error_response(
                    "No input data provided",
                    status_code=400
                )

            data = self.update_schema.load(json_data, partial=True)

            # Update fields
            for key, value in data.items():
                setattr(${entityName}, key, value)

            db.session.commit()

            logger.info(
                f"${entityName.capitalize()} updated",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "user_id": g.get("user_id"),
                    "${entityName}_id": ${entityName}_id,
                    "updated_fields": list(data.keys())
                }
            )

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
            logger.error(
                f"Failed to update ${entityName}",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "${entityName}_id": ${entityName}_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return error_response(
                f"Failed to update ${entityName}",
                status_code=500,
                errors={"detail": str(e)}
            )

    @require_jwt_auth
    @access_required(Operation.UPDATE)
    @limiter.limit("50 per minute")
    def put(self, ${entityName}_id: str) -> tuple[dict, int]:
        """Completely replace a ${entityName}.

        Path Parameters:
            ${entityName}_id (str): UUID of the ${entityName}

        Request Body:
            JSON object with all required fields.

        Returns:
            Tuple of (response dict, HTTP status code).

        Responses:
            200: ${entityName.capitalize()} replaced successfully
            400: Invalid request data
            401: Unauthorized
            403: Forbidden
            404: ${entityName.capitalize()} not found
            500: Internal server error
        """
        try:
            ${entityName} = ${entityName.capitalize()}.query.get(${entityName}_id)

            if not ${entityName}:
                raise NotFoundError(f"${entityName.capitalize()} with id {${entityName}_id} not found")

            # Validate complete data
            json_data = request.get_json()
            if not json_data:
                return error_response(
                    "No input data provided",
                    status_code=400
                )

            data = self.replace_schema.load(json_data)

            # Replace all fields
            for key, value in data.items():
                setattr(${entityName}, key, value)

            db.session.commit()

            logger.info(
                f"${entityName.capitalize()} replaced",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "user_id": g.get("user_id"),
                    "${entityName}_id": ${entityName}_id
                }
            )

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
            logger.error(
                f"Failed to replace ${entityName}",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "${entityName}_id": ${entityName}_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return error_response(
                f"Failed to replace ${entityName}",
                status_code=500,
                errors={"detail": str(e)}
            )

    @require_jwt_auth
    @access_required(Operation.DELETE)
    @limiter.limit("20 per minute")
    def delete(self, ${entityName}_id: str) -> tuple[dict, int]:
        """Delete a specific ${entityName}.

        Path Parameters:
            ${entityName}_id (str): UUID of the ${entityName}

        Returns:
            Tuple of (response dict, HTTP status code).

        Responses:
            204: ${entityName.capitalize()} deleted successfully
            401: Unauthorized
            403: Forbidden
            404: ${entityName.capitalize()} not found
            500: Internal server error
        """
        try:
            ${entityName} = ${entityName.capitalize()}.query.get(${entityName}_id)

            if not ${entityName}:
                raise NotFoundError(f"${entityName.capitalize()} with id {${entityName}_id} not found")

            db.session.delete(${entityName})
            db.session.commit()

            logger.info(
                f"${entityName.capitalize()} deleted",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "user_id": g.get("user_id"),
                    "${entityName}_id": ${entityName}_id
                }
            )

            return success_response(
                message="${entityName.capitalize()} deleted successfully",
                status_code=204
            )

        except NotFoundError as e:
            return error_response(str(e), status_code=404)
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Failed to delete ${entityName}",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "${entityName}_id": ${entityName}_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return error_response(
                f"Failed to delete ${entityName}",
                status_code=500,
                errors={"detail": str(e)}
            )
```

## Step-by-Step Process

### 1. Analyze Context
- Check existing resources for patterns
- Identify available decorators and utilities
- Verify authentication/authorization setup

### 2. Create ListResource
Implements:
- `get()` - List with pagination, filtering, sorting
- `post()` - Create new entity

### 3. Create Resource
Implements:
- `get(id)` - Retrieve single entity
- `patch(id)` - Partial update
- `put(id)` - Complete replacement
- `delete(id)` - Delete entity

### 4. Add Decorators
Apply in order:
1. `@require_jwt_auth` - JWT validation
2. `@access_required(Operation.X)` - Permission check
3. `@limiter.limit("X per minute")` - Rate limiting

### 5. Implement Error Handling
Handle:
- `ValidationError` - 400 Bad Request
- `NotFoundError` - 404 Not Found
- `IntegrityError` - 409 Conflict
- Generic Exception - 500 Internal Server Error

### 6. Add Logging
Log at appropriate levels:
- `logger.info()` - Successful operations
- `logger.warning()` - Validation failures
- `logger.error()` - Exceptions with exc_info=True

### 7. Register Routes
Update `routes.py`:
```python
from .resources.${entityName}_res import ${entityName.capitalize()}ListResource, ${entityName.capitalize()}Resource

api.add_resource(${entityName.capitalize()}ListResource, f"/{api_version}/${entityNamePlural}")
api.add_resource(${entityName.capitalize()}Resource, f"/{api_version}/${entityNamePlural}/<string:${entityName}_id>")
```

## Quality Checklist

- [ ] Two classes in one file (ListResource and Resource)
- [ ] All methods have comprehensive docstrings (English)
- [ ] Decorators in correct order
- [ ] Rate limiting on all endpoints
- [ ] Request validation with schemas
- [ ] Proper error handling and rollback
- [ ] Structured logging with correlation_id
- [ ] Type hints on methods
- [ ] Pagination on list endpoint
- [ ] Filtering and sorting capabilities
- [ ] No business logic (use services if complex)

## Output

Present generated file path and route registration code.
