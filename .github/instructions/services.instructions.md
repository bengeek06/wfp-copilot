---
applyTo: "src/**/services/**/*.py"
excludeAgent: []
description: "Instructions for creating and maintaining service layer files in the project."
---

# Services Instructions

## Purpose
Services contain the business logic layer. They orchestrate operations between resources and models, handle complex workflows, and enforce business rules. Each service file should contain exactly ONE service class.

## Naming Conventions

- **File name**: Singular, lowercase with underscores (e.g., `user.py`, `order.py`)
- **Class name**: Singular with "Service" suffix (e.g., `UserService`, `OrderService`)
- **Methods**: Verb-based, lowercase with underscores (e.g., `create_user`, `get_by_email`)

## Required Structure

```python
"""User service for business logic.

This module implements business logic for user management including
creation, retrieval, updates and validation operations.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.user import User
from ..schemas.user import UserCreateSchema, UserUpdateSchema
from ..utils.exceptions import NotFoundError, ConflictError


class UserService:
    """Service class for user business logic.
    
    Handles all business operations related to users including
    CRUD operations, validation, and complex workflows.
    
    Attributes:
        db_session: SQLAlchemy database session.
    """
    
    def __init__(self, db_session: Session) -> None:
        """Initialize UserService with database session.
        
        Args:
            db_session: SQLAlchemy session for database operations.
        """
        self.db_session = db_session
    
    def create(self, data: dict) -> User:
        """Create a new user.
        
        Validates data and creates a new user in the database.
        Ensures email uniqueness and applies business rules.
        
        Args:
            data: Dictionary containing user data.
            
        Returns:
            Created User instance.
            
        Raises:
            ConflictError: If email already exists.
            ValidationError: If data is invalid.
        """
        # Check for existing email
        if self.get_by_email(data.get("email")):
            raise ConflictError("Email already exists")
        
        try:
            user = User(**data)
            self.db_session.add(user)
            self.db_session.commit()
            self.db_session.refresh(user)
            return user
        except IntegrityError as e:
            self.db_session.rollback()
            raise ConflictError(f"Database constraint violation: {str(e)}")
    
    def get_by_id(self, user_id: int) -> User:
        """Retrieve user by ID.
        
        Args:
            user_id: Unique user identifier.
            
        Returns:
            User instance if found.
            
        Raises:
            NotFoundError: If user does not exist.
        """
        user = self.db_session.get(User, user_id)
        if not user:
            raise NotFoundError(f"User with id {user_id} not found")
        return user
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve user by email.
        
        Args:
            email: User email address.
            
        Returns:
            User instance if found, None otherwise.
        """
        return self.db_session.query(User).filter_by(email=email).first()
    
    def list(
        self,
        page: int = 1,
        per_page: int = 20,
        is_active: Optional[bool] = None
    ) -> tuple[list[User], int]:
        """Retrieve paginated list of users.
        
        Args:
            page: Page number (1-indexed).
            per_page: Number of items per page.
            is_active: Filter by activation status if provided.
            
        Returns:
            Tuple of (list of users, total count).
        """
        query = self.db_session.query(User)
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        total = query.count()
        users = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return users, total
    
    def update(self, user_id: int, data: dict) -> User:
        """Update an existing user.
        
        Args:
            user_id: Unique user identifier.
            data: Dictionary containing fields to update.
            
        Returns:
            Updated User instance.
            
        Raises:
            NotFoundError: If user does not exist.
            ConflictError: If email is taken by another user.
        """
        user = self.get_by_id(user_id)
        
        # Check email uniqueness if changing email
        if "email" in data and data["email"] != user.email:
            existing = self.get_by_email(data["email"])
            if existing:
                raise ConflictError("Email already exists")
        
        for key, value in data.items():
            setattr(user, key, value)
        
        try:
            self.db_session.commit()
            self.db_session.refresh(user)
            return user
        except IntegrityError as e:
            self.db_session.rollback()
            raise ConflictError(f"Database constraint violation: {str(e)}")
    
    def delete(self, user_id: int) -> None:
        """Delete a user.
        
        Args:
            user_id: Unique user identifier.
            
        Raises:
            NotFoundError: If user does not exist.
        """
        user = self.get_by_id(user_id)
        self.db_session.delete(user)
        self.db_session.commit()
```

## Core Principles

### 1. Dependency Injection
Always inject dependencies through constructor:
```python
class UserService:
    def __init__(self, db_session: Session, email_service: EmailService) -> None:
        self.db_session = db_session
        self.email_service = email_service
```

