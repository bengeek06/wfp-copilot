---
applyTo: "src/**/schemas/**/*.py"
excludeAgent: []
description: "Instructions for creating and maintaining Marshmallow schema files in the project."
---

# Schemas Instructions

## Purpose
Marshmallow schemas handle data validation, serialization and deserialization. They define the structure of request/response data and enforce validation rules. Each schema file contains ALL schemas related to ONE entity (e.g., UserSchema, UserCreateSchema, UserUpdateSchema).

## Naming Conventions

- **File name**: Singular, lowercase with underscores (e.g., `user.py`, `order.py`)
- **Base schema**: `<Entity>Schema` (e.g., `UserSchema`)
- **Create schema**: `<Entity>CreateSchema` (e.g., `UserCreateSchema`)
- **Update schema**: `<Entity>UpdateSchema` (e.g., `UserUpdateSchema`)
- **Query schema**: `<Entity>QuerySchema` for query parameters (optional)

## Required Structure

```python
"""User schemas for validation and serialization.

This module defines Marshmallow schemas for user data validation,
serialization and deserialization across different operations.
"""

from marshmallow import Schema, fields, validate, validates, validates_schema, ValidationError, post_load
from datetime import datetime
from typing import Any


class UserSchema(Schema):
    """Base schema for user serialization.

    Used for serializing user data in responses. Includes all
    user fields that should be exposed in the API.

    Attributes:
        id: Unique user identifier.
        email: User email address.
        username: User display name.
        is_active: Account activation status.
        created_at: Account creation timestamp.
        updated_at: Last update timestamp.
    """

    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    is_active = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    class Meta:
        """Schema configuration."""
        ordered = True
        strict = True


class UserCreateSchema(Schema):
    """Schema for user creation.

    Validates data for creating new users. Includes required
    fields and specific validation rules for user registration.

    Attributes:
        email: User email (required, unique).
        username: User display name (required).
        password: User password (required, strong validation).
        first_name: User's first name (optional).
        last_name: User's last name (optional).
    """

    email = fields.Email(
        required=True,
        validate=validate.Length(max=255),
        error_messages={
            "required": "Email address is required",
            "invalid": "Invalid email address format"
        }
    )

    username = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=50),
            validate.Regexp(
                r'^[a-zA-Z0-9_]+$',
                error="Username can only contain letters, numbers and underscores"
            )
        ]
    )

    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=8, max=128),
        error_messages={"required": "Password is required"}
    )

    first_name = fields.Str(validate=validate.Length(max=100))
    last_name = fields.Str(validate=validate.Length(max=100))

    @validates("password")
    def validate_password_strength(self, value: str) -> None:
        """Validate password strength.

        Args:
            value: Password to validate.

        Raises:
            ValidationError: If password doesn't meet requirements.
        """
        if not any(char.isdigit() for char in value):
            raise ValidationError("Password must contain at least one digit")

        if not any(char.isupper() for char in value):
            raise ValidationError("Password must contain at least one uppercase letter")

        if not any(char.islower() for char in value):
            raise ValidationError("Password must contain at least one lowercase letter")

        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in value):
            raise ValidationError("Password must contain at least one special character")

    @validates("email")
    def validate_email_domain(self, value: str) -> None:
        """Validate email domain if needed.

        Args:
            value: Email to validate.

        Raises:
            ValidationError: If email domain is blacklisted.
        """
        blacklisted_domains = ["tempmail.com", "throwaway.email"]
        domain = value.split("@")[1].lower()

        if domain in blacklisted_domains:
            raise ValidationError(f"Email domain {domain} is not allowed")

    @validates_schema
    def validate_schema(self, data: dict, **kwargs) -> None:
        """Validate entire schema for cross-field validation.

        Args:
            data: Dictionary of validated data.

        Raises:
            ValidationError: If cross-field validation fails.
        """
        # Example: username cannot be same as email local part
        if "email" in data and "username" in data:
            email_local = data["email"].split("@")[0]
            if data["username"].lower() == email_local.lower():
                raise ValidationError(
                    "Username cannot be the same as email address",
                    field_name="username"
                )

    class Meta:
        """Schema configuration."""
        ordered = True


class UserUpdateSchema(Schema):
    """Schema for user updates.

    Validates data for updating existing users. All fields are
    optional to support partial updates (PATCH).

    Attributes:
        email: New email address (optional).
        username: New username (optional).
        first_name: Updated first name (optional).
        last_name: Updated last name (optional).
        is_active: Account status (optional, admin only).
    """

    email = fields.Email(validate=validate.Length(max=255))

    username = fields.Str(
        validate=[
            validate.Length(min=3, max=50),
            validate.Regexp(r'^[a-zA-Z0-9_]+$')
        ]
    )

    first_name = fields.Str(validate=validate.Length(max=100))
    last_name = fields.Str(validate=validate.Length(max=100))
    is_active = fields.Bool()

    @validates("email")
    def validate_email_domain(self, value: str) -> None:
        """Validate email domain."""
        blacklisted_domains = ["tempmail.com", "throwaway.email"]
        domain = value.split("@")[1].lower()

        if domain in blacklisted_domains:
            raise ValidationError(f"Email domain {domain} is not allowed")

    class Meta:
        """Schema configuration."""
        ordered = True


class UserQuerySchema(Schema):
    """Schema for query parameter validation.

    Validates query parameters for list endpoints.
    Used for filtering, sorting and pagination.

    Attributes:
        page: Page number (min: 1).
        per_page: Items per page (min: 1, max: 100).
        is_active: Filter by activation status.
        sort_by: Field to sort by.
        order: Sort order (asc/desc).
    """

    page = fields.Int(
        missing=1,
        validate=validate.Range(min=1),
        error_messages={"invalid": "Page must be a positive integer"}
    )

    per_page = fields.Int(
        missing=20,
        validate=validate.Range(min=1, max=100),
        error_messages={"invalid": "Items per page must be between 1 and 100"}
    )

    is_active = fields.Bool()

    sort_by = fields.Str(
        validate=validate.OneOf(
            ["email", "username", "created_at"],
            error="Invalid sort field"
        )
    )

    order = fields.Str(
        validate=validate.OneOf(["asc", "desc"]),
        missing="asc"
    )

    class Meta:
        """Schema configuration."""
        ordered = True
        unknown = "EXCLUDE"  # Ignore unknown query params
```

