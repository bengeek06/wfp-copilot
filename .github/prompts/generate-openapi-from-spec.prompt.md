---
description: "Convert a markdown API specification into a valid OpenAPI 3.x YAML file with complete paths, schemas, and documentation"
agent: "agent"
tools: ["edit", "search", "search/codebase", "web/fetch", "execute/getTerminalOutput", "execute/runInTerminal", "read/terminalLastCommand", "read/terminalSelection", "read/problems"]
---

# Generate OpenAPI from Specification

You are an expert in OpenAPI 3.x specification design and automated API documentation generation from structured markdown specifications.

## Task

Convert a markdown API specification file from `/spec/` directory into a complete, valid OpenAPI 3.x YAML specification file with:
- Parsed paths and operations from markdown
- Extracted request/response schemas
- Security definitions
- Complete documentation
- Validation against openapi-spec-validator
- Generation of HTML documentation

## Input Variables

- `${input:specFile}` - Path to markdown specification file
- `${input:outputFile:openapi/spec.yaml}` - Output OpenAPI YAML file path
- `${input:apiVersion:v0}` - API version prefix
- `${input:validate:true}` - Validate generated OpenAPI spec

## Workflow

### 1. Read and Parse Specification

Read the markdown specification file and extract:

**From Section 4 (Interfaces & Data Contracts)**:
- Endpoint path and HTTP method
- Path parameters with types and descriptions
- Query parameters with defaults and constraints
- Request body schema (JSON structure)
- Response schemas for each status code
- Headers (request and response)

**From Section 3 (Requirements)**:
- Security requirements → security definitions
- Rate limiting → x-ratelimit extension
- Validation constraints → schema validations

**From Section 5 (Acceptance Criteria)**:
- Operation descriptions
- Status code conditions

**From Section 9 (Examples)**:
- Request/response examples for schemas

### 2. Generate OpenAPI Structure

Create complete OpenAPI 3.1.0 YAML with all standard sections:

```yaml
openapi: 3.1.0

info:
  title: [Extracted from spec title]
  version: [Extracted from spec version or default to 1.0.0]
  description: |
    [Extracted from Introduction and Purpose sections]
  contact:
    name: [From owner field]
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.example.com/{version}
    description: Production API
    variables:
      version:
        default: ${apiVersion}
        enum:
          - v0
          - v1
  - url: https://staging-api.example.com/{version}
    description: Staging API
    variables:
      version:
        default: ${apiVersion}
  - url: http://localhost:5000/{version}
    description: Local development
    variables:
      version:
        default: ${apiVersion}

tags:
  - name: [Resource name from spec]
    description: [From Introduction section]

paths:
  [Generated from Section 4]

components:
  schemas:
    [Generated from request/response schemas]
  
  responses:
    [Common error responses]
  
  parameters:
    [Reusable parameters]
  
  securitySchemes:
    [From SEC-xxx requirements]
  
  headers:
    [Common headers like correlation-id, rate-limit]

security:
  - bearerAuth: []

x-ratelimit-limit: [From PERF-xxx requirements]
x-correlation-id: true
```

### 3. Parse Path Operation

For each endpoint in specification:

```yaml
paths:
  /${apiVersion}/[resource-path]:
    [http-method]:
      summary: [From operation description]
      description: |
        [From Purpose section and AC criteria]
      operationId: [methodVerbResourceName, e.g., getUserById]
      tags:
        - [Resource name]
      
      parameters:
        # Path parameters
        - name: [param-name]
          in: path
          required: true
          description: [From table]
          schema:
            type: [From table]
            format: [uuid, date-time, etc.]
          example: [From examples section]
        
        # Query parameters (for GET)
        - name: page
          in: query
          description: Page number for pagination
          required: false
          schema:
            type: integer
            minimum: 1
            default: 1
        
        - name: per_page
          in: query
          description: Items per page
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/[ResourceName]Create'
            examples:
              default:
                summary: Example request
                value: [From examples section]
      
      responses:
        '200':
          description: [From status code table]
          headers:
            X-Correlation-ID:
              $ref: '#/components/headers/X-Correlation-ID'
            X-RateLimit-Limit:
              $ref: '#/components/headers/X-RateLimit-Limit'
            X-RateLimit-Remaining:
              $ref: '#/components/headers/X-RateLimit-Remaining'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/[ResourceName]Response'
              examples:
                default:
                  summary: Successful response
                  value: [From examples section]
        
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
      
      security:
        - bearerAuth: []
      
      x-rate-limit:
        limit: [From rate limiting requirements]
        window: 60
```

