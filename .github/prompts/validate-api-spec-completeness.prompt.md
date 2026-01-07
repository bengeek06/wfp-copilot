---
description: "Validate that a markdown API specification is complete, consistent, and follows all standards and best practices"
agent: "specification"
tools: ["edit", "search", "search/codebase", "web/fetch"]
---

# Validate API Specification Completeness

You are an expert in API specification quality assurance, REST best practices, and technical documentation standards.

## Task

Perform a comprehensive quality check on a markdown API specification file to ensure it is:
- **Complete**: All required sections present with sufficient detail
- **Consistent**: No contradictions between sections
- **Compliant**: Follows REST standards and project conventions
- **Secure**: Security requirements properly defined
- **Testable**: Sufficient detail for implementation and testing
- **Documented**: Examples and edge cases covered

## Input Variables

- `${input:specFile}` - Path to specification file to validate
- `${input:strictMode:true}` - Enforce strict validation (fail on warnings)
- `${input:outputFormat:markdown}` - Output format: markdown, json, or console

## Validation Workflow

### 1. Structural Validation

Check presence and completeness of all required sections:

#### Section 1: Header Metadata ✓/✗
```
- [ ] Title is descriptive and follows naming convention
- [ ] Status is one of: draft, review, approved, deprecated
- [ ] Owner is assigned
- [ ] Version is semantic (MAJOR.MINOR.PATCH)
- [ ] Created/Updated dates are ISO 8601
- [ ] Tags are relevant
```

**Naming Convention:**
- Format: `[AREA]-api-[resource]-[operation].md`
- Example: `schema-api-user-create.md`

#### Section 2: Introduction & Purpose ✓/✗
```
- [ ] Context explains WHY this API exists
- [ ] Business value is clear
- [ ] Target users identified
- [ ] Related systems mentioned
- [ ] Links to parent/related specs provided
```

**Quality Check:**
- Min 2 paragraphs
- No generic filler text
- Specific use cases mentioned

#### Section 3: Requirements ✓/✗

Verify presence of each requirement category:

**Functional Requirements (REQ-xxx):**
```
- [ ] At least 3 functional requirements defined
- [ ] Each REQ has unique ID (REQ-001, REQ-002...)
- [ ] Each REQ uses SHALL/SHOULD/MAY keywords
- [ ] Each REQ is testable/measurable
- [ ] CRUD operations covered where applicable
```

**Security Requirements (SEC-xxx):**
```
- [ ] Authentication specified (JWT, API key, etc.)
- [ ] Authorization rules defined
- [ ] Rate limiting configured
- [ ] Input validation requirements stated
- [ ] PII/sensitive data handling defined
```

**Performance Requirements (PERF-xxx):**
```
- [ ] Response time SLA defined
- [ ] Throughput expectations stated
- [ ] Pagination parameters defined
- [ ] Rate limits specified (requests/minute)
```

**Constraints (CON-xxx):**
```
- [ ] Data size limits specified
- [ ] Timeout values defined
- [ ] Dependency services identified
- [ ] Error handling strategy defined
```

**Consistency Checks:**
```
- [ ] No duplicate requirement IDs
- [ ] All IDs follow pattern: [TYPE]-[XXX]
- [ ] Requirements don't contradict each other
- [ ] All SHALL requirements are critical
```

#### Section 4: Interfaces & Data Contracts ✓/✗

**HTTP Endpoint:**
```
- [ ] Path follows REST conventions: /{version}/{resource}/{id}
- [ ] HTTP method is appropriate (GET/POST/PUT/PATCH/DELETE)
- [ ] Version prefix present (v0, v1...)
- [ ] Resource name is plural for collections
- [ ] Path parameters use {paramName} syntax
```

**Parameters:**
```
- [ ] Path parameters table complete (Name, Type, Required, Description, Example)
- [ ] Query parameters documented (for GET/LIST)
- [ ] Pagination params for collections (page, per_page)
- [ ] Filter params for search
- [ ] All types are valid: string, integer, boolean, UUID, enum
- [ ] Required field accurate
- [ ] Examples provided for all parameters
```

**Request Schema:**
```
- [ ] JSON structure provided
- [ ] All fields have type
- [ ] Required fields marked
- [ ] Constraints defined (minLength, maxLength, min, max, pattern)
- [ ] Nested objects properly structured
- [ ] Enums have allowed values listed
- [ ] Default values specified where applicable
- [ ] Example request provided
```

**Response Schemas:**
```
- [ ] All status codes documented (2xx, 4xx, 5xx)
- [ ] Success response (200/201) schema complete
- [ ] Error response format consistent
- [ ] Pagination metadata for lists (page, total, total_pages)
- [ ] Response wrapper consistent (data, message, errors)
- [ ] Example responses for all status codes
```