## Core Principles

### 1. Multiple Schemas Per File
Group all schemas for one entity in the same file:
```python
# user.py contains:
# - UserSchema (base serialization)
# - UserCreateSchema (creation validation)
# - UserUpdateSchema (update validation)
# - UserQuerySchema (query parameters)
# - Any other user-related schemas
```

### 2. dump_only vs load_only
```python
# dump_only: only in responses, never accepted in requests
id = fields.Int(dump_only=True)
created_at = fields.DateTime(dump_only=True)

# load_only: only in requests, never in responses
password = fields.Str(load_only=True)
```

### 3. Field Validation
Always add proper validation:
```python
# Length constraints
username = fields.Str(validate=validate.Length(min=3, max=50))

# Range for numbers
age = fields.Int(validate=validate.Range(min=0, max=150))

# Regex pattern
phone = fields.Str(validate=validate.Regexp(r'^\+?1?\d{9,15}$'))

# Predefined choices
status = fields.Str(validate=validate.OneOf(["active", "inactive", "pending"]))

# Multiple validators
email = fields.Email(
    required=True,
    validate=[
        validate.Length(max=255),
        validate.Email()
    ]
)
```

### 4. Custom Error Messages
Provide clear, user-friendly error messages:
```python
email = fields.Email(
    required=True,
    error_messages={
        "required": "Email address is required",
        "invalid": "Please provide a valid email address",
        "null": "Email cannot be null"
    }
)
```

### 5. Type Hints
Add type hints for validator methods:
```python
@validates("email")
def validate_email(self, value: str) -> None:
    """Validate email."""
    pass

@validates_schema
def validate_schema(self, data: dict, **kwargs) -> None:
    """Validate entire schema."""
    pass
```

## Field Types Reference

### Common Fields
```python
# String
name = fields.Str(required=True, validate=validate.Length(max=100))

# Integer
age = fields.Int(validate=validate.Range(min=0))

# Float
price = fields.Float(validate=validate.Range(min=0.0))

# Boolean
is_active = fields.Bool()

# Email
email = fields.Email(required=True)

# URL
website = fields.Url()

# UUID
id = fields.UUID()

# Date
birth_date = fields.Date()

# DateTime
created_at = fields.DateTime()

# Decimal (for money)
amount = fields.Decimal(as_string=True, places=2)

# Enum
from enum import Enum
class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

status = fields.Enum(Status)
```