### 4. Generate Component Schemas

Convert JSON schemas from specification to OpenAPI schemas:

```yaml
components:
  schemas:
    # Main resource schema (for responses)
    [ResourceName]:
      type: object
      required:
        - id
        - name
        - created_at
        - updated_at
      properties:
        id:
          type: string
          format: uuid
          description: [From schema]
          readOnly: true
        name:
          type: string
          minLength: [From constraints]
          maxLength: [From constraints]
          description: [From schema]
        description:
          type: string
          maxLength: [From constraints]
          nullable: true
          description: [From schema]
        is_active:
          type: boolean
          default: true
          description: [From schema]
        created_at:
          type: string
          format: date-time
          description: Creation timestamp in ISO 8601 format
          readOnly: true
        updated_at:
          type: string
          format: date-time
          description: Last update timestamp in ISO 8601 format
          readOnly: true
      example: [From examples section]
    
    # Create schema (for POST)
    [ResourceName]Create:
      type: object
      required:
        - name
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 255
          description: Resource name
        description:
          type: string
          maxLength: 1000
          nullable: true
        is_active:
          type: boolean
          default: true
      example: [From examples section]
    
    # Update schema (for PATCH)
    [ResourceName]Update:
      type: object
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 255
        description:
          type: string
          maxLength: 1000
          nullable: true
        is_active:
          type: boolean
      minProperties: 1
      example: [From examples section]
    
    # Replace schema (for PUT)
    [ResourceName]Replace:
      type: object
      required:
        - name
        - is_active
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 255
        description:
          type: string
          maxLength: 1000
          nullable: true
        is_active:
          type: boolean
      example: [From examples section]
    
    # List response (for GET collection)
    [ResourceName]List:
      type: object
      required:
        - data
        - page
        - per_page
        - total
        - total_pages
      properties:
        data:
          type: array
          items:
            $ref: '#/components/schemas/[ResourceName]'
        page:
          type: integer
          minimum: 1
        per_page:
          type: integer
          minimum: 1
          maximum: 100
        total:
          type: integer
          minimum: 0
        total_pages:
          type: integer
          minimum: 0
      example: [From examples section]
    
    # Wrapper for single resource response
    [ResourceName]Response:
      type: object
      required:
        - data
      properties:
        data:
          $ref: '#/components/schemas/[ResourceName]'
        message:
          type: string
          description: Optional success message
      example: [From examples section]
    
    # Error response schema
    Error:
      type: object
      required:
        - message
      properties:
        message:
          type: string
          description: Human-readable error message
        errors:
          type: object
          additionalProperties: true
          description: Field-specific error details
        correlation_id:
          type: string
          format: uuid
          description: Correlation ID for tracing
      example:
        message: "Validation failed"
        errors:
          name: ["Name is required"]
        correlation_id: "123e4567-e89b-12d3-a456-426614174000"
```

### 5. Generate Common Components

```yaml
components:
  responses:
    BadRequest:
      description: Invalid request parameters or body
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            message: "Validation failed"
            errors:
              name: ["Name cannot be empty"]
    
    Unauthorized:
      description: Authentication required or invalid token
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            message: "Invalid or expired token"
    
    Forbidden:
      description: Insufficient permissions
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            message: "Insufficient permissions for this operation"
    
    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            message: "Resource not found"
    
    Conflict:
      description: Resource already exists or constraint violation
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            message: "Resource already exists"
    
    TooManyRequests:
      description: Rate limit exceeded
      headers:
        Retry-After:
          schema:
            type: integer
          description: Seconds until rate limit resets
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            message: "Rate limit exceeded"
    
    InternalServerError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            message: "An unexpected error occurred"
  
  parameters:
    PageParam:
      name: page
      in: query
      description: Page number for pagination
      required: false
      schema:
        type: integer
        minimum: 1
        default: 1
    
    PerPageParam:
      name: per_page
      in: query
      description: Items per page
      required: false
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20
    
    SearchParam:
      name: search
      in: query
      description: Search term for filtering
      required: false
      schema:
        type: string
    
    SortByParam:
      name: sort_by
      in: query
      description: Field to sort by
      required: false
      schema:
        type: string
        default: created_at
    
    SortOrderParam:
      name: sort_order
      in: query
      description: Sort direction
      required: false
      schema:
        type: string
        enum: [asc, desc]
        default: desc
  
  headers:
    X-Correlation-ID:
      description: Correlation ID for request tracing
      schema:
        type: string
        format: uuid
    
    X-RateLimit-Limit:
      description: Maximum requests allowed in window
      schema:
        type: integer
    
    X-RateLimit-Remaining:
      description: Remaining requests in current window
      schema:
        type: integer
    
    X-RateLimit-Reset:
      description: Unix timestamp when rate limit resets
      schema:
        type: integer
  
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: |
        JWT token obtained from authentication endpoint.
        Include in Authorization header as: Bearer <token>

security:
  - bearerAuth: []
```