### 2. Single Responsibility
Each service handles one domain entity. Don't mix concerns:
```python
# Correct ✓
class UserService:
    def create_user(self, data: dict) -> User: ...
    def update_user(self, user_id: int, data: dict) -> User: ...

# Incorrect ✗
class UserService:
    def create_user(self, data: dict) -> User: ...
    def send_welcome_email(self, user: User) -> None: ...  # Should be in EmailService
```

### 3. Type Hints
Every method must have complete type hints:
```python
def create(self, data: dict[str, Any]) -> User:
def list(self, page: int = 1) -> tuple[list[User], int]:
def get_by_id(self, user_id: int) -> Optional[User]:
```

### 4. Error Handling
Use custom exceptions, never generic ones:
```python
# Correct ✓
raise NotFoundError(f"User {user_id} not found")
raise ConflictError("Email already exists")

# Incorrect ✗
raise Exception("User not found")
raise ValueError("Email exists")
```

## Standard Methods

Every service should implement these standard CRUD operations:

### Create
```python
def create(self, data: dict[str, Any]) -> Model:
    """Create a new entity.
    
    Args:
        data: Entity creation data.
        
    Returns:
        Created entity instance.
        
    Raises:
        ConflictError: If entity already exists.
        ValidationError: If data is invalid.
    """
```

### Read (Single)
```python
def get_by_id(self, entity_id: int) -> Model:
    """Retrieve entity by ID.
    
    Args:
        entity_id: Unique identifier.
        
    Returns:
        Entity instance.
        
    Raises:
        NotFoundError: If entity does not exist.
    """
```

### Read (List)
```python
def list(
    self,
    page: int = 1,
    per_page: int = 20,
    filters: Optional[dict[str, Any]] = None
) -> tuple[list[Model], int]:
    """Retrieve paginated list of entities.
    
    Args:
        page: Page number (1-indexed).
        per_page: Items per page.
        filters: Optional filtering criteria.
        
    Returns:
        Tuple of (entities list, total count).
    """
```

### Update
```python
def update(self, entity_id: int, data: dict[str, Any]) -> Model:
    """Update an existing entity.
    
    Args:
        entity_id: Unique identifier.
        data: Fields to update.
        
    Returns:
        Updated entity instance.
        
    Raises:
        NotFoundError: If entity does not exist.
        ConflictError: If update violates constraints.
    """
```

### Delete
```python
def delete(self, entity_id: int) -> None:
    """Delete an entity.
    
    Args:
        entity_id: Unique identifier.
        
    Raises:
        NotFoundError: If entity does not exist.
    """
```

## Transaction Management

### Explicit Commits
Always commit explicitly, never rely on auto-commit:
```python
def create(self, data: dict) -> User:
    user = User(**data)
    self.db_session.add(user)
    self.db_session.commit()  # Explicit commit
    self.db_session.refresh(user)
    return user
```

### Rollback on Error
Always rollback on exceptions:
```python
try:
    user = User(**data)
    self.db_session.add(user)
    self.db_session.commit()
    return user
except IntegrityError as e:
    self.db_session.rollback()  # Always rollback
    raise ConflictError(str(e))
```

### Context Managers for Complex Operations
```python
def complex_operation(self, data: dict) -> User:
    """Perform complex multi-step operation."""
    try:
        # Step 1
        user = User(**data)
        self.db_session.add(user)
        
        # Step 2
        profile = Profile(user_id=user.id)
        self.db_session.add(profile)
        
        # Commit all or nothing
        self.db_session.commit()
        return user
    except Exception as e:
        self.db_session.rollback()
        raise
```

## Business Logic Examples

### Complex Validation
```python
def create_premium_user(self, data: dict) -> User:
    """Create a premium user with special validation.
    
    Args:
        data: User creation data.
        
    Returns:
        Created premium user.
        
    Raises:
        ValidationError: If validation fails.
        ConflictError: If constraints violated.
    """
    # Business rule: Premium users need verified email domain
    email = data.get("email", "")
    if not email.endswith(("@company.com", "@enterprise.com")):
        raise ValidationError("Premium users require corporate email")
    
    # Business rule: Check subscription limit
    active_premium = self.db_session.query(User).filter_by(
        is_premium=True,
        is_active=True
    ).count()
    
    if active_premium >= 1000:
        raise ConflictError("Premium user limit reached")
    
    data["is_premium"] = True
    return self.create(data)
```

