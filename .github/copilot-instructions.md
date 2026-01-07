---
description: "Comprehensive instructions for using and extending the wfp-flask-template project."
applyTo: '**'
---

# Copilot Instructions for wfp-flask-template

## Template Purpose
This is a **template project** for starting new Waterfall microservices. Clone it, rename `dummy` entities to your domain, and build from there.

## Architecture Pattern

**Layered structure:** Resources (HTTP) → Schemas (validation) → Models (database)

| Layer | Location | Purpose |
|-------|----------|---------|
| Resources | `app/resources/` | Flask-RESTful endpoints, decorators for auth/access |
| Schemas | `app/schemas/` | Marshmallow schemas for validation & serialization |
| Models | `app/models/` | SQLAlchemy models with mixins for UUID, timestamps |
| Services | `app/services/` | External service clients (Guardian, Identity) |
| Utils | `app/utils/` | Decorators, JWT handling, rate limiting |

## Adding a New Resource (CRUD Endpoint)
1. Create model in `app/models/` inheriting `UUIDMixin, TimestampMixin, db.Model`
2. Create schemas in `app/schemas/` using `SQLAlchemyAutoSchema` (separate Create, Update, Replace schemas)
3. Create resource in `app/resources/` inheriting `Resource`
4. Register routes in `app/routes.py` with versioned prefix `/{api_version}/`
5. Add constants to respective `constants.py` files (never hardcode strings)
6. **Update OpenAPI spec** in `openapi/` — spec is the contract, implementation follows it

## Authentication & Authorization Stack
```python
@require_jwt_auth                    # Validates JWT from access_token cookie
@access_required(Operation.READ)     # Checks Guardian permissions
@limiter.limit(...)                  # Rate limiting
def get(self):
```
- JWT claims (`user_id`, `company_id`, `email`) trusted after validation

### Guardian Service Integration
Guardian handles RBAC via `/check-access` endpoint. Operations: `LIST`, `CREATE`, `READ`, `UPDATE`, `DELETE`
```python
# Request format sent by @access_required decorator:
{"service": "your-service", "resource_name": "projects", "operation": "CREATE",
 "context": {"project_id": "uuid"}}  # optional context
# Response: {"access_granted": true/false, "reason": "granted|no_permission"}
```

### Identity Service Integration
Identity provides user/company data. JWT contains `user_id` and `company_id` — no extra API call needed for basic auth.

## Database Types & Migrations
Use custom types from `app/models/types.py` for cross-DB compatibility:
- `GUID()` - UUID (PostgreSQL native, CHAR(36) elsewhere)
- `JSONB()` - JSON (PostgreSQL native JSONB)
- `UUIDMixin` / `TimestampMixin` - Standard id, created_at, updated_at

**Migration workflow:**
```bash
flask db migrate -m "Add projects table"  # Generate migration
flask db upgrade                          # Apply to database
flask db downgrade                        # Rollback one revision
```

## Development Commands
```bash
make install-dev          # Setup environment with dev dependencies
make run                  # Start Flask dev server
make test-unit            # Fast unit tests (no external deps)
make test-integration     # Requires: make compose-up
make test-all             # Full suite: starts services, runs all tests, stops
make check                # All quality checks (format, lint, type-check, test)
```

## Testing Conventions
- **Unit tests** (`tests/unit/`): Mock external services, use `TestingConfig`
- **Integration tests** (`tests/integration/`): Real DB via docker-compose

Key fixtures: `app`, `client`, `authenticated_client`, `api_url(endpoint)` → `/v0/dummies`

## Configuration
Configs in `app/config.py`: `DevelopmentConfig`, `TestingConfig`, `IntegrationConfig`, `StagingConfig`, `ProductionConfig`

`.env.*` files: `.env.development` (SQLite), `.env.testing` (in-memory), `.env.integration` (PostgreSQL)

## Code Quality
- **Ruff** formatting (88 chars), **MyPy** types, **isort** imports (black profile)
- All files need copyright header (`scripts/add_license_headers.py`)

## File Naming
Models: `{entity}_model.py` | Schemas: `{entity}_schema.py` | Resources: `{entity}_res.py` | Tests: `test_{module}.py`
