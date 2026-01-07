---
description: "Generate comprehensive GitHub Issues from architecture plan with complete context, acceptance criteria, and vertical slice structure"
agent: "API Architect"
tools: ["edit", "search", "search/codebase", "github/*", "read/problems"]
---

# Create GitHub Issues

You are an expert at creating comprehensive, actionable GitHub Issues. Transform an architecture plan into well-structured Issues with complete context, acceptance criteria, and technical details using vertical slicing strategy.

## Task

Generate GitHub Issues for all implementation tasks identified in the architecture plan. Each issue should be a **complete vertical slice** (full endpoint from database to API) with all necessary context.

## Input Variables

- `${input:architecturePlan}` - Path to architecture plan (e.g., `spec/architecture-projects.md`)
- `${input:repository}` - GitHub repository (e.g., `org/repo`)
- `${input:milestone}` - Milestone for these issues (e.g., `M2-CRUD`)

## Workflow

### 1. Parse Architecture Plan

Read the architecture plan:
```
${architecturePlan}
```

Extract:
- All implementation phases
- Each endpoint with its details
- Story point estimates
- Dependencies between tasks
- Guardian configuration
- Performance requirements
- Database schema

### 2. Generate Foundation Issue

Create ONE foundation issue for database setup:

**Title**: `[FOUNDATION] Database migration for ${resource} table`

**Labels**: `foundation`, `database`, `migration`

**Milestone**: `M1-Foundation`

**Story Points**: 2

**Body**:
```markdown
## Description
Create Alembic migration for ${resource} table with all columns, constraints, and indexes.

## Specification
- 📋 Spec: ${specFile}
- 📖 OpenAPI: openapi/${resource}-api.yaml
- 🏗️ Architecture: spec/architecture-${resource}.md

## Database Schema

\`\`\`sql
-- Copy DDL from architecture plan
CREATE TABLE ${resource_plural} (
    ...
);

-- All indexes
CREATE INDEX idx_${resource}_company_id ON ${resource_plural}(company_id);
...
\`\`\`

## Files to Create
- [ ] migrations/versions/xxx_add_${resource_plural}_table.py

## Acceptance Criteria
- [ ] Migration creates table with all columns
- [ ] All constraints defined (PRIMARY KEY, FOREIGN KEY, UNIQUE, CHECK)
- [ ] All indexes created for filter/sort columns
- [ ] Migration is reversible (downgrade works)
- [ ] Migration applies cleanly to empty database
- [ ] Migration tested locally

## Testing
\`\`\`bash
flask db upgrade
flask db downgrade
\`\`\`

## Estimation
Story Points: 2 (1-2 hours)

## Dependencies
None
```

### 3. Generate Endpoint Issues (Vertical Slices)

For each endpoint, create ONE complete issue including model, schema, resource, tests:

#### GET /resource - List Endpoint

**Title**: `GET /${resource_plural} - List ${resource_plural} with pagination`

**Labels**: `endpoint`, `feature`, `${resource}`

**Milestone**: `M2-CRUD`

**Story Points**: 5

