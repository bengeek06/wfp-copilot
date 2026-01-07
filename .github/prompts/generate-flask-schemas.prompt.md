---
description: "Generate Marshmallow schemas (Base, Create, Update, Replace) for validation and serialization following wfp-flask-template patterns"
agent: "Flask API Expert"
tools: ["edit", "search", "search/codebase", "read/problems"]
---

# Generate Flask Marshmallow Schemas

You are an expert in Marshmallow schema design, creating comprehensive validation and serialization schemas for Flask REST APIs following wfp-flask-template conventions.

## Task

Generate a complete schema file with:
- **Base schema** for serialization (responses)
- **Create schema** for POST requests
- **Update schema** for PATCH requests (partial)
- **Replace schema** for PUT requests (complete replacement)
- Custom validations
- Field-level and schema-level validators

## Input Variables

- `${input:entityName}` - Singular entity name (e.g., "user", "product")
- `${input:targetDir:src/app}` - Base directory
- `${input:useAutoSchema:true}` - Use SQLAlchemyAutoSchema for base schema

## File Structure

Generate: `${targetDir}/schemas/${entityName}_schema.py`

## Schema Template

```python
"""${entityName.capitalize()} schemas for validation and serialization.

This module defines Marshmallow schemas for ${entityName} data validation,
serialization and deserialization across different API operations.
"""

from marshmallow import Schema, fields, validate, validates, validates_schema, ValidationError, post_load
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from datetime import datetime
from typing import Any
from ..models.${entityName}_model import ${entityName.capitalize()}


class ${entityName.capitalize()}Schema(SQLAlchemyAutoSchema):
    """Base schema for ${entityName} serialization.
    
    Used for serializing ${entityName} data in API responses.
    Includes all model fields and read-only metadata.
    
    This schema should be used for:
    - GET /${entityNamePlural} (list response)
    - GET /${entityNamePlural}/<id> (single response)
    - Response bodies after CREATE/UPDATE/DELETE
    """
    
    class Meta:
        """Schema metadata configuration."""
        model = ${entityName.capitalize()}
        load_instance = True
        include_fk = True
        include_relationships = False
    
    # Override fields to control serialization
    id = fields.UUID(dump_only=True)
    created_at = fields.DateTime(dump_only=True, format="iso")
    updated_at = fields.DateTime(dump_only=True, format="iso")


class ${entityName.capitalize()}CreateSchema(Schema):
    """Schema for creating a new ${entityName}.
    
    Validates POST /${entityNamePlural} request body.
    Only includes fields that can be set during creation.
    All required business fields must be present.
    """
    
    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255),
        error_messages={
            "required": "Name is required",
            "invalid": "Name must be a valid string"
        }
    )
    
    description = fields.Str(
        validate=validate.Length(max=1000),
        allow_none=True,
        load_default=None
    )
    
    is_active = fields.Bool(
        load_default=True,
        error_messages={"invalid": "is_active must be a boolean"}
    )
    
    @validates("name")
    def validate_name(self, value: str) -> None:
        """Validate name field.
        
        Args:
            value: Name value to validate.
            
        Raises:
            ValidationError: If name is invalid.
        """
        if not value.strip():
            raise ValidationError("Name cannot be empty or whitespace only")
        
        if value != value.strip():
            raise ValidationError("Name cannot have leading or trailing whitespace")
    
    @validates_schema
    def validate_schema(self, data: dict[str, Any], **kwargs: Any) -> None:
        """Validate complete schema data.
        
        Args:
            data: Complete data dictionary after field validation.
            
        Raises:
            ValidationError: If schema-level validation fails.
        """
        # Add cross-field validations here
        pass


class ${entityName.capitalize()}UpdateSchema(Schema):
    """Schema for partially updating a ${entityName}.
    
    Validates PATCH /${entityNamePlural}/<id> request body.
    All fields are optional - only provided fields will be updated.
    Allows partial updates without requiring all fields.
    """
    
    name = fields.Str(
        validate=validate.Length(min=1, max=255)
    )
    
    description = fields.Str(
        validate=validate.Length(max=1000),
        allow_none=True
    )
    
    is_active = fields.Bool()
    
    @validates("name")
    def validate_name(self, value: str) -> None:
        """Validate name if provided."""
        if value is not None and not value.strip():
            raise ValidationError("Name cannot be empty or whitespace only")
    
    @validates_schema
    def validate_at_least_one_field(self, data: dict[str, Any], **kwargs: Any) -> None:
        """Ensure at least one field is provided for update.
        
        Args:
            data: Validated data dictionary.
            
        Raises:
            ValidationError: If no fields provided.
        """
        if not data:
            raise ValidationError("At least one field must be provided for update")


class ${entityName.capitalize()}ReplaceSchema(Schema):
    """Schema for completely replacing a ${entityName}.
    
    Validates PUT /${entityNamePlural}/<id> request body.
    All required business fields must be present.
    Replaces the entire entity (except id and timestamps).
    """
    
    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255)
    )
    
    description = fields.Str(
        validate=validate.Length(max=1000),
        allow_none=True
    )
    
    is_active = fields.Bool(required=True)
    
    @validates("name")
    def validate_name(self, value: str) -> None:
        """Validate name field."""
        if not value.strip():
            raise ValidationError("Name cannot be empty or whitespace only")
```

