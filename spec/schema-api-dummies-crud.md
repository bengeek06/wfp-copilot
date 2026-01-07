---
title: Dummies CRUD API Specification
version: 1.0
date_created: 2026-01-07
last_updated: 2026-01-07
owner: Backend Team
tags: [api, crud, example, template, authentication, authorization]
---

# Introduction

This specification defines a complete CRUD API for the "Dummy" resource, serving as an example implementation in the wfp-flask-template. This resource demonstrates all standard patterns: JWT authentication, Guardian authorization, multi-tenancy isolation, pagination, validation, and error handling.

## 1. Purpose & Scope

**Purpose:**
- Provide a reference implementation for CRUD endpoints in Waterfall microservices
- Demonstrate authentication, authorization, and multi-tenancy patterns
- Serve as a starting point for new resource implementations
- Enable testing and validation of the template architecture

**Scope:**
- Five CRUD endpoints: List, Create, Retrieve, Update, Delete
- JWT authentication required for all endpoints
- Guardian authorization with LIST, CREATE, READ, UPDATE, DELETE operations
- Multi-tenancy isolation by company_id
- Pagination and sorting for list endpoint
- Comprehensive validation and error handling

**Target Audience:**
- Backend developers implementing new resources
- API consumers testing the service
- DevOps teams validating deployments

**Assumptions:**
- JWT token contains `user_id`, `company_id`, `email` claims
- Guardian service is available and configured
- PostgreSQL database with dummies table
- Users can only access dummies within their company

## 2. Definitions

| Term | Definition |
|------|------------|
| Dummy | Example resource entity for demonstration purposes |
| Multi-tenancy | Data isolation ensuring users only see their company's data |
| Soft Delete | Setting is_active=false instead of physical deletion |
| Guardian Context | Additional data sent to Guardian for authorization decisions |
| Pagination | Splitting large result sets into smaller pages |

## 3. Requirements, Constraints & Guidelines

### Functional Requirements (REQ-xxx)

**REQ-001**: API SHALL expose five CRUD endpoints for Dummy resource
**REQ-002**: All endpoints SHALL be under `/v0/dummies` path with API versioning
**REQ-003**: List endpoint SHALL support pagination with page, per_page parameters
**REQ-004**: List endpoint SHALL support sorting with sort_by, sort_order parameters
**REQ-005**: List endpoint SHALL return total count and total pages in response
**REQ-006**: All endpoints SHALL filter dummies by company_id from JWT automatically
**REQ-007**: Create/Update SHALL validate name field (3-255 characters, required)
**REQ-008**: Update SHALL support partial updates (PATCH semantics)
**REQ-009**: Delete SHALL perform soft delete (set is_active=false) and return 204 No Content
**REQ-010**: Delete SHALL return 410 Gone if dummy already soft-deleted (is_active=false)
**REQ-011**: Retrieve SHALL return 404 if dummy not found or belongs to another company
**REQ-012**: All endpoints SHALL accept optional X-Correlation-ID request header
**REQ-013**: All endpoints SHALL return X-Correlation-ID in response headers
**REQ-014**: System SHALL auto-generate UUID correlation_id if not provided in request
**REQ-015**: All log entries SHALL include correlation_id for request tracing
**REQ-016**: Correlation ID SHALL be propagated to all downstream service calls (Guardian, etc.)
**REQ-017**: Update endpoint SHALL NOT allow setting is_active=true (prevents reactivation via PATCH)

### Security Requirements (SEC-xxx)