**Body**:
```markdown
## Description
Implement complete endpoint for listing ${resource_plural} with pagination, filtering, and sorting.
Complete vertical slice including model (first endpoint), schema, resource, auth, and tests.

## Specification
- 📋 Spec: ${specFile} (Section X.X - List Endpoint)
- 📖 OpenAPI: openapi/${resource}-api.yaml (GET /${resource_plural})
- 🎯 Requirements: REQ-001, SEC-001, SEC-002, PERF-001, PERF-002

## Implementation Scope (Complete Vertical Slice)

### Files to Create
- [ ] app/models/${resource}_model.py - ${Resource} model
- [ ] app/schemas/${resource}_schema.py - ${Resource}Schema (base)
- [ ] app/resources/${resource}_res.py - ${Resource}ListResource.get()
- [ ] app/constants/${resource}_constants.py - Constants
- [ ] app/routes.py - Register /v0/${resource_plural} route
- [ ] tests/unit/models/test_${resource}_model.py - Model tests
- [ ] tests/unit/schemas/test_${resource}_schema.py - Schema tests
- [ ] tests/unit/resources/test_${resource}_list.py - Resource tests
- [ ] tests/integration/resources/test_${resource}_api_list.py - API tests

### Components

**Model** (create):
\`\`\`python
class ${Resource}(UUIDMixin, TimestampMixin, db.Model):
    """${Resource} database model."""
    __tablename__ = '${resource_plural}'

    # Fields from spec
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Indexes
    __table_args__ = (
        Index('idx_${resource_plural}_company_id', 'company_id'),
        Index('idx_${resource_plural}_created_at', 'created_at'),
        UniqueConstraint('name', 'company_id', name='uq_${resource_plural}_name_company'),
    )
\`\`\`

**Schema** (create):
\`\`\`python
class ${Resource}Schema(SQLAlchemyAutoSchema):
    """Base schema for ${Resource} serialization."""
    class Meta:
        model = ${Resource}
        load_instance = True
        include_fk = True
\`\`\`

**Resource** (implement):
\`\`\`python
class ${Resource}ListResource(Resource):
    """Resource for ${resource} collection operations."""

    @require_jwt_auth
    @access_required(Operation.LIST, "${resource_plural}")
    @limiter.limit("100 per minute")
    def get(self):
        """List ${resource_plural} with pagination."""
        # Parse query params (page, per_page, sort_by, sort_order)
        # Filter by company_id from JWT
        # Apply pagination
        # Return {data: [], page, per_page, total, total_pages}
\`\`\`

**Tests**:
- Unit tests (models, schemas, resources with mocks)
- Integration tests (full HTTP cycle with real DB)
- Test cases:
  - List all ${resource_plural} (paginated)
  - Filter by company_id (automatic from JWT)
  - Pagination (page, per_page parameters)
  - Sorting (sort_by, sort_order)
  - Empty list returns []
  - Auth: 401 if no JWT
  - Auth: 403 if no LIST permission
  - Rate limit: 429 if exceeded

## Acceptance Criteria
- [ ] GET /v0/${resource_plural} returns paginated list
- [ ] Response format: `{data: [], page, per_page, total, total_pages}`
- [ ] Filters ${resource_plural} by company_id from JWT automatically
- [ ] Pagination works (default 20, max 100 items per page)
- [ ] Sort by created_at desc (default), supports custom sort_by
- [ ] Returns 401 if no JWT token
- [ ] Returns 403 if user lacks LIST permission (Guardian)
- [ ] Rate limit enforced (100 requests/minute)
- [ ] Unit tests pass (≥85% coverage)
- [ ] Integration tests pass (full HTTP cycle)
- [ ] Ruff formatting and mypy type checking pass
- [ ] OpenAPI spec matches implementation

## Dependencies
Depends on: #XXX (Database migration)

## Guardian Integration
- Service: `${serviceName}`
- Resource: `${resource_plural}`
- Operation: `LIST`
- Context: `{company_id: <from JWT>}`

## Estimation
Story Points: 5 (4-6 hours)
```

#### POST /resource - Create Endpoint

**Title**: `POST /${resource_plural} - Create new ${resource}`

**Labels**: `endpoint`, `feature`, `${resource}`

**Milestone**: `M2-CRUD`

**Story Points**: 5

**Body**:
```markdown
## Description
Implement endpoint for creating new ${resource} with validation.
Vertical slice adding create schema and POST method to existing resource.

## Specification
- 📋 Spec: ${specFile} (Section X.X - Create Endpoint)
- 📖 OpenAPI: openapi/${resource}-api.yaml (POST /${resource_plural})
- 🎯 Requirements: REQ-002, SEC-001, SEC-003, VALID-001, VALID-002

## Implementation Scope

### Files to Modify/Create
- [ ] app/schemas/${resource}_schema.py - Add ${Resource}CreateSchema
- [ ] app/resources/${resource}_res.py - Add ${Resource}ListResource.post()
- [ ] tests/unit/schemas/test_${resource}_schema.py - Create schema tests
- [ ] tests/unit/resources/test_${resource}_create.py - Resource tests
- [ ] tests/integration/resources/test_${resource}_api_create.py - API tests

### Components

**Schema** (add):
\`\`\`python
class ${Resource}CreateSchema(SQLAlchemyAutoSchema):
    """Schema for ${resource} creation with validation."""
    class Meta:
        model = ${Resource}
        load_instance = True
        exclude = ('id', 'created_at', 'updated_at')

    # Custom validation
    @validates('name')
    def validate_name(self, value):
        if len(value) < 3:
            raise ValidationError("Name must be at least 3 characters")
        return value
\`\`\`

**Resource** (add method):
\`\`\`python
@require_jwt_auth
@access_required(Operation.CREATE, "${resource_plural}")
@limiter.limit("50 per minute")
def post(self):
    """Create new ${resource}."""
    # Load and validate request JSON
    # Add company_id from JWT
    # Check uniqueness (if required)
    # Create in database
    # Return 201 with created resource
\`\`\`

**Tests**:
- Valid creation
- Validation errors (missing required, invalid format)
- Duplicate detection (if unique constraint)
- Auth: 401, 403
- Rate limit: 429

## Acceptance Criteria
- [ ] POST /v0/${resource_plural} creates new ${resource}
- [ ] Returns 201 Created with resource data and Location header
- [ ] Validates all required fields (returns 400 if missing)
- [ ] Validates field constraints (returns 422 if invalid)
- [ ] Checks uniqueness constraint (returns 409 if duplicate)
- [ ] Automatically sets company_id from JWT (user cannot override)
- [ ] Returns 401 if no JWT token
- [ ] Returns 403 if user lacks CREATE permission
- [ ] Rate limit: 50 req/min
- [ ] Tests pass (≥85% coverage)

## Dependencies
Depends on: #YYY (GET /${resource_plural} - model exists)

## Guardian Integration
- Service: `${serviceName}`
- Resource: `${resource_plural}`
- Operation: `CREATE`
- Context: `{company_id: <from JWT>}`

## Estimation
Story Points: 5 (4-6 hours)
```