## Step-by-Step Process

### 1. Analyze Model
- Read the corresponding model file
- Identify all fields and their types
- Determine required vs optional fields
- Check for relationships and foreign keys

### 2. Create Base Schema
Use `SQLAlchemyAutoSchema` for automatic mapping:

```python
class ${entityName.capitalize()}Schema(SQLAlchemyAutoSchema):
    """Base serialization schema."""
    
    class Meta:
        model = ${entityName.capitalize()}
        load_instance = True  # Load as model instance
        include_fk = True     # Include foreign keys
        include_relationships = False  # Exclude by default
    
    # Override auto-generated fields
    id = fields.UUID(dump_only=True)
    created_at = fields.DateTime(dump_only=True, format="iso")
    updated_at = fields.DateTime(dump_only=True, format="iso")
```

**Meta Options:**
- `load_instance=True` - Deserialize to model instance
- `include_fk=True` - Include foreign key fields
- `include_relationships=False` - Exclude relationships (avoid N+1)
- `exclude` - Fields to exclude
- `dump_only` - Fields only in serialization

### 3. Create Operation-Specific Schemas

**Create Schema (POST):**
- Only fields that can be set during creation
- Required fields must be marked `required=True`
- Exclude: id, created_at, updated_at (auto-generated)

**Update Schema (PATCH):**
- All business fields optional
- Validates only provided fields
- Can update subset of fields

**Replace Schema (PUT):**
- All business fields required
- Complete replacement of entity
- Exclude: id, created_at, updated_at

### 4. Add Field Validators

**Built-in Validators:**
```python
from marshmallow import validate

# Length constraints
name = fields.Str(validate=validate.Length(min=1, max=255))

# Range constraints
age = fields.Int(validate=validate.Range(min=0, max=150))

# Email validation
email = fields.Email(required=True)

# URL validation
website = fields.Url()

# Choice validation
status = fields.Str(validate=validate.OneOf(["active", "inactive", "pending"]))

# Regex validation
code = fields.Str(validate=validate.Regexp(r'^[A-Z]{3}\d{3}$'))
```

**Custom Field Validators:**
```python
@validates("email")
def validate_email(self, value: str) -> None:
    """Custom email validation.
    
    Args:
        value: Email to validate.
        
    Raises:
        ValidationError: If email is invalid.
    """
    if not value.endswith("@company.com"):
        raise ValidationError("Email must be from company.com domain")
```

### 5. Add Schema-Level Validators

For cross-field validation:

```python
@validates_schema
def validate_dates(self, data: dict[str, Any], **kwargs: Any) -> None:
    """Validate date relationships.
    
    Args:
        data: Complete validated data.
        
    Raises:
        ValidationError: If validation fails.
    """
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    
    if start_date and end_date and start_date > end_date:
        raise ValidationError(
            "start_date must be before end_date",
            field_name="start_date"
        )
```