### 6. Validate Generated OpenAPI

Run validation tools:

```bash
# Install validators
pip install openapi-spec-validator

# Validate spec
openapi-spec-validator ${outputFile}

# Or using swagger-cli
npm install -g swagger-cli
swagger-cli validate ${outputFile}
```

Check for:
- Valid YAML syntax
- All `$ref` references resolve
- Schema definitions are complete
- Examples match schemas
- Required fields are present
- No circular dependencies

### 7. Generate Documentation

Create HTML documentation from OpenAPI spec:

```bash
# Using redoc-cli
npm install -g redoc-cli
redoc-cli bundle ${outputFile} -o docs/api.html

# Or using swagger-ui
# Creates interactive API documentation
```

### 8. Compare with Existing Spec

If OpenAPI file exists:
- Identify added/removed/changed endpoints
- Check for breaking changes
- Suggest version bump if needed
- Generate changelog

## Extraction Patterns

### From Markdown Tables

**Path Parameters Table:**
```
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| userId | UUID | Yes | User identifier | 123e... |
```

→ OpenAPI:
```yaml
parameters:
  - name: userId
    in: path
    required: true
    description: User identifier
    schema:
      type: string
      format: uuid
    example: "123e4567-e89b-12d3-a456-426614174000"
```

### From JSON Code Blocks

**Request Schema:**
````markdown
```json
{
  "name": {
    "type": "string",
    "minLength": 1,
    "maxLength": 255,
    "required": true
  }
}
```
````

→ OpenAPI:
```yaml
properties:
  name:
    type: string
    minLength: 1
    maxLength: 255
required:
  - name
```

### From Requirements

**SEC-001: Endpoint SHALL require valid JWT authentication**

→ OpenAPI:
```yaml
security:
  - bearerAuth: []

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

## Quality Checklist

- [ ] OpenAPI version is 3.1.0 or later
- [ ] All paths extracted from specification
- [ ] All HTTP methods included
- [ ] Request/response schemas complete
- [ ] Security schemes defined
- [ ] Examples provided for all schemas
- [ ] Error responses standardized
- [ ] Headers documented
- [ ] Rate limiting specified
- [ ] Validation passes without errors
- [ ] Documentation generates successfully
- [ ] No broken `$ref` references
- [ ] Enum values match specification
- [ ] Date formats use ISO 8601
- [ ] UUID fields use format: uuid

## Error Handling

**If specification is incomplete:**
- List missing sections
- Use sensible defaults
- Add TODO comments in YAML
- Generate warning summary

**If validation fails:**
- Display validation errors
- Suggest fixes
- Provide corrected YAML snippets
- Re-validate after fixes

**If examples don't match schemas:**
- Flag inconsistencies
- Auto-correct if possible
- Request clarification

## Output

After generation:
1. Save OpenAPI YAML to specified path
2. Run validation and display results
3. Generate HTML documentation
4. Display summary:
   - Number of paths/operations
   - Number of schemas
   - Validation status
   - Documentation URL
5. List any warnings or TODOs
6. Suggest next steps (implementation, contract tests)

## Example Usage

```bash
# In Copilot Chat
/generate-openapi-from-spec

# Prompts for:
Spec file: spec/schema-api-user-get.md
Output file: openapi/spec.yaml (default)
API version: v0 (default)
Validate: true (default)

# Generates:
✅ OpenAPI spec created: openapi/spec.yaml
✅ Validation passed
✅ Documentation generated: docs/api.html
📊 Summary:
   - 5 paths
   - 8 operations
   - 12 schemas
   - 0 warnings
```