#### GET /resource/{id} - Retrieve Endpoint

**Title**: `GET /${resource_plural}/{id} - Retrieve single ${resource}`

**Labels**: `endpoint`, `feature`, `${resource}`

**Milestone**: `M2-CRUD`

**Story Points**: 4

**Body**:
```markdown
## Description
Implement endpoint for retrieving a single ${resource} by ID.
Creates ${Resource}Resource class for item operations.

## Specification
- 📋 Spec: ${specFile} (Section X.X - Retrieve Endpoint)
- 📖 OpenAPI: openapi/${resource}-api.yaml (GET /${resource_plural}/{id})
- 🎯 Requirements: REQ-003, SEC-001, SEC-004

## Implementation Scope

### Files to Modify/Create
- [ ] app/resources/${resource}_res.py - Add ${Resource}Resource.get()
- [ ] app/routes.py - Register /${resource_plural}/<uuid:id> route
- [ ] tests/unit/resources/test_${resource}_retrieve.py
- [ ] tests/integration/resources/test_${resource}_api_retrieve.py

### Components

**Resource** (create class):
\`\`\`python
class ${Resource}Resource(Resource):
    """Resource for single ${resource} operations."""

    @require_jwt_auth
    @access_required(Operation.READ, "${resource_plural}")
    @limiter.limit("100 per minute")
    def get(self, ${resource}_id: uuid.UUID):
        """Retrieve ${resource} by ID."""
        # Query by id AND company_id (security!)
        # Return 404 if not found or wrong company
        # Return 200 with resource data
\`\`\`

**Tests**:
- Retrieve existing ${resource}
- 404 if not found
- 404 if wrong company_id (security)
- Auth: 401, 403

## Acceptance Criteria
- [ ] GET /v0/${resource_plural}/{id} returns single ${resource}
- [ ] Returns 200 OK with resource data
- [ ] Returns 404 if ${resource} not found
- [ ] Returns 404 if ${resource} belongs to different company (security!)
- [ ] Returns 401 if no JWT token
- [ ] Returns 403 if user lacks READ permission
- [ ] Rate limit: 100 req/min
- [ ] Tests pass (≥85% coverage)

## Dependencies
Depends on: #YYY (GET list - model and base schema exist)

## Guardian Integration
- Service: `${serviceName}`
- Resource: `${resource_plural}`
- Operation: `READ`
- Context: `{company_id: <from JWT>, ${resource}_id: <from URL>}`

## Estimation
Story Points: 4 (3-5 hours)
```

#### PATCH /resource/{id} - Update Endpoint

**Title**: `PATCH /${resource_plural}/{id} - Update ${resource}`

**Labels**: `endpoint`, `feature`, `${resource}`

**Milestone**: `M2-CRUD`

**Story Points**: 5