**Status Codes:**
```
- [ ] 200 OK for successful GET/PATCH/DELETE
- [ ] 201 Created for successful POST
- [ ] 204 No Content for DELETE (if no response body)
- [ ] 400 Bad Request for validation errors
- [ ] 401 Unauthorized for auth failures
- [ ] 403 Forbidden for permission issues
- [ ] 404 Not Found for missing resources
- [ ] 409 Conflict for duplicate/constraint violations
- [ ] 429 Too Many Requests for rate limit
- [ ] 500 Internal Server Error for server issues
```

**Headers:**
```
- [ ] Request headers documented (Authorization, Content-Type, X-Correlation-ID)
- [ ] Response headers documented (X-Correlation-ID, X-RateLimit-*)
- [ ] Optional vs required headers marked
```

#### Section 5: Acceptance Criteria ✓/✗

**Structure:**
```
- [ ] At least 3 scenarios defined
- [ ] Each uses Given-When-Then format
- [ ] Covers happy path
- [ ] Covers error cases
- [ ] Covers edge cases
```

**Quality:**
```
- [ ] Given: Context is clear and complete
- [ ] When: Action is specific
- [ ] Then: Expected outcome is measurable
- [ ] Each scenario maps to a requirement (REQ-xxx, SEC-xxx, etc.)
```

**Coverage:**
```
- [ ] Authentication tested
- [ ] Authorization tested
- [ ] Validation tested
- [ ] Success case tested
- [ ] Rate limiting tested (if PERF requirement exists)
- [ ] Pagination tested (for list endpoints)
```

#### Section 6: Business Rules ✓/✗
```
- [ ] Domain-specific rules documented
- [ ] State transitions defined
- [ ] Validation rules beyond schema (e.g., "start_date < end_date")
- [ ] Uniqueness constraints specified
- [ ] Cross-field validations documented
```

#### Section 7: Dependencies ✓/✗
```
- [ ] Internal services listed (Guardian, Identity, etc.)
- [ ] External APIs documented
- [ ] Database requirements specified
- [ ] File storage needs identified
- [ ] Message queues/events documented
```

#### Section 8: Edge Cases & Error Handling ✓/✗

**Edge Cases:**
```
- [ ] At least 3 edge cases listed
- [ ] Empty/null values handled
- [ ] Boundary values tested (min/max)
- [ ] Large datasets considered
- [ ] Concurrent access scenarios
```

**Error Scenarios:**
```
- [ ] Validation errors detailed
- [ ] Authentication failures covered
- [ ] Authorization failures covered
- [ ] Not found scenarios
- [ ] Conflict scenarios
- [ ] Timeout/service unavailable
```

**Error Response Format:**
```
- [ ] Consistent error structure defined
- [ ] Error codes/messages documented
- [ ] Field-level errors format specified
- [ ] Correlation ID for tracing included
```

#### Section 9: Examples ✓/✗

**Request Examples:**
```
- [ ] Valid request example provided
- [ ] Invalid request example (for validation)
- [ ] Curl command provided
- [ ] Examples match request schema exactly
```

**Response Examples:**
```
- [ ] Success response example
- [ ] Error response examples (400, 401, 404, etc.)
- [ ] Examples match response schemas exactly
- [ ] Realistic data (no placeholder values like "xxx")
```

**Quality:**
```
- [ ] JSON is valid and properly formatted
- [ ] UUIDs are valid format
- [ ] Timestamps are ISO 8601
- [ ] Enum values match defined values
- [ ] Nested objects complete
```

### 2. REST Best Practices Validation

**Naming Conventions:**
```
- [ ] Resource names are nouns (not verbs)
- [ ] Plural for collections: /users, /projects
- [ ] Lowercase with hyphens: /user-profiles (not /userProfiles)
- [ ] No trailing slashes
- [ ] Query params use snake_case
```

**HTTP Method Usage:**
```
- [ ] GET: Read operations, idempotent, no body
- [ ] POST: Create new resource, returns 201
- [ ] PUT: Replace entire resource
- [ ] PATCH: Partial update
- [ ] DELETE: Remove resource, idempotent
```

**Idempotency:**
```
- [ ] GET/PUT/DELETE are idempotent
- [ ] POST is NOT idempotent (creates new each time)
- [ ] PATCH idempotency specified
```

**Response Consistency:**
```
- [ ] Single resource: {data: {resource}}
- [ ] Collection: {data: [{resources}], page, total}
- [ ] Error: {message, errors, correlation_id}
- [ ] Same structure across all endpoints
```