### Nested Fields
```python
# Single nested object
address = fields.Nested(AddressSchema)

# List of nested objects
orders = fields.List(fields.Nested(OrderSchema))

# Nested with only some fields
user = fields.Nested(UserSchema, only=["id", "username"])

# Nested excluding some fields
user = fields.Nested(UserSchema, exclude=["password_hash"])
```

### List and Dict
```python
# List of strings
tags = fields.List(fields.Str())

# List of integers
scores = fields.List(fields.Int(validate=validate.Range(min=0, max=100)))

# Dictionary
metadata = fields.Dict(keys=fields.Str(), values=fields.Str())
```

## Validation Methods

### Field-Level Validation
```python
@validates("username")
def validate_username(self, value: str) -> None:
    """Validate username uniqueness or format.

    Args:
        value: Username to validate.

    Raises:
        ValidationError: If validation fails.
    """
    if len(value) < 3:
        raise ValidationError("Username must be at least 3 characters")

    if not value[0].isalpha():
        raise ValidationError("Username must start with a letter")
```

### Schema-Level Validation
```python
@validates_schema
def validate_dates(self, data: dict, **kwargs) -> None:
    """Validate date relationships.

    Args:
        data: Dictionary of validated fields.

    Raises:
        ValidationError: If validation fails.
    """
    if "start_date" in data and "end_date" in data:
        if data["start_date"] > data["end_date"]:
            raise ValidationError(
                "End date must be after start date",
                field_name="end_date"
            )
```

### Conditional Validation
```python
@validates_schema
def validate_conditional(self, data: dict, **kwargs) -> None:
    """Validate fields conditionally.

    Args:
        data: Dictionary of validated fields.

    Raises:
        ValidationError: If validation fails.
    """
    # Require field B if field A is present
    if data.get("requires_approval") and not data.get("approver_id"):
        raise ValidationError(
            "Approver ID is required when approval is needed",
            field_name="approver_id"
        )
```

## Data Transformation

### Pre-Processing (pre_load)
```python
from marshmallow import pre_load

@pre_load
def process_input(self, data: dict, **kwargs) -> dict:
    """Transform data before validation.

    Args:
        data: Raw input data.

    Returns:
        Transformed data.
    """
    # Strip whitespace from all string fields
    for key, value in data.items():
        if isinstance(value, str):
            data[key] = value.strip()

    # Convert email to lowercase
    if "email" in data:
        data["email"] = data["email"].lower()

    return data
```

### Post-Processing (post_load)
```python
@post_load
def make_object(self, data: dict, **kwargs) -> dict:
    """Transform data after validation.

    Args:
        data: Validated data.

    Returns:
        Transformed data ready for use.
    """
    # Hash password before returning
    if "password" in data:
        from werkzeug.security import generate_password_hash
        data["password_hash"] = generate_password_hash(data.pop("password"))

    return data
```

## Complex Validation Examples

### Password Strength
```python
@validates("password")
def validate_password(self, value: str) -> None:
    """Validate password meets security requirements.

    Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character

    Args:
        value: Password to validate.

    Raises:
        ValidationError: If password doesn't meet requirements.
    """
    errors = []

    if len(value) < 8:
        errors.append("Password must be at least 8 characters long")

    if not any(c.isupper() for c in value):
        errors.append("Password must contain at least one uppercase letter")

    if not any(c.islower() for c in value):
        errors.append("Password must contain at least one lowercase letter")

    if not any(c.isdigit() for c in value):
        errors.append("Password must contain at least one digit")

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in value):
        errors.append("Password must contain at least one special character")

    if errors:
        raise ValidationError(errors)
```

### Phone Number Validation
```python
import re

@validates("phone")
def validate_phone(self, value: str) -> None:
    """Validate international phone number format.

    Args:
        value: Phone number to validate.

    Raises:
        ValidationError: If phone format is invalid.
    """
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', value)

    # Check international format
    if not re.match(r'^\+?1?\d{9,15}$', cleaned):
        raise ValidationError(
            "Phone number must be in international format (E.164)"
        )
```

### Business Hours Validation
```python
from datetime import time

@validates_schema
def validate_business_hours(self, data: dict, **kwargs) -> None:
    """Validate time is within business hours.

    Args:
        data: Dictionary with time fields.

    Raises:
        ValidationError: If outside business hours.
    """
    if "appointment_time" in data:
        appt_time = data["appointment_time"].time()
        start = time(9, 0)  # 9 AM
        end = time(17, 0)   # 5 PM

        if not (start <= appt_time <= end):
            raise ValidationError(
                "Appointments must be between 9 AM and 5 PM",
                field_name="appointment_time"
            )
```