**SEC-001**: All endpoints SHALL require valid JWT token via `access_token` cookie
**SEC-002**: All endpoints SHALL verify Guardian permissions before processing
**SEC-003**: List endpoint SHALL require Guardian LIST permission on "dummies" resource
**SEC-004**: Create endpoint SHALL require Guardian CREATE permission
**SEC-005**: Retrieve endpoint SHALL require Guardian READ permission
**SEC-006**: Update endpoint SHALL require Guardian UPDATE permission
**SEC-007**: Delete endpoint SHALL require Guardian DELETE permission
**SEC-008**: Guardian context SHALL include company_id for all operations
**SEC-009**: Guardian context SHALL include dummy_id for item operations (READ, UPDATE, DELETE)
**SEC-010**: Endpoints SHALL enforce company_id isolation (users cannot access other companies' data)
**SEC-011**: Endpoints SHALL rate limit to 100 requests per minute per user
**SEC-012**: OpenAPI spec SHALL include `x-guardian-operation` extension for each endpoint to document required permissions

### Performance Requirements (PERF-xxx)

**PERF-001**: List endpoint SHALL respond in < 300ms for pages up to 100 items (99th percentile)
**PERF-002**: Create endpoint SHALL respond in < 200ms (99th percentile)
**PERF-003**: Retrieve endpoint SHALL respond in < 100ms (99th percentile)
**PERF-004**: Update endpoint SHALL respond in < 200ms (99th percentile)
**PERF-005**: Delete endpoint SHALL respond in < 150ms (99th percentile)
**PERF-006**: Database SHALL have indexes on: company_id, created_at, name
**PERF-007**: List queries SHALL use database-level pagination (LIMIT/OFFSET)

### Constraints (CON-xxx)

**CON-001**: API version prefix MUST be `/v0/` (not /v1/ yet)
**CON-002**: All IDs MUST be UUIDs (not integers)
**CON-003**: Dummy name MUST be unique per company (unique constraint)
**CON-004**: Pagination per_page MUST NOT exceed 100 items
**CON-005**: Soft-deleted dummies (is_active=false) MUST NOT appear in list results
**CON-006**: Guardian service name MUST be "template-service"
**CON-007**: Timestamps MUST be stored in UTC

### Guidelines (GUD-xxx)

**GUD-001**: Use UUIDMixin and TimestampMixin for model
**GUD-002**: Create separate schemas: DummySchema, DummyCreateSchema, DummyUpdateSchema
**GUD-003**: Use DummyListResource for GET /dummies and POST /dummies
**GUD-004**: Use DummyResource for GET/PATCH/DELETE /dummies/{id}
**GUD-005**: Place constants in app/constants/dummy_constants.py
**GUD-006**: Log all Guardian authorization failures at WARNING level
**GUD-007**: Return correlation_id in all error responses
**GUD-008**: Use structured logging (JSON) with correlation_id field
**GUD-009**: Log at appropriate levels: INFO (requests), WARNING (auth failures), ERROR (exceptions)
**GUD-010**: Include correlation_id in all Guardian/Identity service calls for distributed tracing

## 4. Interfaces & Data Contracts

### 4.1 GET /v0/dummies - List Dummies

**Endpoint:** `GET /v0/dummies`

**Description:** Retrieve a paginated list of dummies for the authenticated user's company with optional sorting.

#### Path Parameters
None

#### Query Parameters

| Parameter | Type | Required | Default | Description | Validation |
|-----------|------|----------|---------|-------------|------------|
| page | integer | No | 1 | Page number (1-indexed) | min: 1 |
| per_page | integer | No | 20 | Items per page | min: 1, max: 100 |
| sort_by | string | No | created_at | Field to sort by | enum: name, created_at, updated_at |
| sort_order | string | No | desc | Sort direction | enum: asc, desc |

#### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| Cookie | Yes | Must contain `access_token=<JWT>` |
| X-Correlation-ID | No | Request correlation ID (UUID v4). Auto-generated if not provided |

#### Request Body
None

#### Response Schemas

**Success Response (200 OK):**

```json
{
  "data": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Example Dummy",
      "description": "This is an example dummy resource",
      "company_id": "987e6543-e21b-12d3-a456-426614174000",
      "is_active": true,
      "created_at": "2026-01-07T10:00:00Z",
      "updated_at": "2026-01-07T10:00:00Z"
    },
    {
      "id": "223e4567-e89b-12d3-a456-426614174001",
      "name": "Another Dummy",
      "description": null,
      "company_id": "987e6543-e21b-12d3-a456-426614174000",
      "is_active": true,
      "created_at": "2026-01-07T09:30:00Z",
      "updated_at": "2026-01-07T09:30:00Z"
    }
  ],
  "page": 1,
  "per_page": 20,
  "total": 42,
  "total_pages": 3
}
```

**Success Response (200 OK - Empty):**

```json
{
  "data": [],
  "page": 1,
  "per_page": 20,
  "total": 0,
  "total_pages": 0
}
```

**Error Response (401 Unauthorized):**

```json
{
  "message": "Missing or invalid JWT token",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (403 Forbidden):**

```json
{
  "message": "Insufficient permissions to list dummies",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (422 Unprocessable Entity):**

```json
{
  "message": "Validation failed",
  "errors": {
    "per_page": ["Must be less than or equal to 100"]
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Status Codes

| Code | Description | When to Use |
|------|-------------|-------------|
| 200 | OK | Successful retrieval (even if empty) |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | User lacks Guardian LIST permission |
| 422 | Unprocessable Entity | Invalid query parameters |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

---

### 4.2 POST /v0/dummies - Create Dummy

**Endpoint:** `POST /v0/dummies`

**Description:** Create a new dummy resource for the authenticated user's company.

#### Path Parameters
None

#### Query Parameters
None

#### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| Cookie | Yes | Must contain `access_token=<JWT>` |
| Content-Type | Yes | Must be `application/json` |
| X-Correlation-ID | No | Request correlation ID (UUID v4). Auto-generated if not provided |

#### Request Body Schema

```json
{
  "name": {
    "type": "string",
    "required": true,
    "minLength": 3,
    "maxLength": 255,
    "description": "Unique name for the dummy within the company"
  },
  "description": {
    "type": "string",
    "required": false,
    "maxLength": 1000,
    "description": "Optional description"
  }
}
```

**Example Request:**

```json
{
  "name": "My New Dummy",
  "description": "This is a test dummy resource"
}
```

#### Response Schemas

**Success Response (201 Created):**

```json
{
  "data": {
    "id": "323e4567-e89b-12d3-a456-426614174002",
    "name": "My New Dummy",
    "description": "This is a test dummy resource",
    "company_id": "987e6543-e21b-12d3-a456-426614174000",
    "is_active": true,
    "created_at": "2026-01-07T11:00:00Z",
    "updated_at": "2026-01-07T11:00:00Z"
  },
  "message": "Dummy created successfully"
}
```

**Error Response (401 Unauthorized):**

```json
{
  "message": "Missing or invalid JWT token",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (403 Forbidden):**

```json
{
  "message": "Insufficient permissions to create dummies",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (409 Conflict):**

```json
{
  "message": "Dummy with this name already exists in your company",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (422 Unprocessable Entity):**

```json
{
  "message": "Validation failed",
  "errors": {
    "name": ["Field is required"],
    "description": ["Length must be between 0 and 1000"]
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Status Codes

| Code | Description | When to Use |
|------|-------------|-------------|
| 201 | Created | Dummy successfully created |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | User lacks Guardian CREATE permission |
| 409 | Conflict | Dummy name already exists in company |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

---

### 4.3 GET /v0/dummies/{id} - Retrieve Dummy

**Endpoint:** `GET /v0/dummies/{id}`

**Description:** Retrieve a single dummy by ID. Must belong to authenticated user's company.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Yes | Dummy unique identifier |

#### Query Parameters
None

#### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| Cookie | Yes | Must contain `access_token=<JWT>` |
| X-Correlation-ID | No | Request correlation ID (UUID v4). Auto-generated if not provided |

#### Request Body
None

#### Response Schemas

**Success Response (200 OK):**

```json
{
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Example Dummy",
    "description": "This is an example dummy resource",
    "company_id": "987e6543-e21b-12d3-a456-426614174000",
    "is_active": true,
    "created_at": "2026-01-07T10:00:00Z",
    "updated_at": "2026-01-07T10:00:00Z"
  }
}
```

**Error Response (401 Unauthorized):**

```json
{
  "message": "Missing or invalid JWT token",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (403 Forbidden):**

```json
{
  "message": "Insufficient permissions to read this dummy",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (404 Not Found):**

```json
{
  "message": "Dummy not found",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Status Codes

| Code | Description | When to Use |
|------|-------------|-------------|
| 200 | OK | Dummy found and returned |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | User lacks Guardian READ permission |
| 404 | Not Found | Dummy not found or belongs to another company |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

---

### 4.4 PATCH /v0/dummies/{id} - Update Dummy

**Endpoint:** `PATCH /v0/dummies/{id}`

**Description:** Partially update a dummy. Only provided fields are updated. Must belong to authenticated user's company.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Yes | Dummy unique identifier |

#### Query Parameters
None

#### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| Cookie | Yes | Must contain `access_token=<JWT>` |
| Content-Type | Yes | Must be `application/json` |
| X-Correlation-ID | No | Request correlation ID (UUID v4). Auto-generated if not provided |

#### Request Body Schema

```json
{
  "name": {
    "type": "string",
    "required": false,
    "minLength": 3,
    "maxLength": 255,
    "description": "Updated name (must be unique in company)"
  },
  "description": {
    "type": "string",
    "required": false,
    "maxLength": 1000,
    "description": "Updated description (null to clear)"
  },
  "is_active": {
    "type": "boolean",
    "required": false,
    "enum": [false],
    "description": "Active status. Can only be set to false (soft delete). Use DELETE endpoint instead. Cannot reactivate via PATCH."
  }
}
```

**Example Request (Partial Update):**

```json
{
  "name": "Updated Dummy Name"
}
```

**Example Request (Multiple Fields):**

```json
{
  "name": "Completely Updated",
  "description": "New description here",
  "is_active": false
}
```

#### Response Schemas

**Success Response (200 OK):**

```json
{
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Updated Dummy Name",
    "description": "This is an example dummy resource",
    "company_id": "987e6543-e21b-12d3-a456-426614174000",
    "is_active": true,
    "created_at": "2026-01-07T10:00:00Z",
    "updated_at": "2026-01-07T11:30:00Z"
  },
  "message": "Dummy updated successfully"
}
```

**Error Response (401 Unauthorized):**

```json
{
  "message": "Missing or invalid JWT token",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (403 Forbidden):**

```json
{
  "message": "Insufficient permissions to update this dummy",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (404 Not Found):**

```json
{
  "message": "Dummy not found",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (409 Conflict):**

```json
{
  "message": "Dummy with this name already exists in your company",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (422 Unprocessable Entity):**

```json
{
  "message": "Validation failed",
  "errors": {
    "name": ["Length must be between 3 and 255"]
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Status Codes

| Code | Description | When to Use |
|------|-------------|-------------|
| 200 | OK | Dummy successfully updated |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | User lacks Guardian UPDATE permission |
| 404 | Not Found | Dummy not found or belongs to another company |
| 409 | Conflict | Updated name conflicts with existing dummy |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

---

### 4.5 DELETE /v0/dummies/{id} - Delete Dummy

**Endpoint:** `DELETE /v0/dummies/{id}`

**Description:** Soft delete a dummy (set is_active=false). Must belong to authenticated user's company.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | UUID | Yes | Dummy unique identifier |

#### Query Parameters
None

#### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| Cookie | Yes | Must contain `access_token=<JWT>` |
| X-Correlation-ID | No | Request correlation ID (UUID v4). Auto-generated if not provided |

#### Response Schemas

**Success Response (204 No Content):**

No response body. Headers only (X-Correlation-ID, X-RateLimit-*).

**Error Response (401 Unauthorized):**

```json
{
  "message": "Missing or invalid JWT token",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (403 Forbidden):**

```json
{
  "message": "Insufficient permissions to delete this dummy",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (404 Not Found):**

```json
{
  "message": "Dummy not found",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Response (410 Gone):**

```json
{
  "message": "Dummy has already been deleted",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Status Codes

| Code | Description | When to Use |
|------|-------------|-------------|
| 204 | No Content | Dummy successfully deleted (soft delete) |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | User lacks Guardian DELETE permission |
| 404 | Not Found | Dummy not found or belongs to another company |
| 410 | Gone | Dummy has already been soft-deleted (is_active=false) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

---

### Response Headers (All Endpoints)

| Header | Description | When |
|--------|-------------|------|
| Content-Type | application/json | All responses |
| X-Correlation-ID | Request correlation ID (from request or auto-generated) | All responses (success & errors) |
| X-RateLimit-Limit | Maximum requests per window | All responses |
| X-RateLimit-Remaining | Remaining requests in current window | All responses |
| X-RateLimit-Reset | Unix timestamp when limit resets | All responses |

**Example Response Headers:**
```
Content-Type: application/json
X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704628800
```

## 5. Acceptance Criteria

### AC-001: List Dummies with Pagination
- **Given** user has valid JWT token and Guardian LIST permission
- **And** company has 50 dummies
- **When** GET /v0/dummies?page=2&per_page=20 is called
- **Then** response status is 200
- **And** response contains 20 dummies (items 21-40)
- **And** pagination metadata shows page=2, per_page=20, total=50, total_pages=3
- **And** only dummies with is_active=true are returned
- **And** all dummies have matching company_id from JWT

### AC-002: Create Dummy Successfully
- **Given** user has valid JWT token and Guardian CREATE permission
- **When** POST /v0/dummies with valid data
- **Then** response status is 201
- **And** response contains new dummy with generated UUID
- **And** dummy.company_id matches company_id from JWT
- **And** dummy.is_active is true by default
- **And** created_at and updated_at are set to current UTC time

### AC-003: Create Duplicate Name in Same Company
- **Given** dummy with name "Test" exists in company A
- **And** user belongs to company A
- **When** POST /v0/dummies with name "Test"
- **Then** response status is 409 Conflict
- **And** error message indicates name already exists

### AC-004: Create Same Name in Different Company (Allowed)
- **Given** dummy with name "Test" exists in company A
- **And** user belongs to company B
- **When** POST /v0/dummies with name "Test"
- **Then** response status is 201
- **And** dummy is created successfully in company B

### AC-005: Retrieve Dummy from Same Company
- **Given** dummy with id=123 exists in company A
- **And** user belongs to company A with READ permission
- **When** GET /v0/dummies/123
- **Then** response status is 200
- **And** response contains full dummy data

### AC-006: Retrieve Dummy from Different Company
- **Given** dummy with id=123 exists in company A
- **And** user belongs to company B
- **When** GET /v0/dummies/123
- **Then** response status is 404 Not Found
- **And** no company information is leaked

### AC-007: Update Dummy Partially
- **Given** dummy exists with name="Old" and description="Old desc"
- **And** user has UPDATE permission
- **When** PATCH /v0/dummies/{id} with {"name": "New"}
- **Then** response status is 200
- **And** dummy.name is "New"
- **And** dummy.description remains "Old desc" (unchanged)
- **And** dummy.updated_at is updated to current time

### AC-008: Soft Delete Dummy
- **Given** dummy exists with is_active=true
- **And** user has DELETE permission
- **When** DELETE /v0/dummies/{id}
- **Then** response status is 200
- **And** dummy.is_active is set to false
- **And** dummy no longer appears in GET /v0/dummies list
- **And** dummy can still be retrieved by ID (returns is_active=false)

### AC-009: Guardian Authorization Failure
- **Given** user has valid JWT token
- **And** Guardian denies CREATE permission
- **When** POST /v0/dummies with valid data
- **Then** response status is 403 Forbidden
- **And** no dummy is created
- **And** authorization failure is logged

### AC-010: Invalid JWT Token
- **Given** no JWT token provided in cookie
- **When** any endpoint is called
- **Then** response status is 401 Unauthorized
- **And** response contains authentication error message

### AC-011: Pagination with Sorting
- **Given** company has dummies with names "C", "A", "B"
- **When** GET /v0/dummies?sort_by=name&sort_order=asc
- **Then** response status is 200
- **And** dummies are returned in order: "A", "B", "C"

### AC-012: Rate Limiting
- **Given** user makes 100 requests in 1 minute
- **When** 101st request is made
- **Then** response status is 429 Too Many Requests
- **And** X-RateLimit-Reset header indicates when limit resets

## 6. Test Automation Strategy

**Test Levels:**
- Unit tests: Model validation, schema serialization, business logic
- Integration tests: Database operations, Guardian integration, full endpoint flows
- End-to-end tests: Complete CRUD workflows with authentication

**Frameworks:**
- pytest for all test levels
- FlaskClient for endpoint testing
- pytest-mock for Guardian mocking in unit tests
- Docker Compose for integration test database

**Test Data Management:**
- Factory pattern for creating test dummies
- Fixtures for JWT tokens with different permissions
- Database transaction rollback after each test
- Separate test database schema

**CI/CD Integration:**
- Run on every commit and PR
- Required for merge approval
- Coverage report in PR comments
- Integration tests run against PostgreSQL container

**Coverage Requirements:**
- Minimum 85% overall code coverage
- 100% coverage for critical paths (authentication, authorization)
- All status codes tested for each endpoint
- All validation rules tested

**Performance Testing:**
- Load test with 100 concurrent users
- Verify response times meet requirements
- Test pagination with 10,000 records
- Measure Guardian integration latency

## 7. Logging Strategy

### Log Levels

| Level | When to Use | Examples |
|-------|-------------|----------|
| INFO | Normal operations | Request received, request completed, Guardian check passed |
| WARNING | Recoverable issues | Guardian denied permission, validation failed, rate limit exceeded |
| ERROR | Unexpected failures | Database connection failed, Guardian service unreachable, unhandled exception |
| DEBUG | Development/troubleshooting | Request/response bodies, SQL queries, Guardian request/response |

### Required Log Fields

All log entries MUST include (structured JSON format):

```json
{
  "timestamp": "2026-01-07T12:00:00.123Z",
  "level": "INFO",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-uuid",
  "company_id": "company-uuid",
  "method": "POST",
  "path": "/v0/dummies",
  "status_code": 201,
  "duration_ms": 45,
  "message": "Dummy created successfully"
}
```

### Log Examples by Operation

**Successful Request:**
```json
{
  "timestamp": "2026-01-07T12:00:00.123Z",
  "level": "INFO",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "company_id": "company-456",
  "method": "POST",
  "path": "/v0/dummies",
  "status_code": 201,
  "duration_ms": 45,
  "message": "Request completed",
  "dummy_id": "dummy-789"
}
```

**Authorization Failure:**
```json
{
  "timestamp": "2026-01-07T12:01:00.456Z",
  "level": "WARNING",
  "correlation_id": "650e8400-e29b-41d4-a716-446655440001",
  "user_id": "user-123",
  "company_id": "company-456",
  "method": "POST",
  "path": "/v0/dummies",
  "status_code": 403,
  "duration_ms": 120,
  "message": "Guardian denied CREATE permission",
  "guardian_reason": "no_permission",
  "guardian_operation": "CREATE",
  "guardian_resource": "dummies"
}
```

**Service Error:**
```json
{
  "timestamp": "2026-01-07T12:02:00.789Z",
  "level": "ERROR",
  "correlation_id": "750e8400-e29b-41d4-a716-446655440002",
  "user_id": "user-123",
  "company_id": "company-456",
  "method": "GET",
  "path": "/v0/dummies",
  "status_code": 500,
  "duration_ms": 5000,
  "message": "Guardian service timeout",
  "error_type": "ConnectionTimeout",
  "service": "guardian",
  "stack_trace": "..."
}
```

### Distributed Tracing

**Correlation ID Propagation:**
- Accept X-Correlation-ID from incoming request
- Generate UUID v4 if not provided
- Include in all outgoing service calls (Guardian, Identity, etc.)
- Return in X-Correlation-ID response header
- Log in every log entry for the request lifecycle

**Service Call Example:**
```python
# Propagate correlation_id to Guardian
headers = {
    "Authorization": "Bearer <token>",
    "X-Correlation-ID": correlation_id
}
response = requests.post(guardian_url, headers=headers, json=payload)
```

## 8. Rationale & Context

**Why soft delete instead of hard delete?**
- Maintains audit trail and data history
- Allows potential data recovery
- Prevents foreign key constraint violations
- Industry best practice for user-facing deletions

**Why unique constraint on (name, company_id)?**
- Prevents duplicate names within a company
- Allows same names across different companies (multi-tenancy)
- Provides clear validation error for users
- Database-enforced consistency

**Why company_id in all queries?**
- Enforces multi-tenancy isolation at database level
- Prevents accidental data leaks between companies
- Performance: allows index on company_id
- Security defense in depth

**Why separate Guardian check for each operation?**
- Fine-grained permission control (user can LIST but not CREATE)
- Follows principle of least privilege
- Allows role-based access control
- Audit trail of authorization decisions

**Why pagination default to 20 items?**
- Balance between user experience and performance
- Prevents accidentally loading thousands of records
- Standard REST API practice
- Allows fast response times

**Why return 404 for cross-company access?**
- Prevents information disclosure (dummy exists or not)
- Consistent with "not found" from user perspective
- Security best practice (don't leak existence)
- Simpler client error handling

## 9. Dependencies & External Integrations

### External Systems
- **EXT-001**: Guardian Service - Authorization service checking permissions
  - Endpoint: `/check-access`
  - Required for all CRUD operations
  - Context includes: service="template-service", resource="dummies", operation, company_id, dummy_id

- **EXT-002**: Identity Service - JWT token validation
  - Validates JWT signature and expiration
  - Provides user_id, company_id, email claims

### Infrastructure Dependencies
- **INF-001**: PostgreSQL Database - Primary data store
  - Table: dummies
  - Indexes: company_id, created_at, (name, company_id) unique

- **INF-002**: Redis (Optional) - Rate limiting storage
  - Tracks request counts per user/IP
  - TTL for rate limit windows

### Technology Platform Dependencies
- **PLT-001**: Flask web framework - HTTP request handling
- **PLT-002**: SQLAlchemy - ORM and database operations
- **PLT-003**: Marshmallow - Schema validation and serialization
- **PLT-004**: Flask-RESTful - Resource class base
- **PLT-005**: Python 3.11+ - Runtime environment

### Data Dependencies
- **DAT-001**: JWT Token - Contains user_id, company_id, email
- **DAT-002**: Guardian Configuration - Service and resource definitions

## 10. Examples & Edge Cases

### Example 1: Complete CRUD Workflow
```bash
# 1. Create dummy
curl -X POST http://localhost:5000/v0/dummies \
  -H "Content-Type: application/json" \
  -b "access_token=<jwt>" \
  -d '{"name": "Test Dummy", "description": "Testing"}'

# Response: 201 Created
{
  "data": {
    "id": "abc-123",
    "name": "Test Dummy",
    "description": "Testing",
    "company_id": "company-xyz",
    "is_active": true,
    "created_at": "2026-01-07T12:00:00Z",
    "updated_at": "2026-01-07T12:00:00Z"
  },
  "message": "Dummy created successfully"
}

# 2. List dummies
curl http://localhost:5000/v0/dummies?page=1&per_page=10 \
  -b "access_token=<jwt>"

# Response: 200 OK
{
  "data": [{"id": "abc-123", "name": "Test Dummy", ...}],
  "page": 1,
  "per_page": 10,
  "total": 1,
  "total_pages": 1
}

# 3. Retrieve single dummy
curl http://localhost:5000/v0/dummies/abc-123 \
  -b "access_token=<jwt>"

# Response: 200 OK
{
  "data": {"id": "abc-123", "name": "Test Dummy", ...}
}

# 4. Update dummy
curl -X PATCH http://localhost:5000/v0/dummies/abc-123 \
  -H "Content-Type: application/json" \
  -b "access_token=<jwt>" \
  -d '{"name": "Updated Name"}'

# Response: 200 OK
{
  "data": {"id": "abc-123", "name": "Updated Name", ...},
  "message": "Dummy updated successfully"
}

# 5. Delete dummy
curl -X DELETE http://localhost:5000/v0/dummies/abc-123 \
  -b "access_token=<jwt>"

# Response: 200 OK
{
  "message": "Dummy deleted successfully"
}

# 6. Verify deletion (soft delete)
curl http://localhost:5000/v0/dummies \
  -b "access_token=<jwt>"

# Response: 200 OK (deleted dummy not in list)
{
  "data": [],
  "page": 1,
  "per_page": 20,
  "total": 0,
  "total_pages": 0
}
```

### Example 2: Validation Errors
```bash
# Missing required field
curl -X POST http://localhost:5000/v0/dummies \
  -H "Content-Type: application/json" \
  -b "access_token=<jwt>" \
  -d '{"description": "No name provided"}'

# Response: 422 Unprocessable Entity
{
  "message": "Validation failed",
  "errors": {
    "name": ["Field is required"]
  },
  "correlation_id": "xyz-789"
}

# Name too short
curl -X POST http://localhost:5000/v0/dummies \
  -H "Content-Type: application/json" \
  -b "access_token=<jwt>" \
  -d '{"name": "AB"}'

# Response: 422 Unprocessable Entity
{
  "message": "Validation failed",
  "errors": {
    "name": ["Length must be between 3 and 255"]
  },
  "correlation_id": "xyz-790"
}
```

### Example 3: Multi-Tenancy Isolation
```bash
# User A in Company 1 creates dummy
curl -X POST http://localhost:5000/v0/dummies \
  -H "Content-Type: application/json" \
  -b "access_token=<jwt-company-1>" \
  -d '{"name": "Company 1 Dummy"}'

# Response: 201 Created (id=123, company_id=company-1)

# User B in Company 2 tries to access Company 1's dummy
curl http://localhost:5000/v0/dummies/123 \
  -b "access_token=<jwt-company-2>"

# Response: 404 Not Found (cross-company access blocked)
{
  "message": "Dummy not found",
  "correlation_id": "xyz-791"
}

# User B lists dummies (sees only their company's data)
curl http://localhost:5000/v0/dummies \
  -b "access_token=<jwt-company-2>"

# Response: 200 OK (empty, no Company 1 data visible)
{
  "data": [],
  "page": 1,
  "per_page": 20,
  "total": 0,
  "total_pages": 0
}
```

### Edge Case 1: Guardian Service Down
```bash
curl -X POST http://localhost:5000/v0/dummies \
  -H "Content-Type: application/json" \
  -b "access_token=<jwt>" \
  -d '{"name": "Test"}'

# Response: 500 Internal Server Error
{
  "message": "Authorization service unavailable",
  "correlation_id": "xyz-792"
}
```

### Edge Case 2: Pagination Beyond Last Page
```bash
# Only 10 dummies exist, request page 5
curl "http://localhost:5000/v0/dummies?page=5&per_page=20" \
  -b "access_token=<jwt>"

# Response: 200 OK (empty page, valid request)
{
  "data": [],
  "page": 5,
  "per_page": 20,
  "total": 10,
  "total_pages": 1
}
```

### Edge Case 3: Concurrent Update Conflict
```bash
# User A and User B update same dummy simultaneously
# Last write wins, both succeed with 200 OK
# updated_at timestamp shows most recent update
```

### Edge Case 4: Invalid UUID Format
```bash
curl http://localhost:5000/v0/dummies/not-a-uuid \
  -b "access_token=<jwt>"

# Response: 404 Not Found (Flask route doesn't match)
# Or 422 Unprocessable Entity if route matches but UUID validation fails
```

## 11. Validation Criteria

- **VAL-001**: All endpoints return valid JSON (validated with jsonschema)
- **VAL-002**: JWT authentication rejects missing or invalid tokens with 401
- **VAL-003**: Guardian authorization failures return 403 with clear message
- **VAL-004**: Multi-tenancy isolation: users never see other companies' data
- **VAL-005**: Pagination calculates total_pages correctly: ceil(total / per_page)
- **VAL-006**: Soft delete sets is_active=false and removes from list results
- **VAL-007**: Unique constraint (name, company_id) enforced at database level
- **VAL-008**: All validation errors return 422 with field-specific messages
- **VAL-009**: All timestamps stored and returned in UTC ISO 8601 format
- **VAL-010**: Response times meet performance requirements (PERF-001 to PERF-005)
- **VAL-011**: Rate limiting enforces 100 requests per minute per user
- **VAL-012**: Correlation ID present in all error responses

## 11. Related Specifications / Further Reading

- spec/schema-api-health-endpoints.md - Health check endpoints
- spec/schema-api-metrics-endpoint.md - Prometheus metrics endpoint
- [Guardian Service API Documentation](../docs/guardian-integration.md)
- [Identity Service JWT Claims](../docs/jwt-authentication.md)
- [REST API Best Practices](https://restfulapi.net/)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [UUID v4 Specification](https://datatracker.ietf.org/doc/html/rfc4122)