**Body**:
```markdown
## Description
Implement endpoint for partial update of ${resource}.
Adds update schema and PATCH method.

## Specification
- 📋 Spec: ${specFile} (Section X.X - Update Endpoint)
- 📖 OpenAPI: openapi/${resource}-api.yaml (PATCH /${resource_plural}/{id})
- 🎯 Requirements: REQ-004, SEC-001, SEC-005, VALID-003

## Implementation Scope

### Files to Modify/Create
- [ ] app/schemas/${resource}_schema.py - Add ${Resource}UpdateSchema
- [ ] app/resources/${resource}_res.py - Add ${Resource}Resource.patch()
- [ ] tests/unit/schemas/test_${resource}_schema.py
- [ ] tests/unit/resources/test_${resource}_update.py
- [ ] tests/integration/resources/test_${resource}_api_update.py

### Components

**Schema** (add):
\`\`\`python
class ${Resource}UpdateSchema(SQLAlchemyAutoSchema):
    """Schema for partial ${resource} update."""
    class Meta:
        model = ${Resource}
        load_instance = False
        exclude = ('id', 'company_id', 'created_at', 'updated_at')
        partial = True  # All fields optional
\`\`\`

**Resource** (add method):
\`\`\`python
@require_jwt_auth
@access_required(Operation.UPDATE, "${resource_plural}")
@limiter.limit("50 per minute")
def patch(self, ${resource}_id: uuid.UUID):
    """Partially update ${resource}."""
    # Find by id AND company_id
    # Validate partial data
    # Update only provided fields
    # Return 200 with updated resource
\`\`\`

**Tests**:
- Update single field
- Update multiple fields
- Validation errors
- 404 if not found
- Cannot update immutable fields (id, company_id, timestamps)
- Auth: 401, 403

## Acceptance Criteria
- [ ] PATCH /v0/${resource_plural}/{id} updates ${resource}
- [ ] Returns 200 OK with updated resource
- [ ] Supports partial updates (only provided fields updated)
- [ ] Validates field constraints (returns 422 if invalid)
- [ ] Returns 404 if ${resource} not found or wrong company
- [ ] Cannot update immutable fields (id, company_id, timestamps)
- [ ] Returns 401 if no JWT token
- [ ] Returns 403 if user lacks UPDATE permission
- [ ] Rate limit: 50 req/min
- [ ] Tests pass (≥85% coverage)

## Dependencies
Depends on: #ZZZ (GET /${resource_plural}/{id} - resource class exists)

## Guardian Integration
- Service: `${serviceName}`
- Resource: `${resource_plural}`
- Operation: `UPDATE`
- Context: `{company_id: <from JWT>, ${resource}_id: <from URL>}`

## Estimation
Story Points: 5 (4-6 hours)
```

#### DELETE /resource/{id} - Delete Endpoint

**Title**: `DELETE /${resource_plural}/{id} - Delete ${resource}`

**Labels**: `endpoint`, `feature`, `${resource}`

**Milestone**: `M2-CRUD`

**Story Points**: 4

**Body**:
```markdown
## Description
Implement endpoint for deleting ${resource}.
Adds DELETE method with cascade handling.

## Specification
- 📋 Spec: ${specFile} (Section X.X - Delete Endpoint)
- 📖 OpenAPI: openapi/${resource}-api.yaml (DELETE /${resource_plural}/{id})
- 🎯 Requirements: REQ-005, SEC-001, SEC-006

## Implementation Scope

### Files to Modify/Create
- [ ] app/resources/${resource}_res.py - Add ${Resource}Resource.delete()
- [ ] tests/unit/resources/test_${resource}_delete.py
- [ ] tests/integration/resources/test_${resource}_api_delete.py

### Components

**Resource** (add method):
\`\`\`python
@require_jwt_auth
@access_required(Operation.DELETE, "${resource_plural}")
@limiter.limit("50 per minute")
def delete(self, ${resource}_id: uuid.UUID):
    """Delete ${resource}."""
    # Find by id AND company_id
    # Check cascade constraints (if has related data)
    # Delete or soft-delete
    # Return 204 No Content
\`\`\`

**Tests**:
- Successful deletion
- 404 if not found
- Cascade behavior (if applicable)
- Cannot delete if has dependencies (if applicable)
- Auth: 401, 403

## Acceptance Criteria
- [ ] DELETE /v0/${resource_plural}/{id} deletes ${resource}
- [ ] Returns 204 No Content on success
- [ ] Returns 404 if ${resource} not found or wrong company
- [ ] Handles cascade deletion properly (if has related entities)
- [ ] Returns 409 if cannot delete due to dependencies (if applicable)
- [ ] Returns 401 if no JWT token
- [ ] Returns 403 if user lacks DELETE permission
- [ ] Rate limit: 50 req/min
- [ ] Tests pass (≥85% coverage)

## Dependencies
Depends on: #ZZZ (GET /${resource_plural}/{id} - resource class exists)

## Guardian Integration
- Service: `${serviceName}`
- Resource: `${resource_plural}`
- Operation: `DELETE`
- Context: `{company_id: <from JWT>, ${resource}_id: <from URL>}`

## Estimation
Story Points: 4 (3-5 hours)
```