**Filtering & Pagination:**
```
- [ ] Collections support pagination (page, per_page)
- [ ] Search parameter for filtering
- [ ] Sorting parameters (sort_by, sort_order)
- [ ] Filter parameters use snake_case
```

### 3. Security Validation

**Authentication:**
```
- [ ] Auth method specified (JWT recommended)
- [ ] Token location defined (Header: Authorization: Bearer <token>)
- [ ] Token validation requirements stated
- [ ] Unauthenticated access returns 401
```

**Authorization:**
```
- [ ] Permission requirements documented
- [ ] Operation-level access control (READ, CREATE, UPDATE, DELETE)
- [ ] Resource-level access control (user_id, company_id)
- [ ] Forbidden access returns 403
```

**Input Validation:**
```
- [ ] All inputs validated
- [ ] String length limits enforced
- [ ] Numeric ranges validated
- [ ] Format validation (UUID, email, URL)
- [ ] Injection prevention mentioned
```

**Rate Limiting:**
```
- [ ] Rate limit defined (requests per minute)
- [ ] Rate limit headers specified
- [ ] 429 response documented
- [ ] Retry-After header included
```

**Data Protection:**
```
- [ ] PII handling specified
- [ ] Sensitive fields identified
- [ ] Data retention policy mentioned
- [ ] HTTPS/TLS required
```

### 4. Data Consistency Validation

**Cross-Section Consistency:**
```
- [ ] Request schema matches examples
- [ ] Response schema matches examples
- [ ] Parameters match endpoint definition
- [ ] Requirements align with acceptance criteria
- [ ] Status codes match error scenarios
```

**Type Consistency:**
```
- [ ] UUIDs consistently typed as UUID (not string)
- [ ] Dates consistently ISO 8601 format
- [ ] Booleans not using 0/1 or "true"/"false" strings
- [ ] Integers not using strings
- [ ] Same field has same type everywhere
```

**Naming Consistency:**
```
- [ ] Field names use snake_case consistently
- [ ] Same concept uses same field name (created_at not createdAt)
- [ ] Abbreviations avoided or consistent
```

### 5. Implementation Readiness Check

**Developer Readiness:**
```
- [ ] Sufficient detail to implement without ambiguity
- [ ] Database schema inferable from data model
- [ ] Validation rules can be coded directly
- [ ] Error messages can be used as-is
- [ ] Test cases can be automated from AC
```

**Missing Information Flags:**
```
- [ ] No "TBD" or "TODO" in critical sections
- [ ] No ambiguous terms like "appropriate", "reasonable"
- [ ] No missing examples
- [ ] No undefined references
```

## Validation Output

Generate comprehensive report:

### Summary Section

```markdown
## Validation Report: [spec-file-name.md]

**Overall Status**: ✅ PASS | ⚠️ WARNING | ❌ FAIL

**Validation Date**: 2025-01-29T10:30:00Z

**Scores**:
- Structural Completeness: 95% (38/40 checks passed)
- REST Compliance: 100% (12/12 checks passed)
- Security Standards: 90% (9/10 checks passed)
- Consistency: 85% (17/20 checks passed)
- Implementation Readiness: 80% (8/10 checks passed)

**Overall Quality Score**: 90% (84/92 checks passed)
```

### Issues by Severity

**❌ Errors (Must Fix)**:
```
1. [SEC-003] Missing authentication requirement
   Location: Section 3 - Requirements
   Fix: Add "SEC-003: Endpoint SHALL require valid JWT authentication"

2. [SCHEMA] Request schema missing required field: company_id
   Location: Section 4 - Request Schema
   Fix: Add company_id field with type UUID and required: true
```

**⚠️ Warnings (Should Fix)**:
```
1. [NAMING] Resource name should be plural: /user → /users
   Location: Section 4 - HTTP Endpoint
   Fix: Change endpoint path to /{version}/users/{id}

2. [EXAMPLE] Example request contains placeholder "xxx"
   Location: Section 9 - Examples
   Fix: Replace with realistic value
```

**ℹ️ Info (Nice to Have)**:
```
1. [PERF] No performance requirements defined
   Location: Section 3 - Requirements
   Suggestion: Add PERF-001 for response time SLA

2. [DOCS] Business rules section is minimal
   Location: Section 6 - Business Rules
   Suggestion: Add domain-specific validation rules
```

### Detailed Findings

For each issue, provide:
```markdown
### [ERROR-001] Missing Security Requirement

**Severity**: ❌ Error  
**Category**: Security  
**Location**: Section 3, line 45  
**Current State**:
```text
(empty - no SEC requirements)
```

**Expected State**:
```text
#### Security Requirements (SEC-xxx)

