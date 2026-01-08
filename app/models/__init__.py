# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Database models package.

Provides SQLAlchemy database instance, custom types, and mixins for models.
"""

from app.models.db import db
from app.models.dummy import Dummy
from app.models.types import GUID, JSONB, TimestampMixin, UUIDMixin

__all__ = ["db", "Dummy", "GUID", "JSONB", "UUIDMixin", "TimestampMixin"]