### 4. Generate Quality Issue

Create final quality/optimization issue:

**Title**: `Performance optimization & documentation for ${resource_plural} API`

**Labels**: `optimization`, `docs`, `quality`

**Milestone**: `M3-Quality`

**Story Points**: 3

**Body**:
```markdown
## Description
Optimize performance and complete documentation for ${resource_plural} API.

## Specification
- 📋 Spec: ${specFile}
- 📖 OpenAPI: openapi/${resource}-api.yaml

## Tasks

### Performance
- [ ] Verify all indexes are used (EXPLAIN ANALYZE)
- [ ] Add database query profiling
- [ ] Implement caching strategy (if applicable)
- [ ] Load test endpoints (verify rate limits)
- [ ] Optimize N+1 queries (if any)

### Documentation
- [ ] Validate OpenAPI spec against implementation
- [ ] Add/verify all examples in OpenAPI
- [ ] Document error responses
- [ ] Add inline code documentation (docstrings)
- [ ] Update README if needed

### Quality
- [ ] Coverage ≥85% for all modules
- [ ] Ruff and mypy pass
- [ ] Security scan clean
- [ ] Manual testing of all endpoints

## Acceptance Criteria
- [ ] All queries use indexes efficiently
- [ ] Response times meet PERF requirements (<200ms p95)
- [ ] Rate limiting tested and working
- [ ] OpenAPI spec 100% accurate
- [ ] Code coverage ≥85%
- [ ] All linters pass
- [ ] Manual testing completed

## Dependencies
Depends on: All endpoint issues (#XXX, #YYY, #ZZZ, etc.)

## Estimation
Story Points: 3 (2-4 hours)
```

### 5. Create Issues in GitHub

For each issue generated:
1. Create issue via GitHub API
2. Set labels
3. Set milestone
4. Add to project board (if configured)
5. Link dependencies in issue body

### 6. Summary Report

Generate summary:
```markdown
## GitHub Issues Created

### Foundation (M1-Foundation)
- [ ] #XXX: [FOUNDATION] Database migration for ${resource_plural} table

### Core Endpoints (M2-CRUD)
- [ ] #YYY: GET /${resource_plural} - List ${resource_plural}
- [ ] #ZZZ: POST /${resource_plural} - Create ${resource}
- [ ] #AAA: GET /${resource_plural}/{id} - Retrieve ${resource}
- [ ] #BBB: PATCH /${resource_plural}/{id} - Update ${resource}
- [ ] #CCC: DELETE /${resource_plural}/{id} - Delete ${resource}

### Quality (M3-Quality)
- [ ] #DDD: Performance optimization & documentation

**Total Issues**: 7
**Total Story Points**: 28
**Estimated Time**: 1.5-2 weeks (1 developer)

## Implementation Order
1. #XXX (Foundation) - Creates database table
2. #YYY (GET list) - Creates model, base schema, first endpoint
3. #ZZZ, #AAA, #BBB, #CCC (Other endpoints) - Can be parallelized
4. #DDD (Quality) - Final polish

## Next Steps
1. Review and refine issues
2. Assign to developers
3. Start with foundation issue (#XXX)
4. Proceed with GET list endpoint (#YYY)
5. Parallelize remaining CRUD endpoints
```

## Quality Checklist

Before creating issues:
- [ ] Each endpoint is a complete vertical slice
- [ ] Foundation issue separate from endpoints
- [ ] All acceptance criteria from spec included
- [ ] Guardian integration documented
- [ ] Story points realistic (4-6h per endpoint)
- [ ] Dependencies properly linked
- [ ] Labels and milestones assigned
- [ ] Test requirements specified
- [ ] OpenAPI compliance mentioned

## Example Usage

```
@api-architect /create-github-issues
Architecture: spec/architecture-projects.md
Repository: waterfall/projects-service
Milestone: M2-CRUD
```

The agent will:
1. Parse architecture plan
2. Generate 7 comprehensive issues (1 foundation + 5 endpoints + 1 quality)
3. Create issues in GitHub with labels and milestones
4. Link dependencies
5. Provide summary report

---

**Note**: Issues follow vertical slicing pattern where each endpoint is delivered complete with model, schema, resource, and tests.