## Pagination and Filtering Schemas

### Standard Pagination Schema
```python
class PaginationSchema(Schema):
    """Reusable pagination schema.

    Can be extended or used directly for pagination parameters.
    """

    page = fields.Int(
        missing=1,
        validate=validate.Range(min=1),
        error_messages={"invalid": "Page must be positive"}
    )

    per_page = fields.Int(
        missing=20,
        validate=validate.Range(min=1, max=100),
        error_messages={"invalid": "Per page must be between 1 and 100"}
    )

    class Meta:
        ordered = True
        unknown = "EXCLUDE"
```

### Filtering Schema
```python
class UserFilterSchema(PaginationSchema):
    """Schema for user filtering and pagination.

    Extends pagination with filter-specific fields.
    """

    is_active = fields.Bool()
    role = fields.Str(validate=validate.OneOf(["admin", "user", "guest"]))
    created_after = fields.DateTime()
    created_before = fields.DateTime()
    search = fields.Str(validate=validate.Length(max=100))

    @validates_schema
    def validate_date_range(self, data: dict, **kwargs) -> None:
        """Validate created date range."""
        if "created_after" in data and "created_before" in data:
            if data["created_after"] > data["created_before"]:
                raise ValidationError(
                    "created_after must be before created_before"
                )
```

## What NOT to Do

- ❌ Business logic in schemas (use services)
- ❌ Database queries in validators
- ❌ Missing type hints on validator methods
- ❌ Generic error messages
- ❌ Missing validation on user inputs
- ❌ French docstrings or error messages
- ❌ Exposing sensitive fields (passwords, tokens)
- ❌ Missing dump_only on system fields (id, created_at)
- ❌ Inconsistent field names with model
- ❌ Overly permissive validation

## Testing Schemas

Create tests in `tests/unit/schemas/test_<schema_name>.py`:

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

    def test_valid_data(self):
        """Test schema with valid data.

        Given: Valid user creation data
        When: Schema loads data
        Then: Data is validated successfully
        """
        schema = UserCreateSchema()
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }

        result = schema.load(data)

        assert result["email"] == "test@example.com"
        assert result["username"] == "testuser"

    def test_missing_required_field(self):
        """Test schema with missing required field.

        Given: Data missing required email
        When: Schema loads data
        Then: ValidationError is raised
        """
        schema = UserCreateSchema()
        data = {"username": "testuser", "password": "SecurePass123!"}

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "email" in exc.value.messages

    def test_invalid_email_format(self):
        """Test schema with invalid email.

        Given: Invalid email format
        When: Schema loads data
        Then: ValidationError is raised
        """
        schema = UserCreateSchema()
        data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "SecurePass123!"
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "email" in exc.value.messages

    def test_weak_password(self):
        """Test password strength validation.

        Given: Weak password
        When: Schema loads data
        Then: ValidationError is raised
        """
        schema = UserCreateSchema()
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak"
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "password" in exc.value.messages

    def test_short_username(self):
        """Test username length validation.

        Given: Username too short
        When: Schema loads data
        Then: ValidationError is raised
        """
        schema = UserCreateSchema()
        data = {
            "email": "test@example.com",
            "username": "ab",
            "password": "SecurePass123!"
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "username" in exc.value.messages

    def test_blacklisted_email_domain(self):
        """Test blacklisted email domain.

        Given: Email from blacklisted domain
        When: Schema loads data
        Then: ValidationError is raised
        """
        schema = UserCreateSchema()
        data = {
            "email": "test@tempmail.com",
            "username": "testuser",
            "password": "SecurePass123!"
        }

        with pytest.raises(ValidationError) as exc:
            schema.load(data)

        assert "email" in exc.value.messages


class TestUserUpdateSchema:
    """Tests for UserUpdateSchema."""

    def test_partial_update(self):
        """Test partial update with some fields.

        Given: Only username to update
        When: Schema loads data with partial=True
        Then: Data is validated successfully
        """
        schema = UserUpdateSchema()
        data = {"username": "newusername"}

        result = schema.load(data, partial=True)

        assert result["username"] == "newusername"
        assert "email" not in result

    def test_empty_update(self):
        """Test update with no fields.

        Given: Empty update data
        When: Schema loads data
        Then: Returns empty dict (valid)
        """
        schema = UserUpdateSchema()
        data = {}

        result = schema.load(data, partial=True)

        assert result == {}
```

## Complete Example

See the main structure at the top of this document for a complete, production-ready schema implementation with all validation patterns.
