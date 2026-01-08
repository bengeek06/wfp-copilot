# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro
"""Custom SQLAlchemy column types for cross-database compatibility.

This module provides custom column types that work seamlessly across
different database backends (SQLite, PostgreSQL, etc.) while maintaining
optimal performance and native type support where available.
"""

import json
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB as PostgreSQLJSONB  # noqa: N811
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID  # noqa: N811
from sqlalchemy.orm import Mapped, mapped_column

from app import db


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type.

    Uses PostgreSQL's native UUID type when available, otherwise uses
    CHAR(36) for maximum compatibility (SQLite, MySQL, etc.). Always
    returns Python uuid.UUID objects regardless of backend.

    Attributes:
        impl: Base SQLAlchemy type (String).
        cache_ok: Enables caching for improved performance.

    Example:
        >>> class User(db.Model):
        ...     id = db.Column(GUID(), primary_key=True, default=uuid.uuid4)
        ...     company_id = db.Column(GUID(), nullable=False)
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load the appropriate type for the current database dialect.

        Args:
            dialect: The SQLAlchemy dialect being used.

        Returns:
            Native UUID type for PostgreSQL, CHAR(36) for other databases.
        """
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQLUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(
        self, value: uuid.UUID | str | None, dialect
    ) -> uuid.UUID | str | None:
        """Convert Python value to database format.

        Handles both UUID objects and strings, converting them appropriately
        for the target database. This ensures compatibility whether the value
        comes from application code (UUID) or from external sources like
        JSON payloads (string).

        Args:
            value: Python UUID object, string, or None.
            dialect: The SQLAlchemy dialect being used.

        Returns:
            UUID object for PostgreSQL, string for other databases, or None.
        """
        if value is None:
            return value

        # Convert to UUID first if it's a string
        if isinstance(value, str):
            value = uuid.UUID(value)

        # Return appropriate format for dialect
        if dialect.name == "postgresql":
            return value  # PostgreSQL handles UUID natively
        else:
            return str(value)  # SQLite and others need string

    def process_result_value(
        self, value: uuid.UUID | str | None, dialect
    ) -> uuid.UUID | None:
        """Convert database value to Python UUID.

        Args:
            value: Database value (native UUID or string).
            dialect: The SQLAlchemy dialect being used.

        Returns:
            Python uuid.UUID object or None.
        """
        if value is None:
            return value
        if not isinstance(value, uuid.UUID):
            return uuid.UUID(value)
        return value


class JSONB(TypeDecorator):
    """Platform-independent JSONB type.

    Uses PostgreSQL's native JSONB type when available (with indexing
    and query capabilities), otherwise uses TEXT with JSON serialization
    for compatibility with SQLite and other databases.

    Attributes:
        impl: Base SQLAlchemy type (Text).
        cache_ok: Enables caching for improved performance.

    Example:
        >>> class User(db.Model):
        ...     metadata = db.Column(JSONB(), default={})
        ...     settings = db.Column(JSONB(), nullable=True)
        >>>
        >>> user = User(metadata={"theme": "dark", "notifications": True})
        >>> user.metadata["theme"]
        'dark'
    """

    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """Load the appropriate type for the current database dialect.

        Args:
            dialect: The SQLAlchemy dialect being used.

        Returns:
            Native JSONB type for PostgreSQL, TEXT for other databases.
        """
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgreSQLJSONB())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(
        self, value: dict | list | None, dialect
    ) -> dict | list | str | None:
        """Convert Python value to database format.

        Args:
            value: Python dict, list, or None.
            dialect: The SQLAlchemy dialect being used.

        Returns:
            Native Python object for PostgreSQL, JSON string for others, or None.
        """
        if value is None or dialect.name == "postgresql":
            return value
        else:
            return json.dumps(value)

    def process_result_value(
        self, value: str | dict | list | None, dialect
    ) -> dict | list | None:
        """Convert database value to Python object.

        Args:
            value: Database value (native JSON or string).
            dialect: The SQLAlchemy dialect being used.

        Returns:
            Python dict or list, or None.
        """
        if value is None:
            return value
        if dialect.name == "postgresql":
            # PostgreSQL returns native dict/list, never str
            return value  # type: ignore[return-value]
        else:
            return json.loads(value) if isinstance(value, str) else value


class UUIDMixin:
    """Mixin class to add UUID primary key to models.

    Provides a standard UUID-based primary key with automatic generation.
    Use this mixin for models that should have UUID identifiers instead
    of auto-incrementing integers.

    Attributes:
        id: UUID primary key with automatic generation via uuid.uuid4().

    Example:
        >>> class Company(UUIDMixin, db.Model):
        ...     __tablename__ = 'companies'
        ...     name: Mapped[str] = mapped_column(String(100), nullable=False)
        >>>
        >>> company = Company(name="Acme Corp")
        >>> isinstance(company.id, uuid.UUID)  # Auto-generated
        True
    """

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    """Mixin class to add created_at and updated_at timestamps.

    Automatically tracks creation and modification times for database records.

    Attributes:
        created_at: Timestamp of record creation (auto-set on insert).
        updated_at: Timestamp of last update (auto-updated on modify).

    Example:
        >>> class Article(TimestampMixin, db.Model):
        ...     __tablename__ = 'articles'
        ...     title: Mapped[str] = mapped_column(String(200), nullable=False)
        >>>
        >>> article = Article(title="Hello World")
        >>> db.session.add(article)
        >>> db.session.commit()
        >>> article.created_at  # Automatically set
        datetime.datetime(2025, 12, 21, 18, 30, 0)
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=db.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )
