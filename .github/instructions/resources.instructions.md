---
applyTo: "src/**/resources/**/*.py"
excludeAgent: []
description: "Instructions for creating and maintaining Flask-RESTful resource files in the project."
---

# Resources Instructions

## Purpose
Resources are Flask-RESTful controllers that handle HTTP requests and responses. They are the entry point for API endpoints. Each resource file contains TWO resource classes: one for collection operations (*ListResource) and one for individual item operations (*Resource).

## Naming Conventions

- **File name**: Singular, lowercase with underscores (e.g., `user.py`, `order.py`)
- **List resource class**: `<Entity>ListResource` (e.g., `UserListResource`)
- **Item resource class**: `<Entity>Resource` (e.g., `UserResource`)
- **Methods**: HTTP verbs in lowercase (get, post, put, patch, delete)

## Required Structure

```python
"""User resource endpoints.

This module implements REST API endpoints for user management
including list, create, retrieve, update and delete operations.
"""

from flask import request, g
from flask_restful import Resource
from marshmallow import ValidationError
from ..services.user import UserService
from ..schemas.user import UserSchema, UserCreateSchema, UserUpdateSchema
from ..utils.exceptions import NotFoundError, ConflictError
from ..utils.responses import success_response, error_response, paginated_response
from ..utils.decorators import require_auth, rate_limit
from .. import db


class UserListResource(Resource):
    """Resource for user collection operations.
    
    Handles endpoints for listing users and creating new users.
    Corresponds to /users endpoint.
    """
    
    def __init__(self) -> None:
        """Initialize UserListResource with dependencies."""
        self.user_service = UserService(db.session)
        self.schema = UserSchema()
        self.create_schema = UserCreateSchema()
    
    @rate_limit(max_requests=100, window=60)
    def get(self) -> tuple[dict, int]:
        """Retrieve paginated list of users.
        
        Query Parameters:
            page (int): Page number (default: 1)
            per_page (int): Items per page (default: 20, max: 100)
            is_active (bool): Filter by activation status
        
        Returns:
            Tuple of (response dict, HTTP status code).
            
        Responses:
            200: Success with user list
            400: Invalid query parameters
        """
        # Parse and validate query parameters
        page = request.args.get("page", 1, type=int)
        per_page = min(request.args.get("per_page", 20, type=int), 100)
        is_active = request.args.get("is_active", type=lambda v: v.lower() == "true")
        
        # Validate pagination
        if page < 1 or per_page < 1:
            return error_response(
                "Invalid pagination parameters",
                status_code=400
            )
        
        try:
            users, total = self.user_service.list(
                page=page,
                per_page=per_page,
                is_active=is_active
            )
            
            return paginated_response(
                data=self.schema.dump(users, many=True),
                page=page,
                per_page=per_page,
                total=total
            )
        except Exception as e:
            return error_response(
                "Failed to retrieve users",
                status_code=500,
                errors={"detail": str(e)}
            )
    
    @require_auth
    @rate_limit(max_requests=10, window=60)
    def post(self) -> tuple[dict, int]:
        """Create a new user.
        
        Request Body:
            JSON object with user data (validated by UserCreateSchema)
        
        Returns:
            Tuple of (response dict, HTTP status code).
            
        Responses:
            201: User created successfully
            400: Invalid request data
            409: Email already exists
        """
        try:
            # Validate request data
            data = self.create_schema.load(request.get_json())
            
            # Create user
            user = self.user_service.create(data)
            
            return success_response(
                data=self.schema.dump(user),
                message="User created successfully",
                status_code=201
            )
            
        except ValidationError as e:
            return error_response(
                "Validation failed",
                status_code=400,
                errors=e.messages
            )
        except ConflictError as e:
            return error_response(
                str(e),
                status_code=409
            )
        except Exception as e:
            return error_response(
                "Failed to create user",
                status_code=500,
                errors={"detail": str(e)}
            )


class UserResource(Resource):
    """Resource for individual user operations.
    
    Handles endpoints for retrieving, updating and deleting
    a specific user. Corresponds to /users/<user_id> endpoint.
    """
    
    def __init__(self) -> None:
        """Initialize UserResource with dependencies."""
        self.user_service = UserService(db.session)
        self.schema = UserSchema()
        self.update_schema = UserUpdateSchema()
    
    @rate_limit(max_requests=100, window=60)
    def get(self, user_id: int) -> tuple[dict, int]:
        """Retrieve a specific user by ID.
        
        Path Parameters:
            user_id (int): Unique user identifier
        
        Returns:
            Tuple of (response dict, HTTP status code).
            
        Responses:
            200: User found and returned
            404: User not found
        """
        try:
            user = self.user_service.get_by_id(user_id)
            
            return success_response(
                data=self.schema.dump(user)
            )
            
        except NotFoundError as e:
            return error_response(
                str(e),
                status_code=404
            )
        except Exception as e:
            return error_response(
                "Failed to retrieve user",
                status_code=500,
                errors={"detail": str(e)}
            )
    
    @require_auth
    @rate_limit(max_requests=20, window=60)
    def put(self, user_id: int) -> tuple[dict, int]:
        """Update a user completely.
        
        Path Parameters:
            user_id (int): Unique user identifier
            
        Request Body:
            JSON object with complete user data
        
        Returns:
            Tuple of (response dict, HTTP status code).
            
        Responses:
            200: User updated successfully
            400: Invalid request data
            404: User not found
            409: Email conflict
        """
        try:
            # Validate request data
            data = self.update_schema.load(request.get_json())
            
            # Update user
            user = self.user_service.update(user_id, data)
            
            return success_response(
                data=self.schema.dump(user),
                message="User updated successfully"
            )
            
        except ValidationError as e:
            return error_response(
                "Validation failed",
                status_code=400,
                errors=e.messages
            )
        except NotFoundError as e:
            return error_response(
                str(e),
                status_code=404
            )
        except ConflictError as e:
            return error_response(
                str(e),
                status_code=409
            )
        except Exception as e:
            return error_response(
                "Failed to update user",
                status_code=500,
                errors={"detail": str(e)}
            )
    
    @require_auth
    @rate_limit(max_requests=20, window=60)
    def patch(self, user_id: int) -> tuple[dict, int]:
        """Partially update a user.
        
        Path Parameters:
            user_id (int): Unique user identifier
            
        Request Body:
            JSON object with fields to update (partial)
        
        Returns:
            Tuple of (response dict, HTTP status code).
            
        Responses:
            200: User updated successfully
            400: Invalid request data
            404: User not found
        """
        try:
            # Validate partial data
            data = self.update_schema.load(request.get_json(), partial=True)
            
            # Update user
            user = self.user_service.update(user_id, data)
            
            return success_response(
                data=self.schema.dump(user),
                message="User updated successfully"
            )
            
        except ValidationError as e:
            return error_response(
                "Validation failed",
                status_code=400,
                errors=e.messages
            )
        except NotFoundError as e:
            return error_response(
                str(e),
                status_code=404
            )
        except Exception as e:
            return error_response(
                "Failed to update user",
                status_code=500,
                errors={"detail": str(e)}
            )
    
    @require_auth
    @rate_limit(max_requests=10, window=60)
    def delete(self, user_id: int) -> tuple[dict, int]:
        """Delete a user.
        
        Path Parameters:
            user_id (int): Unique user identifier
        
        Returns:
            Tuple of (empty dict, HTTP status code 204).
            
        Responses:
            204: User deleted successfully
            404: User not found
        """
        try:
            self.user_service.delete(user_id)
            
            return {}, 204
            
        except NotFoundError as e:
            return error_response(
                str(e),
                status_code=404
            )
        except Exception as e:
            return error_response(
                "Failed to delete user",
                status_code=500,
                errors={"detail": str(e)}
            )
```

