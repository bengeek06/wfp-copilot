# Contributing to Waterfall

Thank you for your interest in contributing to Waterfall! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Architecture](#project-architecture)
- [Coding Standards](#coding-standards)
- [OpenAPI Specification](#openapi-specification)
- [Testing](#testing)
- [Git Workflow](#git-workflow)
- [Pull Request Process](#pull-request-process)
- [License](#license)

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/wfp-copilot.git
   cd wfp-copilot
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/bengeek06/wfp-copilot.git
   ```

## Development Setup

### Prerequisites

- **Python 3.11+** (required)
- **Docker** and **Docker Compose** (for integration tests)
- **Make** (for automation commands)
- **Git** (for version control)

### Installation

Install development dependencies:

```bash
make install-dev
```

This will:
- Create a virtual environment
- Install all dependencies from `pyproject.toml`
- Install pre-commit hooks

### Environment Configuration

Create a `.env.development` file for local development:

```bash
# Database
DATABASE_URL=sqlite:///data/app.db

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES=3600

# Service Configuration
SERVICE_NAME=wfp-flask-template
SERVICE_VERSION=1.0.0
SERVICE_PORT=5000

# Guardian Service (for RBAC)
GUARDIAN_SERVICE_URL=http://localhost:5001
GUARDIAN_SERVICE_TIMEOUT=5

# Metrics
METRICS_API_KEY=your-metrics-api-key

# Logging
LOG_LEVEL=DEBUG
```

### Running the Application

**Development server**:
```bash
make run
```

**Or directly with Python**:
```bash
python run.py
```

**With Docker**:
```bash
make compose-up
```

## Project Architecture

This project follows a **layered architecture** pattern:

```
app/
├── models/          # SQLAlchemy models (database layer)
├── schemas/         # Marshmallow schemas (validation/serialization)
├── resources/       # Flask-RESTful resources (HTTP endpoints)
├── services/        # Business logic and external service clients
├── utils/           # Utilities (decorators, JWT, rate limiting)
└── constants/       # Constants and enumerations
```

### Architecture Principles

- **Separation of Concerns**: Resources → Services → Models
- **One File Per Entity**: `models/user.py`, `schemas/user.py`, `resources/user.py`
- **Centralized Routes**: All routes defined in `app/routes.py`
- **Specification-Driven**: OpenAPI spec is the contract, implementation follows it
- **Security First**: JWT authentication + Guardian RBAC on all protected endpoints

## Coding Standards

### Python Style

Follow **PEP 8** with these configurations:

- **Formatter**: Ruff (line length: 100)
- **Type Checker**: mypy (strict mode)
- **Linter**: Ruff with comprehensive rule set
- **Import Sorting**: isort (black profile)

### Code Quality Commands

**Format code**:
```bash
make format
```

**Lint code**:
```bash
make lint
```

**Type check**:
```bash
make type-check
```

**Run all checks**:
```bash
make check
```

### Documentation Standards

- **All docstrings in English** using **Google Style**
- **Type hints required** on all functions
- **Module docstrings** at the top of every file
- **Copyright header** on all source files:

```python
# Copyright (c) 2025 Waterfall
#
# This source code is dual-licensed under:
# - GNU Affero General Public License v3.0 (AGPLv3) for open source use
# - Commercial License for proprietary use
#
# See LICENSE and LICENSE.md files in the root directory for full license text.
# For commercial licensing inquiries, contact: contact@waterfall-project.pro
```

### Example Documentation

```python
"""User management service module.

This module provides business logic for user CRUD operations,
authentication, and authorization according to OpenAPI specification.
"""

from typing import Optional


def get_user_by_id(user_id: int) -> Optional[dict[str, Any]]:
    """Retrieve a user by their unique identifier.

    Args:
        user_id: Unique identifier of the user.

    Returns:
        User dictionary if found, None otherwise.

    Raises:
        DatabaseError: If database connection fails.

    Examples:
        >>> user = get_user_by_id(1)
        >>> print(user["email"])
        'user@example.com'
    """
    pass
```

## OpenAPI Specification

### Specification-Driven Development

**CRITICAL**: Implementation MUST follow OpenAPI specification.

1. **Read the specification** in `openapi/` and `spec/` directories
2. **Extract requirements** from markdown specs (REQ-xxx, SEC-xxx)
3. **Implement exactly** according to spec
4. **Validate conformity** before submitting PR

### Validation

Validate OpenAPI specs:

```bash
npx @redocly/cli lint --config .redocly.yaml openapi/**/*.yaml
```

Generate API documentation:

```bash
npx @redocly/cli build-docs openapi/dummies-api.yaml -o docs/api.html
```

### Adding New Endpoints

1. **Update OpenAPI spec** in `openapi/` directory
2. **Update markdown spec** in `spec/` directory with requirements
3. **Create/update model** in `app/models/`
4. **Create/update schemas** in `app/schemas/`
5. **Create/update resource** in `app/resources/`
6. **Register routes** in `app/routes.py`
7. **Add tests** in `tests/`
8. **Validate conformity** against spec

## Testing

### Test Structure

```
tests/
├── unit/              # Fast unit tests (mocked dependencies)
└── integration/       # Integration tests (real database)
```

### Running Tests

**Unit tests only** (fast):
```bash
make test-unit
```

**Integration tests** (requires Docker):
```bash
make test-integration
```

**All tests with coverage**:
```bash
make test-all
```

**Coverage report**:
```bash
make test-cov
```

### Test Conventions

- **File naming**: `test_*.py`
- **Class naming**: `TestResourceName`
- **Function naming**: `test_operation_scenario`
- **Structure**: Given-When-Then pattern
- **Fixtures**: Use pytest fixtures from `conftest.py`

### Example Test

```python
"""Integration tests for user resources."""

import pytest
from flask.testing import FlaskClient


class TestUserListResource:
    """Tests for UserListResource."""

    def test_get_users_success(self, client: FlaskClient) -> None:
        """Test retrieving user list.

        Given: Users exist in database
        When: GET /users is called
        Then: Status is 200 and data is correct
        """
        response = client.get("/users")

        assert response.status_code == 200
        assert "users" in response.json
        assert isinstance(response.json["users"], list)
```

## Git Workflow

This project follows **Git Flow** branching model:

- **`main`**: Production-ready code
- **`develop`**: Integration branch for features
- **`feature/*`**: Feature branches
- **`hotfix/*`**: Emergency fixes for production

### Creating a Feature Branch

1. **Update develop branch**:
   ```bash
   git checkout develop
   git pull upstream develop
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/123-add-user-endpoint
   ```

3. **Make changes and commit**:
   ```bash
   git add .
   git commit -m "feat: add user CRUD endpoint (closes #123)"
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/123-add-user-endpoint
   ```

### Commit Message Format

Follow **Conventional Commits** specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Build process or auxiliary tool changes

**Examples**:
```
feat(resources): add user CRUD endpoints
fix(auth): correct JWT token expiration handling
docs(api): update OpenAPI spec for users endpoint
test(integration): add tests for user deletion
```

## Pull Request Process

### Before Submitting

1. **Run all checks**:
   ```bash
   make check
   ```

2. **Run all tests**:
   ```bash
   make test-all
   ```

3. **Update documentation** if needed

4. **Validate OpenAPI spec**:
   ```bash
   npx @redocly/cli lint openapi/**/*.yaml
   ```

### PR Checklist

- [ ] Code follows style guidelines (Ruff, mypy pass)
- [ ] All tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated (docstrings, README, specs)
- [ ] OpenAPI spec updated and validated
- [ ] Commit messages follow Conventional Commits
- [ ] PR description explains changes clearly
- [ ] Related issue referenced (closes #123)

### PR Template

```markdown
## Description
Brief description of changes

## Related Issue
Closes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] OpenAPI spec validated
```

### Review Process

1. **Automated checks** must pass (GitHub Actions)
2. **Code review** by at least one maintainer
3. **All discussions resolved**
4. **Merge to develop** after approval

## License

This project is dual-licensed:

- **GNU Affero General Public License v3.0 (AGPLv3)** for open source use
- **Commercial License** for proprietary use

By contributing, you agree that your contributions will be licensed under these terms.

See [LICENSE](LICENSE) and [LICENSE.md](LICENSE.md) for full details.

For commercial licensing inquiries, contact: contact@waterfall-project.pro

---

Thank you for contributing to wfp-flask-template! 🎉