- **SEC-001**: Endpoint SHALL require valid JWT authentication
- **SEC-002**: Endpoint SHALL validate user has READ permission via Guardian
- **SEC-003**: Endpoint SHALL enforce rate limit of 100 requests per minute
```

**Impact**: Implementation will be insecure without auth requirements

**Fix Instructions**:
1. Add Security Requirements subsection to Section 3
2. Define at least SEC-001 (authentication) and SEC-002 (authorization)
3. Add SEC-003 for rate limiting
4. Reference SEC requirements in acceptance criteria
```

### Compliance Summary

```markdown
## REST API Standards Compliance

✅ PASS: Resource naming conventions  
✅ PASS: HTTP method semantics  
✅ PASS: Status code usage  
⚠️ WARN: Pagination parameters incomplete (missing total_pages)  
✅ PASS: Error response format  
✅ PASS: Idempotency considerations  
```

```markdown
## Security Standards Compliance

✅ PASS: Authentication method specified  
⚠️ WARN: Authorization rules incomplete  
✅ PASS: Input validation requirements  
❌ FAIL: Rate limiting not defined  
✅ PASS: HTTPS requirement stated  
```

### Actionable Recommendations

Priority-ordered list:

```markdown
## Recommended Actions

### High Priority (Must Fix Before Implementation)
1. ❌ Add missing security requirements (SEC-001, SEC-002, SEC-003)
2. ❌ Fix request schema: add company_id field
3. ❌ Add rate limiting requirement and response headers

### Medium Priority (Should Fix Before Review)
4. ⚠️ Change endpoint path to plural: /users
5. ⚠️ Add pagination metadata to list response
6. ⚠️ Complete authorization rules in business logic section

### Low Priority (Enhancements)
7. ℹ️ Add performance SLA requirements
8. ℹ️ Expand business rules section
9. ℹ️ Add more edge case scenarios
```

## Output Formats

### Markdown (Default)
Complete report as markdown with sections, checklists, and code blocks.

### JSON
```json
{
  "spec_file": "schema-api-user-create.md",
  "validation_date": "2025-01-29T10:30:00Z",
  "overall_status": "warning",
  "scores": {
    "structural": 0.95,
    "rest_compliance": 1.0,
    "security": 0.9,
    "consistency": 0.85,
    "implementation_readiness": 0.8,
    "overall": 0.9
  },
  "checks_passed": 84,
  "checks_total": 92,
  "issues": [
    {
      "id": "SEC-001",
      "severity": "error",
      "category": "security",
      "message": "Missing authentication requirement",
      "location": {"section": 3, "line": 45},
      "fix": "Add SEC-xxx requirement for JWT auth"
    }
  ],
  "recommendations": [...]
}
```

### Console
Colorized output for terminal:
```
✅ VALIDATION PASSED with warnings

📊 Quality Score: 90% (84/92)

❌ 3 Errors | ⚠️ 5 Warnings | ℹ️ 2 Info

Errors:
  1. [SEC] Missing authentication requirement (section 3)
  2. [SCHEMA] Missing required field: company_id (section 4)
  ...
```

## Quality Thresholds

**Pass Criteria** (strictMode=false):
- Overall score ≥ 70%
- No critical errors in security/schema
- All required sections present

**Strict Pass Criteria** (strictMode=true):
- Overall score ≥ 90%
- Zero errors
- All warnings addressed
- Complete examples

## Example Usage

```bash
# In Copilot Chat
/validate-api-spec-completeness

# Prompts for:
Spec file: spec/schema-api-user-create.md
Strict mode: true (default)
Output format: markdown (default)

# Generates:
📋 Validation Report

Overall Status: ⚠️ WARNING
Quality Score: 85%

❌ 2 Errors
⚠️ 3 Warnings
ℹ️ 1 Info

[Detailed report follows...]
```

## Integration with CI/CD

The validation can be automated:

```yaml
# .github/workflows/validate-specs.yml
- name: Validate API Specs
  run: |
    for spec in spec/**/*.md; do
      copilot-cli prompt validate-api-spec-completeness \
        --spec-file "$spec" \
        --strict-mode true \
        --output-format json > "validation-${spec}.json"
    done
```

**Fail build if**:
- Any errors found
- Overall score < 90%
- Security requirements missing

## Quality Checklist

After validation:

- [ ] All errors fixed
- [ ] All warnings reviewed
- [ ] Security requirements complete
- [ ] Examples match schemas exactly
- [ ] REST best practices followed
- [ ] Acceptance criteria testable
- [ ] Implementation ready
- [ ] Documentation complete
- [ ] OpenAPI can be generated
- [ ] Ready for peer review
