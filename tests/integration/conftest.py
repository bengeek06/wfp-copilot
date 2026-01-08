# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro

"""Pytest fixtures for integration tests.

This module provides common fixtures for integration testing with real
database connections and full application stack.
"""

import os
from collections.abc import Generator

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app import create_app, db


@pytest.fixture(scope="session")
def app() -> Generator[Flask, None, None]:
    """Create Flask application instance for integration testing.

    Application is created once per test session for efficiency.
    Uses IntegrationConfig with real PostgreSQL database or SQLite.

    Yields:
        Flask application configured for integration tests.
    """
    os.environ["TESTING"] = "true"
    app = create_app("app.config.IntegrationConfig")

    with app.app_context():
        # Create all tables
        db.create_all()
        yield app
        # Cleanup
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app: Flask) -> FlaskClient:
    """Create Flask test client for making HTTP requests.

    Recreated for each test function to ensure isolation.

    Args:
        app: Flask application fixture.

    Returns:
        Flask test client for making HTTP requests.
    """
    return app.test_client()