### 6. Add Error Messages

Customize error messages:

```python
name = fields.Str(
    required=True,
    error_messages={
        "required": "Name is required and cannot be empty",
        "invalid": "Name must be a valid string",
        "null": "Name cannot be null"
    }
)
```

### 7. Handle Nested Data

For relationships:

```python
# Nested schema (include related data)
author = fields.Nested("UserSchema", dump_only=True)

# List of nested (one-to-many)
items = fields.List(fields.Nested("ItemSchema"), dump_only=True)

# Method field (computed)
full_name = fields.Method("get_full_name")

def get_full_name(self, obj: User) -> str:
    """Compute full name."""
    return f"{obj.first_name} {obj.last_name}"
```

## Common Patterns

### Email Field
```python
email = fields.Email(
    required=True,
    validate=validate.Length(max=255),
    error_messages={"invalid": "Invalid email format"}
)

@validates("email")
def validate_email_unique(self, value: str) -> None:
    """Ensure email is unique."""
    # Check database for existing email
    pass
```

### Password Field
```python
password = fields.Str(
    required=True,
    load_only=True,  # Never serialize passwords
    validate=validate.Length(min=8, max=128),
    error_messages={"invalid": "Password must be at least 8 characters"}
)

@validates("password")
def validate_password_strength(self, value: str) -> None:
    """Validate password complexity."""
    if not any(c.isupper() for c in value):
        raise ValidationError("Password must contain at least one uppercase letter")
    if not any(c.isdigit() for c in value):
        raise ValidationError("Password must contain at least one digit")
```

### Enum/Choice Field
```python
status = fields.Str(
    required=True,
    validate=validate.OneOf(["draft", "published", "archived"]),
    load_default="draft"
)
```

### UUID Foreign Key
```python
company_id = fields.UUID(required=True)

@validates("company_id")
def validate_company_exists(self, value: uuid.UUID) -> None:
    """Validate company exists."""
    # Check if company exists in database
    pass
```

### Date/DateTime Fields
```python
from datetime import datetime, timezone

published_at = fields.DateTime(
    format="iso",
    timezone=timezone.utc
)

@validates("published_at")
def validate_not_future(self, value: datetime) -> None:
    """Ensure date is not in the future."""
    if value > datetime.now(timezone.utc):
        raise ValidationError("Published date cannot be in the future")
```

## Quality Checklist

- [ ] Base schema uses SQLAlchemyAutoSchema when appropriate
- [ ] All schemas have descriptive docstrings (English)
- [ ] Create schema has all required fields marked
- [ ] Update schema has all fields optional
- [ ] Replace schema has all business fields required
- [ ] Field validators for business rules
- [ ] Schema-level validators for cross-field rules
- [ ] Appropriate error messages on fields
- [ ] Proper handling of dump_only fields (id, timestamps)
- [ ] load_only for sensitive fields (passwords)
- [ ] Type hints on validator methods
- [ ] No circular imports

## Constraints to Follow

**NEVER:**
- Serialize sensitive data (passwords, tokens)
- Validate in models (always use schemas)
- Allow id, created_at, updated_at in Create/Update/Replace schemas
- Use `required=True` on all fields in Update schema
- Forget to strip whitespace in validators

**ALWAYS:**
- Use dump_only for id and timestamps
- Use load_only for passwords
- Validate cross-field dependencies in @validates_schema
- Provide helpful error messages
- Follow schemas.instructions.md
- Match field types to model field types

## Testing Schemas

Create unit tests for schemas:

```python
def test_create_schema_valid():
    """Test schema with valid data."""
    schema = ${entityName.capitalize()}CreateSchema()
    data = {"name": "Test", "description": "Test desc"}
    result = schema.load(data)
    assert result["name"] == "Test"

def test_create_schema_missing_required():
    """Test schema with missing required field."""
    schema = ${entityName.capitalize()}CreateSchema()
    with pytest.raises(ValidationError):
        schema.load({"description": "Test"})
```

## Output

Present the generated schema file path and remind to create unit tests.
