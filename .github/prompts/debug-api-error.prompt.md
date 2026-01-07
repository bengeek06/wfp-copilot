---
description: "Analyze API errors, stack traces, and logs to identify root cause and suggest fixes for Flask REST APIs"
agent: "Flask API Expert"
tools: ["search", "search/codebase", "read/problems", "search/changes", "web/fetch", "read/terminalLastCommand"]
---

# Debug API Error

You are an expert Flask API debugger. Analyze error messages, stack traces, logs, and HTTP responses to identify root causes and provide actionable fixes for common API issues.

## Task

Diagnose and resolve API errors by:
- **Analyzing stack traces** and error messages
- **Identifying root cause** (database, validation, auth, Guardian, business logic)
- **Categorizing error type** (500, 422, 403, 401, 404, 409, etc.)
- **Suggesting specific fixes** with code examples
- **Providing prevention strategies** to avoid similar issues

## Input Variables

- `${input:errorMessage}` - Error message or stack trace (paste full error)
- `${input:httpStatus}` - HTTP status code (e.g., 500, 422, 403)
- `${input:endpoint}` - Endpoint that failed (e.g., GET /projects, POST /tasks)
- `${input:context}` - Additional context (request body, query params, logs)

## Workflow

### 1. Parse Error Information

Extract key information from error:
- **Exception type** (ValueError, IntegrityError, Unauthorized, etc.)
- **Error message** (text description)
- **Stack trace** (file paths, line numbers, function calls)
- **HTTP status code** (if available)
- **Endpoint and method** (GET, POST, PATCH, DELETE)

### 2. Categorize Error Type

Classify error into category:

**Database Errors** (IntegrityError, OperationalError, DataError):
- Foreign key violation
- Unique constraint violation
- NULL constraint violation
- Data type mismatch
- Connection timeout
- Query syntax error

**Validation Errors** (ValidationError, ValueError):
- Missing required fields
- Invalid field format (email, UUID, enum)
- Field length violations (min/max)
- Type mismatches (string vs number)
- Custom validation failures

**Authentication Errors** (Unauthorized, 401):
- Missing JWT token
- Expired JWT token
- Invalid JWT signature
- Missing authentication header
- Malformed token

**Authorization Errors** (Forbidden, 403):
- Missing Guardian permission
- Wrong company_id (multi-tenancy violation)
- Resource ownership check failed
- Role insufficient for operation
- Guardian service unreachable