## Core Principles

### 1. Two Classes Per File
Always have both list and item resources:
```python
# user.py
class UserListResource(Resource):  # For /users
    def get(self): ...   # List users
    def post(self): ...  # Create user

class UserResource(Resource):  # For /users/<id>
    def get(self, user_id: int): ...     # Get one user
    def put(self, user_id: int): ...     # Update user
    def patch(self, user_id: int): ...   # Partial update
    def delete(self, user_id: int): ...  # Delete user
```

### 2. Dependency Injection in __init__
Initialize services and schemas in constructor:
```python
def __init__(self) -> None:
    """Initialize with dependencies."""
    self.user_service = UserService(db.session)
    self.schema = UserSchema()
    self.create_schema = UserCreateSchema()
```

### 3. Consistent Response Format
Always use helper functions for responses:
```python
# Success
return success_response(data=result, message="Success")

# Error
return error_response("Error message", status_code=400, errors={})

# Paginated
return paginated_response(data=items, page=1, per_page=20, total=100)
```

### 4. Complete Type Hints
All methods must specify return types:
```python
def get(self, user_id: int) -> tuple[dict, int]:
def post(self) -> tuple[dict, int]:
```

### 5. HTTP Status Codes
Use correct status codes:
- **200**: Success (GET, PUT, PATCH)
- **201**: Created (POST)
- **204**: No Content (DELETE)
- **400**: Bad Request (validation errors)
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **409**: Conflict (unique constraint violation)
- **500**: Internal Server Error

