---
description: "Generate a SQLAlchemy model with proper mixins, type hints, indexes, and relationships following wfp-flask-template conventions"
agent: "agent"
tools: ["edit", "search", "search/codebase", "read/problems"]
---

# Generate Flask SQLAlchemy Model

You are an expert SQLAlchemy developer creating production-ready database models for Flask applications following wfp-flask-template architecture.

## Task

Generate a complete SQLAlchemy model file with:
- Proper mixins (UUIDMixin, TimestampMixin)
- Type hints with `Mapped[]` annotations
- Appropriate indexes and constraints
- Relationships if needed
- Validation methods
- Complete docstrings

## Input Variables

- `${input:entityName}` - Singular entity name (e.g., "user", "product", "order")
- `${input:tableName:entityName + 's'}` - Database table name (defaults to plural)
- `${input:targetDir:src/app}` - Base directory

## File Structure

Generate: `${targetDir}/models/${entityName}_model.py`

## Model Template

```python
"""${entityName.capitalize()} model.

Database model for ${entityName} entity with UUID primary key
and automatic timestamp management.
"""

from sqlalchemy import String, Boolean, Integer, Text, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..models.base import UUIDMixin, TimestampMixin
from ..models.types import GUID, JSONB
from .. import db


class ${entityName.capitalize()}(UUIDMixin, TimestampMixin, db.Model):
    """${entityName.capitalize()} database model.
    
    Represents ${entityName} entity in the database with automatic
    UUID generation and timestamp tracking.
    
    Attributes:
        id: Unique UUID identifier (from UUIDMixin).
        created_at: Creation timestamp (from TimestampMixin).
        updated_at: Last update timestamp (from TimestampMixin).
        name: ${entityName.capitalize()} name.
        description: Optional description text.
        is_active: Active status flag.
    """
    
    __tablename__ = "${tableName}"
    
    # Required fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="${entityName.capitalize()} display name"
    )
    
    # Optional fields
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description"
    )
    
    # Boolean flags
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Active status flag"
    )
    
    # Indexes and constraints
    __table_args__ = (
        Index("idx_${entityName}_name_active", "name", "is_active"),
        UniqueConstraint("name", name="uq_${entityName}_name"),
    )
    
    def __repr__(self) -> str:
        """String representation for debugging.
        
        Returns:
            Human-readable string with key attributes.
        """
        return f"<${entityName.capitalize()}(id={self.id}, name={self.name})>"
    
    def validate_name(self) -> bool:
        """Validate name field.
        
        Returns:
            True if name is valid, False otherwise.
        """
        return bool(self.name and self.name.strip())
```

## Step-by-Step Process

### 1. Analyze Context
- Search for existing models to understand patterns
- Identify available mixins and custom types
- Check for relationship patterns

### 2. Define Fields
Based on entity type, include appropriate fields:

**Common Field Types:**
- `String(length)` - VARCHAR fields (names, emails)
- `Text` - Long text (descriptions, content)
- `Integer` - Numeric IDs, counters
- `Boolean` - Flags, status indicators
- `GUID()` - UUID foreign keys
- `JSONB()` - JSON data (PostgreSQL optimized)
- `DateTime(timezone=True)` - Timestamps (additional to mixins)

**Type Hints:**
- `Mapped[str]` - Required string
- `Mapped[str | None]` - Optional string
- `Mapped[int]` - Required integer
- `Mapped[bool]` - Boolean with default

### 3. Add Indexes
Create indexes for:
- Fields used in WHERE clauses
- Fields used in ORDER BY
- Composite indexes for common query patterns

```python
__table_args__ = (
    Index("idx_${entityName}_field1_field2", "field1", "field2"),
)
```

### 4. Add Constraints
Include constraints:
- `UniqueConstraint` - Unique fields/combinations
- `CheckConstraint` - Value validations
- `ForeignKeyConstraint` - Complex FK relationships

### 5. Add Relationships
If the model relates to others:

```python
# One-to-Many
items: Mapped[list["Item"]] = relationship(
    "Item",
    back_populates="${entityName}",
    cascade="all, delete-orphan"
)

# Many-to-One
company_id: Mapped[uuid.UUID] = mapped_column(
    GUID(),
    ForeignKey("companies.id"),
    nullable=False
)
company: Mapped["Company"] = relationship("Company", back_populates="${entityNamePlural}")
```

### 6. Add Validation Methods
Instance methods for validation (NOT in model):

```python
def validate_email(self) -> bool:
    """Validate email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, self.email))
```

### 7. Follow Conventions

**Naming:**
- File: `${entityName}_model.py` (snake_case)
- Class: `${entityName.capitalize()}` (PascalCase)
- Table: `${tableName}` (snake_case plural)
- Columns: `snake_case`

**Mixins:**
- Always use `UUIDMixin` for primary key
- Always use `TimestampMixin` for timestamps
- Inherit in order: `UUIDMixin, TimestampMixin, db.Model`

**Type Safety:**
- Use `Mapped[Type]` for all columns
- Use `mapped_column()` for configuration
- Type relationships properly

### 8. Generate Migration
After creating model:

```bash
flask db migrate -m "Add ${entityName.capitalize()} model"
flask db upgrade
```

## Common Patterns

### User/Account Models
```python
email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
```

### Timestamped Content
```python
title: Mapped[str] = mapped_column(String(255), nullable=False)
content: Mapped[str] = mapped_column(Text, nullable=False)
author_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"))
published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

### Hierarchical Data
```python
parent_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("${tableName}.id"))
parent: Mapped["${entityName.capitalize()} | None"] = relationship(
    "${entityName.capitalize()}",
    remote_side=[id],
    back_populates="children"
)
children: Mapped[list["${entityName.capitalize()}"]] = relationship(
    "${entityName.capitalize()}",
    back_populates="parent"
)
```

### Soft Deletes
```python
deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

@property
def is_deleted(self) -> bool:
    """Check if entity is soft-deleted."""
    return self.deleted_at is not None
```

## Quality Checklist

- [ ] Inherits from UUIDMixin, TimestampMixin, db.Model (in that order)
- [ ] All fields have `Mapped[]` type hints
- [ ] All fields use `mapped_column()` with proper config
- [ ] Table name is snake_case plural
- [ ] Appropriate indexes on query fields
- [ ] Unique constraints where needed
- [ ] Relationships properly configured (if applicable)
- [ ] `__repr__` method implemented
- [ ] Docstrings in English for class and complex methods
- [ ] No `to_dict()` method (use Marshmallow schemas)
- [ ] Comments on columns explain their purpose

## Constraints to Follow

**NEVER:**
- Use `Column()` instead of `mapped_column()`
- Omit type hints on fields
- Add `to_dict()` or serialization methods
- Use auto-increment integer IDs (always UUID)
- Forget UUIDMixin or TimestampMixin

**ALWAYS:**
- Use custom types (GUID, JSONB) from `models.types`
- Add indexes on foreign keys
- Add comments on complex fields
- Follow models.instructions.md
- Validate migration before committing

## Migration Verification

After generation:
1. Review migration file in `migrations/versions/`
2. Check for proper indexes and constraints
3. Verify column types are correct
4. Test upgrade and downgrade

## Output

Present the generated model file path and migration command to run.