**Business Logic Errors**:
- Invalid state transitions
- Constraint violations (can't delete with dependencies)
- Rate limiting exceeded
- Resource conflicts (409)

**Infrastructure Errors**:
- Database connection failed
- External service timeout (Guardian, Identity)
- Out of memory
- Network issues

### 3. Analyze Stack Trace

Walk through stack trace from bottom (origin) to top (where exception surfaced):

```python
# Example stack trace analysis
Traceback (most recent call last):
  File "app/resources/project_res.py", line 45, in post
    new_project = Project(**data)              # ← Where exception occurred
  File "app/models/project_model.py", line 23, in __init__
    if len(name) < 3:                          # ← Root cause
TypeError: object of type 'NoneType' has no len()

# Analysis:
# 1. Exception: TypeError (type mismatch)
# 2. Root cause: 'name' field is None
# 3. Location: project_model.py line 23
# 4. Trigger: Missing validation before accessing name.length
# 5. Fix: Add null check or schema validation
```

**Key Questions**:
- What line threw the exception? (bottom of stack)
- What function called it? (trace upward)
- What file is involved? (model, schema, resource, service)
- What operation failed? (database query, validation, HTTP call)

### 4. Identify Root Cause

Common root causes by category:

**Database Root Causes**:
```python
# IntegrityError: duplicate key
# Root: Trying to insert duplicate on unique constraint
# Location: db.session.commit()
# Fix: Check for existing record before insert, return 409

# IntegrityError: foreign key violation
# Root: Referenced entity doesn't exist
# Location: Assigning invalid FK (project_id, company_id)
# Fix: Verify FK exists before assignment

# OperationalError: connection timeout
# Root: Database unreachable or query too slow
# Location: db.session.execute(query)
# Fix: Check DB connection, add timeout, optimize query
```

**Validation Root Causes**:
```python
# ValidationError: Missing required field
# Root: Client didn't send required field, schema allows it
# Location: schema.load(request.json)
# Fix: Ensure schema has required=True for mandatory fields

# ValueError: Invalid UUID format
# Root: Client sent non-UUID string for UUID field
# Location: uuid.UUID(value)
# Fix: Add format validation in schema with UUID field type

# ValidationError: Field too long
# Root: Input exceeds maxLength in schema
# Location: Marshmallow validation
# Fix: Expected behavior, return 422 to client
```

**Auth/Authz Root Causes**:
```python
# Unauthorized (401): No JWT
# Root: Client didn't send access_token cookie
# Location: @require_jwt_auth decorator
# Fix: Client must authenticate first (POST /login)

# Forbidden (403): No Guardian permission
# Root: User lacks required role/permission
# Location: @access_required decorator → Guardian API call
# Fix: Assign correct role to user in Guardian

# Forbidden (403): Wrong company_id
# Root: Resource belongs to different company
# Location: Query filter by company_id returns empty
# Fix: Expected behavior (multi-tenancy working correctly)
```

**Business Logic Root Causes**:
```python
# ValueError: Invalid state transition
# Root: Business rule violation (can't move from 'completed' to 'active')
# Location: Custom validation in model or resource
# Fix: Check if transition allowed, return 422 with error message

# IntegrityError: Can't delete (foreign key constraint)
# Root: Resource has dependent records (project has tasks)
# Location: db.session.delete(project)
# Fix: Either cascade delete or return 409 with message
```

### 5. Suggest Specific Fix

Provide concrete, actionable fix with code:

**Example 1: Missing Validation**

**Error**:
```
TypeError: object of type 'NoneType' has no len()
File "app/models/project_model.py", line 23
    if len(self.name) < 3:
```

**Root Cause**: `name` is None, validation didn't catch it

**Fix**:
```python
# In app/schemas/project_schema.py
class ProjectCreateSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Project
        exclude = ('id', 'created_at', 'updated_at')
    
    # Add required validation
    name = fields.String(required=True, validate=Length(min=3, max=255))
    #                    ^^^^^^^^^^^^^^ This prevents None values

# Alternative: Add null check in model
class Project(UUIDMixin, TimestampMixin, db.Model):
    def __init__(self, **kwargs):
        # Validate before accessing
        name = kwargs.get('name')
        if name is None:
            raise ValueError("name is required")
        if len(name) < 3:
            raise ValueError("name must be at least 3 characters")
        super().__init__(**kwargs)
```

**Prevention**: Always validate inputs in schema with `required=True` for mandatory fields

---

**Example 2: IntegrityError - Duplicate Key**

**Error**:
```
IntegrityError: duplicate key value violates unique constraint "uq_projects_name_company"
DETAIL: Key (name, company_id)=(Project A, uuid) already exists.
```

**Root Cause**: Trying to create project with name that already exists for this company

**Fix**:
```python
# In app/resources/project_res.py
class ProjectListResource(Resource):
    @require_jwt_auth
    @access_required(Operation.CREATE, "projects")
    def post(self):
        claims = get_jwt_claims()
        company_id = claims['company_id']
        
        # Load and validate
        schema = ProjectCreateSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as e:
            return {"errors": e.messages}, 422
        
        # Check for duplicate BEFORE inserting
        existing = Project.query.filter_by(
            name=data['name'],
            company_id=company_id
        ).first()
        
        if existing:
            return {
                "error": "Conflict",
                "message": f"Project '{data['name']}' already exists"
            }, 409  # 409 Conflict
        
        # Safe to create
        data['company_id'] = company_id
        project = Project(**data)
        db.session.add(project)
        
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            # Race condition: created between check and insert
            return {
                "error": "Conflict",
                "message": "Project already exists"
            }, 409
        
        return ProjectSchema().dump(project), 201
```

**Prevention**: 
- Check for duplicates before INSERT
- Wrap commit in try/except for race conditions
- Return 409 Conflict (not 500) for duplicates

---

**Example 3: Guardian 403 Forbidden**

**Error**:
```
Forbidden: Access denied
Response from Guardian: {"access_granted": false, "reason": "no_permission"}
```

**Root Cause**: User doesn't have required Guardian permission

**Fix (Two Options)**:

**Option A: Assign Role to User** (if user should have access)
```bash
# In Guardian admin UI or via API:
# 1. Verify user exists
curl -X GET https://guardian.example.com/api/v1/users/search?email=user@example.com

# 2. Assign role
curl -X POST https://guardian.example.com/api/v1/user-roles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "user_id": "uuid-from-step-1",
    "role": "projects_editor",
    "company_id": "uuid-company",
    "service": "projects-service"
  }'

# 3. Test again
curl -X POST https://api.example.com/v0/projects \
  -H "Cookie: access_token=$USER_JWT" \
  -d '{"name": "Test Project"}'
```

**Option B: Fix Missing Decorator** (if code is wrong)
```python
# If decorator is missing:
class ProjectListResource(Resource):
    @require_jwt_auth
    @access_required(Operation.CREATE, "projects")  # ← Add this if missing
    def post(self):
        ...
```

**Prevention**:
- Always use `@access_required` on protected endpoints
- Document required roles in API spec
- Test with users having different roles

---

**Example 4: Foreign Key Violation**

**Error**:
```
IntegrityError: insert or update on table "tasks" violates foreign key constraint "tasks_project_id_fkey"
DETAIL: Key (project_id)=(non-existent-uuid) is not present in table "projects".
```

**Root Cause**: Client sent invalid `project_id` that doesn't exist

**Fix**:
```python
# In app/resources/task_res.py
class TaskListResource(Resource):
    @require_jwt_auth
    @access_required(Operation.CREATE, "tasks")
    def post(self):
        claims = get_jwt_claims()
        company_id = claims['company_id']
        
        schema = TaskCreateSchema()
        try:
            data = schema.load(request.json)
        except ValidationError as e:
            return {"errors": e.messages}, 422
        
        project_id = data.get('project_id')
        
        # Verify project exists AND belongs to user's company
        project = Project.query.filter_by(
            id=project_id,
            company_id=company_id  # Security: company isolation
        ).first()
        
        if not project:
            return {
                "error": "Validation Error",
                "message": "Invalid project_id: project not found or access denied"
            }, 422  # 422 Unprocessable Entity
        
        # Safe to create task
        data['company_id'] = company_id
        task = Task(**data)
        db.session.add(task)
        db.session.commit()
        
        return TaskSchema().dump(task), 201
```

**Prevention**:
- Validate FK references before INSERT
- Check company_id for multi-tenancy security
- Return 422 (not 500) for invalid FKs

---

**Example 5: Database Connection Timeout**

**Error**:
```
OperationalError: (psycopg2.OperationalError) could not connect to server: Connection timed out
	Is the server running on host "db.example.com" (10.0.1.5) and accepting TCP/IP connections on port 5432?
```

**Root Cause**: Database is unreachable or overloaded

**Fix (Debugging Steps)**:
```bash
# 1. Check if database is running
docker ps | grep postgres
# or
systemctl status postgresql

# 2. Test connection manually
psql -h db.example.com -U dbuser -d dbname

# 3. Check network connectivity
ping db.example.com
telnet db.example.com 5432

# 4. Check database load
# Connect to DB and run:
SELECT count(*) FROM pg_stat_activity;  # Active connections
SELECT * FROM pg_stat_activity WHERE state = 'active';  # Running queries

# 5. Check connection pool settings
# In config.py:
SQLALCHEMY_POOL_SIZE = 10  # Increase if exhausted
SQLALCHEMY_POOL_TIMEOUT = 30  # Seconds to wait
SQLALCHEMY_POOL_RECYCLE = 3600  # Recycle connections
SQLALCHEMY_MAX_OVERFLOW = 20  # Extra connections allowed
```

**Fix (Code)**:
```python
# Add retry logic for transient errors
from sqlalchemy.exc import OperationalError
from time import sleep

def create_project_with_retry(data, max_retries=3):
    """Create project with retry on connection errors."""
    for attempt in range(max_retries):
        try:
            project = Project(**data)
            db.session.add(project)
            db.session.commit()
            return project
        except OperationalError as e:
            db.session.rollback()
            if attempt < max_retries - 1:
                sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            raise  # Give up after max_retries
```

**Prevention**:
- Monitor database health
- Set appropriate connection pool size
- Add retry logic for transient errors
- Use database connection timeout settings

### 6. Provide Debugging Commands

Suggest commands to investigate further:

**View logs**:
```bash
# Application logs
tail -f logs/app.log | grep ERROR

# Flask development server
flask run --debug

# Docker logs
docker logs -f container_name
```

**Test endpoint manually**:
```bash
# With curl
curl -X POST http://localhost:5000/v0/projects \
  -H "Cookie: access_token=$JWT" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "description": "Debug test"}' \
  -v  # Verbose output

# With httpie (prettier)
http POST localhost:5000/v0/projects \
  Cookie:"access_token=$JWT" \
  name="Test" \
  description="Debug test"
```

**Database inspection**:
```bash
# Connect to database
flask shell

# In shell:
from app.models import Project
from app import db

# Check if record exists
Project.query.filter_by(name="Test").all()

# Check constraints
db.engine.execute("SELECT * FROM information_schema.table_constraints WHERE table_name='projects'")

# Verify data
Project.query.get("uuid-here")
```

**Guardian debugging**:
```bash
# Check user roles
curl https://guardian.example.com/api/v1/user-roles?user_id=UUID

# Test permission directly
curl -X POST https://guardian.example.com/check-access \
  -H "Authorization: Bearer $JWT" \
  -d '{
    "service": "projects-service",
    "resource_name": "projects",
    "operation": "CREATE",
    "context": {"company_id": "uuid", "user_id": "uuid"}
  }'
```

### 7. Prevention Strategies

Recommend patterns to avoid similar errors:

**For Validation Errors**:
- ✅ Always use `required=True` for mandatory fields in schemas
- ✅ Add `validate=Length(min, max)` for string fields
- ✅ Use `validate=OneOf([...])` for enums
- ✅ Define custom validators with `@validates` decorator
- ✅ Test with invalid inputs (missing fields, wrong types, out of range)

**For Database Errors**:
- ✅ Check for duplicates before INSERT on unique constraints
- ✅ Verify FK exists before assigning foreign keys
- ✅ Wrap commits in try/except IntegrityError
- ✅ Return appropriate status codes (409 for duplicates, 422 for invalid FK)
- ✅ Add database indexes for filter/sort columns
- ✅ Use connection pooling correctly

**For Auth/Authz Errors**:
- ✅ Always use `@require_jwt_auth` on protected endpoints
- ✅ Always use `@access_required` for authorization
- ✅ Filter by `company_id` from JWT (multi-tenancy)
- ✅ Test with users having different roles
- ✅ Document required permissions in API spec
- ✅ Handle Guardian service unavailability gracefully

**For Business Logic Errors**:
- ✅ Validate business rules explicitly (state transitions, constraints)
- ✅ Return meaningful error messages (not just "validation failed")
- ✅ Use appropriate status codes (422 for business rule violations)
- ✅ Document business rules in specification
- ✅ Test edge cases and error paths

### 8. Generate Debugging Report

Create structured analysis:

```markdown
# API Error Debug Report
## Error: ${error_type}

### Summary
- **Endpoint**: ${endpoint}
- **HTTP Status**: ${status}
- **Exception**: ${exception_type}
- **Root Cause**: ${root_cause}
- **Severity**: ${critical/high/medium/low}

### Error Details

**Stack Trace**:
\`\`\`
${stack_trace}
\`\`\`

**Error Message**: ${error_message}

**Location**: ${file}:${line} in ${function}

### Root Cause Analysis

${detailed_analysis}

**Why It Happened**:
- ${reason_1}
- ${reason_2}

**Impact**:
- ${impact_description}

### Fix

**Immediate Fix** (resolves this error):
\`\`\`python
${code_fix}
\`\`\`

**Test Fix**:
\`\`\`bash
${test_command}
\`\`\`

**Expected Result**: ${expected_outcome}

### Prevention

**Long-term Solution** (prevents recurrence):
- ${prevention_strategy_1}
- ${prevention_strategy_2}

**Code Improvements**:
\`\`\`python
${improved_code}
\`\`\`

**Tests to Add**:
\`\`\`python
${test_case}
\`\`\`

### Related Issues

- Similar error patterns to watch for
- Related endpoints that might have same issue
- Documentation to update

### References

- Spec section: ${spec_reference}
- Related requirements: ${requirements}
- Flask docs: ${flask_docs_link}
- SQLAlchemy docs: ${sqlalchemy_docs_link}
```

## Quick Reference: Error → Fix Mapping

| Error Type | HTTP Status | Common Cause | Quick Fix |
|------------|-------------|--------------|-----------|
| IntegrityError (duplicate) | 409 | Unique constraint violation | Check before insert, return 409 |
| IntegrityError (FK) | 422 | Invalid foreign key | Validate FK exists, return 422 |
| IntegrityError (NOT NULL) | 422 | Missing required field | Add required=True in schema |
| ValidationError | 422 | Invalid field format | Fix schema validation rules |
| Unauthorized (401) | 401 | Missing/invalid JWT | Client must authenticate |
| Forbidden (403) | 403 | No Guardian permission | Assign role or fix decorator |
| Forbidden (403) | 403 | Wrong company_id | Expected (multi-tenancy working) |
| NotFound (404) | 404 | Resource doesn't exist | Verify ID, check company_id filter |
| ValueError | 500 | Type mismatch in code | Add validation, fix types |
| AttributeError | 500 | Accessing None | Add null checks |
| OperationalError | 500 | DB connection issue | Check DB health, retry logic |
| TimeoutError | 500 | External service timeout | Add timeout handling, retry |

## Quality Checklist

Before completing debug session:
- [ ] Error type correctly identified
- [ ] Root cause clearly explained
- [ ] Fix provided with code example
- [ ] Fix tested and verified
- [ ] Prevention strategies suggested
- [ ] Related tests recommended
- [ ] Documentation updated if needed
- [ ] Similar issues checked across codebase

## Example Usage

```
@flask-api-expert /debug-api-error

Error: IntegrityError: duplicate key value violates unique constraint "uq_projects_name_company"
HTTP Status: 500
Endpoint: POST /v0/projects
Context: Creating project with name "Project A" for company XYZ

# Agent analyzes, identifies duplicate issue, suggests fix:
# - Check for existing record before insert
# - Return 409 Conflict instead of 500
# - Add test for duplicate handling
```

---

**Note**: This prompt focuses on Flask/SQLAlchemy/Guardian stack errors. For frontend or infrastructure errors, use appropriate debugging tools.