## Request Handling

### Query Parameters
```python
def get(self) -> tuple[dict, int]:
    """Handle query parameters properly."""
    # With defaults and type conversion
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    # Boolean parameters
    is_active = request.args.get(
        "is_active",
        type=lambda v: v.lower() == "true"
    )
    
    # List parameters
    tags = request.args.getlist("tags")
    
    # Validate
    if page < 1:
        return error_response("Invalid page number", status_code=400)
```

### Request Body
```python
def post(self) -> tuple[dict, int]:
    """Handle request body with validation."""
    try:
        # Get JSON body
        json_data = request.get_json()
        
        # Validate with schema
        data = self.create_schema.load(json_data)
        
        # Process data
        result = self.service.create(data)
        
        return success_response(data=self.schema.dump(result), status_code=201)
    
    except ValidationError as e:
        return error_response(
            "Validation failed",
            status_code=400,
            errors=e.messages
        )
```

### Path Parameters
```python
def get(self, user_id: int) -> tuple[dict, int]:
    """Path parameter is automatically typed."""
    # user_id is already an int from route definition
    user = self.service.get_by_id(user_id)
    return success_response(data=self.schema.dump(user))
```

## Error Handling Pattern

### Comprehensive Try-Except
Every method should handle expected exceptions:
```python
def post(self) -> tuple[dict, int]:
    """Standard error handling pattern."""
    try:
        data = self.create_schema.load(request.get_json())
        result = self.service.create(data)
        return success_response(data=self.schema.dump(result), status_code=201)
        
    except ValidationError as e:
        # Schema validation errors
        return error_response(
            "Validation failed",
            status_code=400,
            errors=e.messages
        )
    except ConflictError as e:
        # Business logic conflicts (unique constraints, etc.)
        return error_response(str(e), status_code=409)
    except Exception as e:
        # Unexpected errors - log and return generic message
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return error_response(
            "An unexpected error occurred",
            status_code=500
        )
```

## Decorators

### Authentication
```python
@require_auth
def post(self) -> tuple[dict, int]:
    """Protected endpoint requiring authentication."""
    pass
```

### Authorization
```python
@require_permission("admin")
def delete(self, user_id: int) -> tuple[dict, int]:
    """Admin-only endpoint."""
    pass
```

### Rate Limiting
```python
@rate_limit(max_requests=10, window=60)
def post(self) -> tuple[dict, int]:
    """Limited to 10 requests per 60 seconds."""
    pass
```

### Idempotency
```python
@idempotent
def post(self) -> tuple[dict, int]:
    """Idempotent operation using Idempotency-Key header."""
    pass
```

## Logging

### Request Logging
```python
import logging
from flask import g

logger = logging.getLogger(__name__)


def post(self) -> tuple[dict, int]:
    """Log important operations."""
    logger.info(
        "Creating user",
        extra={
            "correlation_id": g.get("correlation_id"),
            "endpoint": "POST /users"
        }
    )
    
    try:
        result = self.service.create(data)
        
        logger.info(
            "User created",
            extra={
                "correlation_id": g.get("correlation_id"),
                "user_id": result.id
            }
        )
        
        return success_response(data=self.schema.dump(result), status_code=201)
    except Exception as e:
        logger.error(
            "User creation failed",
            extra={
                "correlation_id": g.get("correlation_id"),
                "error": str(e)
            }
        )
        raise
```

## OpenAPI Documentation

### Inline Documentation
Resources should be self-documenting through docstrings:
```python
def get(self, user_id: int) -> tuple[dict, int]:
    """Retrieve a specific user by ID.
    
    Path Parameters:
        user_id (int): Unique user identifier
    
    Returns:
        Tuple of (response dict, HTTP status code).
        
    Responses:
        200: User found and returned
        404: User not found
        500: Internal server error
        
    Example Response:
        {
            "data": {
                "id": 1,
                "email": "user@example.com",
                "username": "johndoe"
            }
        }
    """
```

## What NOT to Do

- ❌ Business logic in resources (use services)
- ❌ Direct database queries (use services)
- ❌ Mixing list and item operations in same class
- ❌ Missing type hints
- ❌ Incomplete error handling
- ❌ French docstrings or comments
- ❌ Returning raw exceptions to client
- ❌ Missing validation before service calls
- ❌ Inconsistent response formats
- ❌ Missing rate limiting on public endpoints
- ❌ Exposing internal error details in production

