# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Dummy model definition.

This module defines the Dummy model as an example resource for the
wfp-flask-template, demonstrating multi-tenancy, soft deletion, and
all standard CRUD patterns.
"""

import uuid
from typing import Optional

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app import db
from app.models.types import GUID, TimestampMixin, UUIDMixin


class Dummy(UUIDMixin, TimestampMixin, db.Model):
    """Dummy resource model.

    Represents an example resource for demonstrating CRUD operations,
    JWT authentication, Guardian authorization, and multi-tenancy patterns
    in the Waterfall Flask template.

    This model demonstrates:
    - UUID primary keys via UUIDMixin
    - Automatic timestamps via TimestampMixin
    - Multi-tenancy isolation by company_id
    - Soft deletion with is_active flag
    - Unique constraint per company
    - Proper indexing for performance

    Attributes:
        id: Unique identifier (UUID, primary key).
        name: Dummy name (3-255 characters, required, unique per company).
        description: Optional description (max 1000 characters).
        company_id: Company identifier for multi-tenancy (UUID, required).
        is_active: Active status flag (soft delete, default True).
        created_at: Timestamp of creation (auto-generated).
        updated_at: Timestamp of last update (auto-updated).
    """

    __tablename__ = "dummies"

    # Required Fields
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, doc="Unique name within company"
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        nullable=False,
        index=True,
        doc="Company ID for multi-tenancy isolation",
    )

    # Optional Fields
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, doc="Optional description (max 1000 chars)"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        doc="Active status (soft delete flag)",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "name",
            "company_id",
            name="uq_dummies_name_company",
        ),
    )

    def __repr__(self) -> str:
        """String representation of Dummy.

        Returns:
            Human-readable string with key attributes.
        """
        return f"<Dummy(id={self.id}, name='{self.name}', company_id={self.company_id}, is_active={self.is_active})>"