### Cascade Operations
```python
def deactivate_user(self, user_id: int) -> User:
    """Deactivate user and related entities.
    
    Args:
        user_id: User identifier.
        
    Returns:
        Deactivated user.
        
    Raises:
        NotFoundError: If user not found.
    """
    user = self.get_by_id(user_id)
    
    # Business logic: Cancel active subscriptions
    for subscription in user.subscriptions:
        if subscription.is_active:
            subscription.is_active = False
    
    # Business logic: Archive orders
    for order in user.orders:
        order.status = OrderStatus.ARCHIVED
    
    user.is_active = False
    self.db_session.commit()
    self.db_session.refresh(user)
    
    return user
```

## Query Optimization

### Eager Loading
```python
def get_with_relations(self, user_id: int) -> User:
    """Get user with all relationships loaded.
    
    Args:
        user_id: User identifier.
        
    Returns:
        User with loaded relationships.
    """
    from sqlalchemy.orm import joinedload
    
    user = self.db_session.query(User).options(
        joinedload(User.orders),
        joinedload(User.profile)
    ).filter_by(id=user_id).first()
    
    if not user:
        raise NotFoundError(f"User {user_id} not found")
    
    return user
```

### Bulk Operations
```python
def bulk_deactivate(self, user_ids: list[int]) -> int:
    """Deactivate multiple users.
    
    Args:
        user_ids: List of user identifiers.
        
    Returns:
        Number of users deactivated.
    """
    count = self.db_session.query(User).filter(
        User.id.in_(user_ids)
    ).update(
        {"is_active": False},
        synchronize_session=False
    )
    
    self.db_session.commit()
    return count
```

## Logging and Monitoring

### Structured Logging
```python
import logging
from flask import g

logger = logging.getLogger(__name__)


class UserService:
    def create(self, data: dict) -> User:
        """Create a new user with logging."""
        logger.info(
            "Creating user",
            extra={
                "correlation_id": g.get("correlation_id"),
                "email": data.get("email"),
                "action": "user_create"
            }
        )
        
        try:
            user = User(**data)
            self.db_session.add(user)
            self.db_session.commit()
            
            logger.info(
                "User created successfully",
                extra={
                    "correlation_id": g.get("correlation_id"),
                    "user_id": user.id
                }
            )
            
            return user
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

## What NOT to Do

- ❌ Multiple service classes in one file
- ❌ Direct database access from resources (always use services)
- ❌ HTTP-related code in services (status codes, request/response)
- ❌ Missing type hints on methods
- ❌ Missing or incomplete docstrings (always in English)
- ❌ Generic exception handling without rollback
- ❌ Business logic in models or resources
- ❌ Hardcoded values (use config)
- ❌ Missing logging for important operations
- ❌ Forgetting to refresh after commit when returning entity

## Testing Services

Always create comprehensive service tests in `tests/unit/services/test_<service_name>.py`:

```python
"""Unit tests for UserService."""

import pytest
from unittest.mock import Mock, MagicMock
from src.api.services.user import UserService
from src.api.models.user import User
from src.api.utils.exceptions import NotFoundError, ConflictError


class TestUserService:
    """Tests for UserService."""
    
    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def user_service(self, db_session):
        """UserService instance with mocked session."""
        return UserService(db_session)
    
    def test_create_user_success(self, user_service, db_session):
        """Test successful user creation.
        
        Given: Valid user data
        When: create() is called
        Then: User is created and committed
        """
        data = {"email": "test@example.com", "username": "test"}
        
        user_service.create(data)
        
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()
    
    def test_get_by_id_not_found(self, user_service, db_session):
        """Test retrieving non-existent user.
        
        Given: User does not exist
        When: get_by_id() is called
        Then: NotFoundError is raised
        """
        db_session.get.return_value = None
        
        with pytest.raises(NotFoundError):
            user_service.get_by_id(999)
    
    def test_create_duplicate_email(self, user_service, db_session):
        """Test creating user with existing email.
        
        Given: Email already exists
        When: create() is called
        Then: ConflictError is raised
        """
        from sqlalchemy.exc import IntegrityError
        
        data = {"email": "existing@example.com"}
        db_session.commit.side_effect = IntegrityError("", "", "")
        
        with pytest.raises(ConflictError):
            user_service.create(data)
        
        db_session.rollback.assert_called_once()
```

## Complete Example

See the main structure example at the top of this document for a complete, production-ready service implementation.