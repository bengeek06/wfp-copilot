---
description: "Generate conventional commit messages from code changes following Conventional Commits specification"
agent: "Git & GitHub Expert"
tools: ["search/changes", "search", "search/codebase"]
---

# Generate Conventional Commits

You are an expert at creating meaningful, conventional commit messages. Analyze code changes and generate commit messages following the Conventional Commits specification organized by architectural layer.

## Task

Generate structured, informative commit messages that:
- Follow **Conventional Commits** format
- Group changes by **architectural layer** (model, schema, resource, tests)
- Include **scope** (resource name)
- Reference **specification** sections
- Link to **GitHub issues**
- Provide clear **description** of what changed and why

## Conventional Commits Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring (no functional change)
- `test`: Adding/updating tests
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `perf`: Performance improvements
- `chore`: Build, tooling, dependencies
- `ci`: CI/CD configuration

**Scope**: Module or resource name (e.g., `projects`, `users`, `auth`)

**Subject**: Imperative mood, lowercase, no period (max 72 chars)

**Body**: Detailed explanation, wrapped at 72 characters (optional)

**Footer**: Issue references, breaking changes (optional)

## Workflow

### 1. Analyze Code Changes

Review changed files and categorize by layer:

**Model changes** (`app/models/*.py`):
- New model created
- Fields added/modified
- Relationships changed
- Constraints updated
- Indexes added

**Schema changes** (`app/schemas/*.py`):
- New schema created
- Validation rules added
- Field serialization changed
- Custom validators added

**Resource changes** (`app/resources/*.py`):
- New endpoint implemented
- Business logic added
- HTTP method added
- Authorization updated
- Error handling improved

**Test changes** (`tests/**/*.py`):
- New tests added
- Test coverage increased
- Test fixtures updated
- Integration tests added

**Documentation** (`docs/`, `*.md`):
- OpenAPI spec updated
- README updated
- Architecture docs changed

**Infrastructure** (`migrations/`, `config/`):
- Database migration
- Configuration changes
- Dependencies updated

### 2. Group Changes by Layer

Organize changes into logical groups:

```
Changes detected:
├── Model Layer
│   └── app/models/project_model.py (new file, +87 lines)
├── Schema Layer
│   └── app/schemas/project_schema.py (new file, +45 lines)
├── Resource Layer
│   ├── app/resources/project_res.py (new file, +123 lines)
│   └── app/routes.py (modified, +4 lines)
├── Test Layer
│   ├── tests/unit/test_project_model.py (new file, +65 lines)
│   ├── tests/unit/test_project_schema.py (new file, +52 lines)
│   └── tests/integration/test_project_api_list.py (new file, +98 lines)
└── Migration
    └── migrations/versions/xxx_add_projects_table.py (new file, +42 lines)
```

### 3. Generate Commit Messages

Create ONE commit message for all related changes (vertical slice):

**For Complete Endpoint Implementation** (Recommended - Vertical Slice):
```
feat(projects): implement GET /projects list endpoint

Complete vertical slice for listing projects:
- Model: Project with UUIDMixin, TimestampMixin
- Schema: ProjectSchema for serialization
- Resource: ProjectListResource.get() with pagination
- Routes: Register /v0/projects endpoint
- Tests: 8 unit tests, 6 integration tests (92% coverage)
- Auth: JWT + Guardian LIST permission
- Rate limit: 100 requests/minute

Implements: spec/schema-api-projects-crud.md Section 4.1
Closes #124
```

**Alternative: Multiple Commits by Layer** (If required by team conventions):

**Commit 1 - Model**:
```
feat(model): add Project model with UUID and timestamps

- Inherit from UUIDMixin, TimestampMixin, db.Model
- Fields: name, description, company_id, is_active
- Constraints: unique(name, company_id)
- Indexes: company_id, created_at

Implements: spec/schema-api-projects-crud.md Section 4
Related: #124
```

**Commit 2 - Schema**:
```
feat(schema): add Project schemas for CRUD operations

- ProjectSchema: Base serialization schema
- ProjectCreateSchema: Creation with validation
- ProjectUpdateSchema: Partial update schema
- Validates: name length (3-255), required fields

Implements: spec/schema-api-projects-crud.md Section 5
Related: #124
```

**Commit 3 - Resource**:
```
feat(resource): add Project REST endpoints

- GET /v0/projects: List with pagination, filtering, sorting
- POST /v0/projects: Create with validation
- GET /v0/projects/{id}: Retrieve single project
- PATCH /v0/projects/{id}: Partial update
- DELETE /v0/projects/{id}: Delete project
- Auth: @require_jwt_auth + @access_required decorators
- Rate limiting: 50-100 requests/minute per endpoint

Implements: spec/schema-api-projects-crud.md Section 6-10
Related: #124
```

**Commit 4 - Tests**:
```
test(projects): add comprehensive test suite

- Unit tests: models, schemas, resources (68 tests)
- Integration tests: full HTTP cycle (23 tests)
- Coverage: 92% (models 95%, schemas 90%, resources 90%)
- Test scenarios: CRUD, validation, auth, rate limits, errors

Related: #124
```

