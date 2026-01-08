---
applyTo: "src/**/models/**/*.py"
excludeAgent: []
description: "Instructions for creating and maintaining SQLAlchemy model files in the project."
---

# Models Instructions

## Purpose
SQLAlchemy models represent database tables and define the data structure. Each model file should contain exactly ONE model class.

## Naming Conventions

- **File name**: Singular, lowercase with underscores (e.g., `user.py`, `order_item.py`)
- **Class name**: Singular, PascalCase (e.g., `User`, `OrderItem`)
- **Table name**: Plural, lowercase with underscores (e.g., `users`, `order_items`)
- **Column names**: Lowercase with underscores (e.g., `created_at`, `user_id`)

## Required Structure

```python
"""User model definition.

This module defines the User model for storing user account information
in the database with proper relationships and constraints.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .. import db


class User(db.Model):
    """User account model.

    Represents a user account in the system with authentication
    and profile information.

    Attributes:
        id: Unique identifier (primary key).
        email: User email address (unique, indexed).
        username: User display name.
        is_active: Account activation status.
        created_at: Timestamp of account creation.
        updated_at: Timestamp of last update.
    """

    __tablename__ = "users"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Required Fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    username: Mapped[str] = mapped_column(String(100), nullable=False)

    # Optional Fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    orders: Mapped[list["Order"]] = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of User.

        Returns:
            Human-readable string with key attributes.
        """
        return f"<User(id={self.id}, email='{self.email}')>"
```

## Mandatory Elements

### 1. Module Docstring
Every model file MUST start with a module docstring in English explaining:
- What the model represents
- Its main purpose
- Key relationships if any

### 2. Imports
Always import in this order:
1. Standard library (datetime, typing, etc.)
2. SQLAlchemy types and utilities
3. Relative imports from parent modules

### 3. Type Hints with Mapped
Use SQLAlchemy 2.0+ style with `Mapped` type hints:
```python
# Correct ✓
email: Mapped[str] = mapped_column(String(255))
count: Mapped[int] = mapped_column(default=0)
is_active: Mapped[bool] = mapped_column(Boolean, default=True)

# Incorrect ✗
email = db.Column(db.String(255))  # Old style
```

### 4. Always Include Timestamps
Every model MUST have:
```python
created_at: Mapped[datetime] = mapped_column(
    DateTime,
    default=datetime.utcnow,
    nullable=False
)
updated_at: Mapped[datetime] = mapped_column(
    DateTime,
    default=datetime.utcnow,
    onupdate=datetime.utcnow,
    nullable=False
)
```

### 5. Class Docstring
Comprehensive docstring following Google style:
- Brief description
- Detailed explanation if needed
- List all important attributes
- Always in English

### 6. __repr__ Method
Always implement for debugging:
```python
def __repr__(self) -> str:
    """String representation of ModelName.

    Returns:
        Human-readable string with key attributes.
    """
    return f"<ModelName(id={self.id}, key_field='{self.key_field}')>"
```

## Column Definitions

### Primary Keys
```python
id: Mapped[int] = mapped_column(primary_key=True)
```

### Unique Constraints
```python
email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
```

### Foreign Keys
```python
user_id: Mapped[int] = mapped_column(
    ForeignKey("users.id", ondelete="CASCADE"),
    nullable=False,
    index=True
)
```

### Optional Fields
```python
# Use Optional for nullable columns
phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
```

### Enums
```python
from enum import Enum as PyEnum

class StatusEnum(PyEnum):
    """Order status enumeration."""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

status: Mapped[StatusEnum] = mapped_column(
    Enum(StatusEnum),
    default=StatusEnum.PENDING,
    nullable=False
)
```

## Relationships

### One-to-Many
```python
# In parent (User)
orders: Mapped[list["Order"]] = relationship(
    "Order",
    back_populates="user",
    cascade="all, delete-orphan",
    lazy="select"
)

# In child (Order)
user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
user: Mapped["User"] = relationship("User", back_populates="orders")
```

### Many-to-Many
```python
# Association table
user_roles = Table(
    "user_roles",
    db.Model.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True)
)

# In model
roles: Mapped[list["Role"]] = relationship(
    "Role",
    secondary=user_roles,
    back_populates="users"
)
```

## Indexes and Constraints

### Single Column Index
```python
email: Mapped[str] = mapped_column(String(255), index=True)
```

### Composite Index
```python
__table_args__ = (
    Index("idx_user_email_active", "email", "is_active"),
    UniqueConstraint("email", "username", name="uq_email_username"),
)
```

## Validation Methods

Add validation as instance methods, not in the model:
```python
def validate_email(self) -> bool:
    """Validate email format.

    Returns:
        True if email is valid, False otherwise.
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, self.email))
```

## JSON Serialization

Do NOT add `to_dict()` methods in models. Use Marshmallow schemas for serialization.

## What NOT to Do

- ❌ Multiple model classes in one file
- ❌ Business logic in models (use services)
- ❌ Direct validation (use Marshmallow schemas)
- ❌ Hardcoded connection strings
- ❌ Missing type hints
- ❌ Missing docstrings (module and class)
- ❌ French comments or docstrings
- ❌ Old-style Column definitions without Mapped
- ❌ Missing created_at/updated_at timestamps
- ❌ Missing __repr__ method

## Testing Models

Always create corresponding tests in `tests/unit/models/test_<model_name>.py`:

```python
"""Unit tests for User model."""

import pytest
from src.api.models.user import User


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self, db_session):
        """Test creating a user instance.

        Given: Valid user data
        When: User is created
        Then: User has correct attributes
        """
        user = User(email="test@example.com", username="testuser")
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.created_at is not None

    def test_user_repr(self):
        """Test user string representation.

        Given: A user instance
        When: repr() is called
        Then: Returns formatted string
        """
        user = User(id=1, email="test@example.com")
        assert repr(user) == "<User(id=1, email='test@example.com')>"
```

## Database Migrations

After creating or modifying a model:
```bash
# Generate migration
flask db migrate -m "Add User model"

# Review the generated migration file
# Apply migration
flask db upgrade
```

## Complete Example

```python
"""Order model definition.

This module defines the Order model for managing customer orders
with full relationship support to users and order items.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from enum import Enum as PyEnum
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .. import db


class OrderStatus(PyEnum):
    """Order status enumeration.

    Defines possible states for an order lifecycle.
    """
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(db.Model):
    """Order model representing customer purchase orders.

    Manages order information including status, pricing, and
    relationships to users and order items.

    Attributes:
        id: Unique order identifier.
        order_number: Human-readable order number (unique).
        user_id: Foreign key to user who placed the order.
        status: Current order status from OrderStatus enum.
        total_amount: Total order value in decimal format.
        notes: Optional order notes.
        created_at: Order creation timestamp.
        updated_at: Last modification timestamp.
        user: Relationship to User model.
        items: Relationship to OrderItem models.
    """

    __tablename__ = "orders"

    # Primary Key
    id: Mapped[int] = mapped_column(primary_key=True)

    # Business Fields
    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    # Foreign Keys
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Status and Pricing
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    # Optional Fields
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")

    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Indexes
    __table_args__ = (
        Index("idx_order_user_status", "user_id", "status"),
    )

    def __repr__(self) -> str:
        """String representation of Order.

        Returns:
            Human-readable string with order details.
        """
        return (
            f"<Order(id={self.id}, order_number='{self.order_number}', "
            f"status={self.status.value})>"
        )
```