## Testing Resources

Create integration tests in `tests/integration/resources/test_<resource_name>.py`:

```python
"""Integration tests for user resources."""

import pytest
from flask import Flask
from flask.testing import FlaskClient


class TestUserListResource:
    """Tests for UserListResource."""
    
    def test_get_users_success(self, client: FlaskClient):
        """Test retrieving user list.
        
        Given: Users exist in database
        When: GET /users is called
        Then: Returns 200 with user list
        """
        response = client.get("/users")
        
        assert response.status_code == 200
        assert "data" in response.json
        assert isinstance(response.json["data"], list)
    
    def test_get_users_pagination(self, client: FlaskClient):
        """Test user list pagination.
        
        Given: Query parameters for pagination
        When: GET /users?page=2&per_page=5 is called
        Then: Returns paginated results
        """
        response = client.get("/users?page=2&per_page=5")
        
        assert response.status_code == 200
        assert response.json["page"] == 2
        assert response.json["per_page"] == 5
    
    def test_create_user_success(self, client: FlaskClient, auth_headers):
        """Test creating a new user.
        
        Given: Valid user data and authentication
        When: POST /users is called
        Then: Returns 201 with created user
        """
        data = {
            "email": "new@example.com",
            "username": "newuser",
            "password": "SecurePass123!"
        }
        
        response = client.post("/users", json=data, headers=auth_headers)
        
        assert response.status_code == 201
        assert response.json["data"]["email"] == data["email"]
    
    def test_create_user_validation_error(self, client: FlaskClient, auth_headers):
        """Test creating user with invalid data.
        
        Given: Invalid user data
        When: POST /users is called
        Then: Returns 400 with validation errors
        """
        data = {"email": "invalid-email"}
        
        response = client.post("/users", json=data, headers=auth_headers)
        
        assert response.status_code == 400
        assert "errors" in response.json
    
    def test_create_user_unauthorized(self, client: FlaskClient):
        """Test creating user without authentication.
        
        Given: No authentication token
        When: POST /users is called
        Then: Returns 401 unauthorized
        """
        data = {"email": "test@example.com", "username": "test"}
        
        response = client.post("/users", json=data)
        
        assert response.status_code == 401


class TestUserResource:
    """Tests for UserResource."""
    
    def test_get_user_success(self, client: FlaskClient):
        """Test retrieving existing user."""
        response = client.get("/users/1")
        
        assert response.status_code == 200
        assert response.json["data"]["id"] == 1
    
    def test_get_user_not_found(self, client: FlaskClient):
        """Test retrieving non-existent user."""
        response = client.get("/users/99999")
        
        assert response.status_code == 404
    
    def test_update_user_success(self, client: FlaskClient, auth_headers):
        """Test updating a user."""
        data = {"username": "updated_name"}
        
        response = client.put("/users/1", json=data, headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json["data"]["username"] == "updated_name"
    
    def test_delete_user_success(self, client: FlaskClient, auth_headers):
        """Test deleting a user."""
        response = client.delete("/users/1", headers=auth_headers)
        
        assert response.status_code == 204
```

## Response Helpers

Create in `utils/responses.py`:

```python
"""Response helper functions for consistent API responses."""

from typing import Any, Optional


def success_response(
    data: Any,
    message: Optional[str] = None,
    status_code: int = 200
) -> tuple[dict, int]:
    """Create a success response.
    
    Args:
        data: Response data.
        message: Optional success message.
        status_code: HTTP status code.
        
    Returns:
        Tuple of (response dict, status code).
    """
    response = {"data": data}
    if message:
        response["message"] = message
    
    return response, status_code


def error_response(
    message: str,
    status_code: int = 400,
    errors: Optional[dict] = None
) -> tuple[dict, int]:
    """Create an error response.
    
    Args:
        message: Error message.
        status_code: HTTP status code.
        errors: Optional detailed errors.
        
    Returns:
        Tuple of (response dict, status code).
    """
    response = {"message": message}
    if errors:
        response["errors"] = errors
    
    return response, status_code


def paginated_response(
    data: list,
    page: int,
    per_page: int,
    total: int
) -> tuple[dict, int]:
    """Create a paginated response.
    
    Args:
        data: List of items.
        page: Current page number.
        per_page: Items per page.
        total: Total number of items.
        
    Returns:
        Tuple of (response dict, 200).
    """
    return {
        "data": data,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page
    }, 200
```