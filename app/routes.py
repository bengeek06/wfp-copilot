# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Route registration."""

from flask_restful import Api


def register_routes(app):
    """Register all API routes."""
    api = Api(app)
    _ = api  # To avoid unused variable warning

    # Health endpoints will be registered here
    # Versioned API endpoints will be registered here