**Commit 5 - Documentation**:
```
docs(openapi): update OpenAPI spec with Project endpoints

- Add /v0/projects paths (GET, POST)
- Add /v0/projects/{id} paths (GET, PATCH, DELETE)
- Define ProjectSchema components
- Add error response examples (400, 401, 403, 404, 422, 429)
- Validate spec against implementation

Related: #124
```

### 4. Handle Different Change Types

**Bug Fix**:
```
fix(projects): correct pagination calculation for edge cases

- Fix off-by-one error in total_pages calculation
- Handle empty result sets correctly
- Add tests for edge cases (0 items, 1 item, exact page boundary)

Fixes #234
```

**Refactoring**:
```
refactor(projects): extract query builder to separate method

- Move complex query logic to _build_project_query()
- Improve testability and readability
- No functional changes
- Tests still pass (92% coverage)

Related: #124
```

**Performance**:
```
perf(projects): optimize list query with database indexes

- Add composite index on (company_id, is_active, created_at)
- Reduce query time from 450ms to 95ms (p95)
- Add EXPLAIN ANALYZE tests
- Update spec/architecture-projects.md with index strategy

Closes #245
```

**Breaking Change**:
```
feat(projects)!: change pagination response format

BREAKING CHANGE: Pagination metadata moved to root level

Before:
{
  "data": [...],
  "meta": {"page": 1, "per_page": 20, "total": 50}
}

After:
{
  "data": [...],
  "page": 1,
  "per_page": 20,
  "total": 50,
  "total_pages": 3
}

Reason: Consistency with other Waterfall services
Migration: Update API clients to read from root level

Closes #256
```

### 5. Reference Specification

Always link commits to specification:

```
feat(tasks): implement POST /tasks create endpoint

- TaskCreateSchema with validation (title 3-200 chars, status enum)
- TaskListResource.post() with company_id auto-assignment
- Guardian CREATE permission check
- Tests: creation, validation errors, auth, duplicates

Implements: spec/schema-api-tasks-crud.md Section 6
Closes #203
```

### 6. Multi-File Changes

When changes span multiple files but serve one purpose:

```
feat(auth): add Guardian authorization integration

Changes across layers:
- utils/access_control.py: @access_required decorator
- utils/auth.py: get_jwt_claims() helper
- constants/auth_constants.py: Guardian operation enum
- resources/*_res.py: Apply decorators to all endpoints
- tests/unit/test_access_control.py: Decorator tests
- tests/integration/test_auth_integration.py: Guardian API tests

Implements: spec/security-requirements.md Section 3
Closes #189
```

### 7. Quality Checklist

Before finalizing commit message:
- [ ] Type is appropriate (feat, fix, refactor, test, docs)
- [ ] Scope matches resource/module name
- [ ] Subject is imperative, lowercase, <72 chars
- [ ] Body explains WHAT and WHY (not HOW - code shows that)
- [ ] Specification reference included (if applicable)
- [ ] Issue reference included ("Closes #123" or "Related: #123")
- [ ] Breaking changes called out with "BREAKING CHANGE:"
- [ ] Changes grouped logically (by layer or feature)

## Commit Message Template

```
<type>(<scope>): <short description>

[Optional body explaining the change]
- Bullet points for multiple changes
- Reference architecture layers
- Explain why, not how

[Optional footer]
Implements: spec/file.md Section X.X
Closes #123
Related: #456
```

## Examples by Scenario

### Complete Endpoint (Vertical Slice)
```
feat(orders): implement GET /orders list endpoint

Complete vertical slice for order listing:
- Model: Order with status, total, customer relationship
- Schema: OrderSchema with nested customer serialization
- Resource: OrderListResource.get() with filters (status, date_range)
- Routes: /v0/orders endpoint registered
- Tests: 12 unit, 8 integration (94% coverage)
- Auth: JWT + Guardian LIST + company isolation
- Performance: Indexed on (company_id, status, created_at)

Implements: spec/schema-api-orders-crud.md Section 4.1
Closes #301
```

### Bug Fix
```
fix(users): prevent duplicate email registration

- Add unique constraint on email (case-insensitive)
- Return 409 Conflict instead of 500 on duplicate
- Add test_user_create_duplicate_email test
- Update OpenAPI with 409 response

Fixes #412
```

### Database Migration
```
chore(db): add projects table migration

- Create projects table with all columns and constraints
- Indexes on company_id, created_at, is_active
- Foreign key to companies table
- Trigger for updated_at auto-update
- Migration tested (upgrade/downgrade)

Related: #124
```

### Documentation
```
docs(api): update README with Guardian integration guide

- Add Guardian authorization section
- Document @access_required decorator usage
- Include role setup instructions
- Add troubleshooting for 403 errors

Related: #189
```

## Example Usage

```
@git-github-expert /generate-conventional-commits

# Agent analyzes staged changes:
git diff --cached

# Output: Suggested commit messages grouped by layer
```

---

**Note**: Prefer ONE commit per vertical slice (complete endpoint) for better traceability and atomic PRs. Multiple commits by layer should only be used if team conventions require it.
