---
description: "Update OpenAPI 3.x specification with new paths, schemas, and operations for a Flask resource following wfp-flask-template API documentation standards"
agent: "specification"
tools: ["edit", "search", "search/codebase", "web/fetch"]
---

# Update OpenAPI Specification

You are an expert in OpenAPI 3.x specification design, creating comprehensive and accurate API documentation that serves as the contract for Flask REST APIs following wfp-flask-template conventions.

## Task

Update OpenAPI specification file with:
- Path definitions for new resource endpoints
- Request/response schema definitions
- Parameter specifications
- Error response schemas
- Security requirements
- Tags and descriptions

## Input Variables

- `${input:entityName}` - Singular entity name (e.g., "user", "project")
- `${input:entityNamePlural:entityName + 's'}` - Plural form
- `${input:specFile:openapi/spec.yaml}` - OpenAPI spec file path
- `${input:apiVersion:v0}` - API version prefix

## Workflow

### 1. Read Existing Spec
- Load current OpenAPI specification
- Identify existing patterns and components
- Check version and info section

### 2. Add Schema Definitions
Add to `components.schemas`:

```yaml
# Component Schemas
components:
  schemas:
    ${entityName.capitalize()}:
      type: object
      description: ${entityName.capitalize()} entity with metadata
      required:
        - id
        - name
        - is_active
        - created_at
        - updated_at
      properties:
        id:
          type: string
          format: uuid
          description: Unique identifier
          readOnly: true
        name:
          type: string
          minLength: 1
          maxLength: 255
          description: ${entityName.capitalize()} name
        description:
          type: string
          maxLength: 1000
          description: Optional description
          nullable: true
        is_active:
          type: boolean
          description: Active status flag
          default: true
        created_at:
          type: string
          format: date-time
          description: Creation timestamp
          readOnly: true
        updated_at:
          type: string
          format: date-time
          description: Last update timestamp
          readOnly: true
      example:
        id: "123e4567-e89b-12d3-a456-426614174000"
        name: "Example ${entityName.capitalize()}"
        description: "Sample description"
        is_active: true
        created_at: "2024-01-07T10:00:00Z"
        updated_at: "2024-01-07T10:00:00Z"
    
    ${entityName.capitalize()}Create:
      type: object
      description: Schema for creating a new ${entityName}
      required:
        - name
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 255
          description: ${entityName.capitalize()} name
        description:
          type: string
          maxLength: 1000
          description: Optional description
          nullable: true
        is_active:
          type: boolean
          description: Active status flag
          default: true
      example:
        name: "New ${entityName.capitalize()}"
        description: "Description text"
        is_active: true
    
    ${entityName.capitalize()}Update:
      type: object
      description: Schema for partially updating a ${entityName}
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 255
          description: ${entityName.capitalize()} name
        description:
          type: string
          maxLength: 1000
          description: Optional description
          nullable: true
        is_active:
          type: boolean
          description: Active status flag
      example:
        name: "Updated Name"
    
    ${entityName.capitalize()}Replace:
      type: object
      description: Schema for completely replacing a ${entityName}
      required:
        - name
        - is_active
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 255
          description: ${entityName.capitalize()} name
        description:
          type: string
          maxLength: 1000
          description: Optional description
          nullable: true
        is_active:
          type: boolean
          description: Active status flag
      example:
        name: "Replaced Name"
        description: "New description"
        is_active: false
    
    ${entityName.capitalize()}List:
      type: object
      description: Paginated list of ${entityNamePlural}
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
            $ref: '#/components/schemas/${entityName.capitalize()}'
          description: Array of ${entityName} objects
        page:
          type: integer
          minimum: 1
          description: Current page number
        per_page:
          type: integer
          minimum: 1
          maximum: 100
          description: Items per page
        total:
          type: integer
          minimum: 0
          description: Total number of items
        total_pages:
          type: integer
          minimum: 0
          description: Total number of pages
      example:
        data:
          - id: "123e4567-e89b-12d3-a456-426614174000"
            name: "Example ${entityName.capitalize()}"
            is_active: true
            created_at: "2024-01-07T10:00:00Z"
            updated_at: "2024-01-07T10:00:00Z"
        page: 1
        per_page: 20
        total: 1
        total_pages: 1
```

### 3. Add Path Definitions
Add to `paths`:

```yaml
paths:
  /${apiVersion}/${entityNamePlural}:
    get:
      summary: List ${entityNamePlural}
      description: Retrieve a paginated list of ${entityNamePlural} with optional filtering and sorting
      operationId: list${entityName.capitalize()}s
      tags:
        - ${entityName.capitalize()}s
      security:
        - bearerAuth: []
      parameters:
        - name: page
          in: query
          description: Page number
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
        - name: search
          in: query
          description: Search term for name field
          required: false
          schema:
            type: string
        - name: is_active
          in: query
          description: Filter by active status
          required: false
          schema:
            type: boolean
        - name: sort_by
          in: query
          description: Field to sort by
          required: false
          schema:
            type: string
            enum: [name, created_at, updated_at]
            default: created_at
        - name: sort_order
          in: query
          description: Sort direction
          required: false
          schema:
            type: string
            enum: [asc, desc]
            default: desc
      responses:
        '200':
          description: Successful response with paginated ${entityNamePlural}
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/${entityName.capitalize()}List'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '500':
          $ref: '#/components/responses/InternalServerError'
    
    post:
      summary: Create ${entityName}
      description: Create a new ${entityName}
      operationId: create${entityName.capitalize()}
      tags:
        - ${entityName.capitalize()}s
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/${entityName.capitalize()}Create'
      responses:
        '201':
          description: ${entityName.capitalize()} created successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    $ref: '#/components/schemas/${entityName.capitalize()}'
                  message:
                    type: string
                    example: "${entityName.capitalize()} created successfully"
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '409':
          $ref: '#/components/responses/Conflict'
        '500':
          $ref: '#/components/responses/InternalServerError'
  
  /${apiVersion}/${entityNamePlural}/{${entityName}Id}:
    parameters:
      - name: ${entityName}Id
        in: path
        description: ${entityName.capitalize()} UUID
        required: true
        schema:
          type: string
          format: uuid
    
    get:
      summary: Get ${entityName}
      description: Retrieve a specific ${entityName} by ID
      operationId: get${entityName.capitalize()}
      tags:
        - ${entityName.capitalize()}s
      security:
        - bearerAuth: []
      responses:
        '200':
          description: ${entityName.capitalize()} found
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    $ref: '#/components/schemas/${entityName.capitalize()}'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
    
    patch:
      summary: Update ${entityName}
      description: Partially update a ${entityName}
      operationId: update${entityName.capitalize()}
      tags:
        - ${entityName.capitalize()}s
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/${entityName.capitalize()}Update'
      responses:
        '200':
          description: ${entityName.capitalize()} updated successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    $ref: '#/components/schemas/${entityName.capitalize()}'
                  message:
                    type: string
                    example: "${entityName.capitalize()} updated successfully"
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
    
    put:
      summary: Replace ${entityName}
      description: Completely replace a ${entityName}
      operationId: replace${entityName.capitalize()}
      tags:
        - ${entityName.capitalize()}s
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/${entityName.capitalize()}Replace'
      responses:
        '200':
          description: ${entityName.capitalize()} replaced successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    $ref: '#/components/schemas/${entityName.capitalize()}'
                  message:
                    type: string
                    example: "${entityName.capitalize()} replaced successfully"
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
    
    delete:
      summary: Delete ${entityName}
      description: Delete a specific ${entityName}
      operationId: delete${entityName.capitalize()}
      tags:
        - ${entityName.capitalize()}s
      security:
        - bearerAuth: []
      responses:
        '204':
          description: ${entityName.capitalize()} deleted successfully
        '401':
          $ref: '#/components/responses/Unauthorized'
        '403':
          $ref: '#/components/responses/Forbidden'
        '404':
          $ref: '#/components/responses/NotFound'
        '500':
          $ref: '#/components/responses/InternalServerError'
```

### 4. Add Tag Definition
Add to `tags`:

```yaml
tags:
  - name: ${entityName.capitalize()}s
    description: Operations related to ${entityName} management
```

### 5. Common Response Definitions
Ensure these exist in `components.responses`:

```yaml
components:
  responses:
    BadRequest:
      description: Invalid request parameters or body
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    
    Unauthorized:
      description: Authentication required or invalid token
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    
    Forbidden:
      description: Insufficient permissions
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    
    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    
    Conflict:
      description: Resource already exists or constraint violation
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
    
    InternalServerError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
  
  schemas:
    Error:
      type: object
      required:
        - message
      properties:
        message:
          type: string
          description: Error message
        errors:
          type: object
          description: Detailed error information
          additionalProperties: true
      example:
        message: "Validation failed"
        errors:
          name: ["Name is required"]
```

### 6. Security Definitions
Ensure security schemes are defined:

```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT token obtained from authentication endpoint
```

## Validation Steps

### 1. Validate Syntax
```bash
# Using openapi-spec-validator
openapi-spec-validator ${specFile}

# Using swagger-cli
swagger-cli validate ${specFile}
```

### 2. Generate Documentation
```bash
# Generate HTML documentation
redoc-cli bundle ${specFile} -o docs/api.html

# Or with swagger-ui
swagger-ui-watcher ${specFile}
```

### 3. Check Consistency
- All `$ref` references resolve correctly
- Schema names follow PascalCase
- Path parameters match URL templates
- Response codes follow REST conventions
- Examples are valid against schemas

## Quality Checklist

- [ ] All schemas defined in `components.schemas`
- [ ] All paths follow `/${apiVersion}/${resource}` pattern
- [ ] Security requirements on all authenticated endpoints
- [ ] Request/response examples provided
- [ ] Error responses documented (400, 401, 403, 404, 500)
- [ ] Parameter descriptions are clear
- [ ] operationId follows convention: `verb${Entity}`
- [ ] Tags assigned to group operations
- [ ] Spec validates without errors
- [ ] Pagination parameters on list endpoints
- [ ] UUID format on ID fields

## OpenAPI Best Practices

**Naming Conventions:**
- Schemas: `PascalCase` (e.g., `UserCreate`, `UserList`)
- Paths: `kebab-case` or `snake_case` (e.g., `/api/v0/users`)
- operationIds: `camelCase` (e.g., `createUser`, `listUsers`)

**Response Patterns:**
- 200: Success (GET, PATCH, PUT)
- 201: Created (POST)
- 204: No Content (DELETE)
- 400: Bad Request (validation)
- 401: Unauthorized (auth)
- 403: Forbidden (permissions)
- 404: Not Found
- 409: Conflict (duplicates)
- 500: Server Error

**Schema Patterns:**
- Base schema: Full entity with all fields
- Create schema: Fields allowed during creation
- Update schema: Optional fields for partial update
- Replace schema: Required fields for full replacement
- List schema: Wrapper with data array + pagination

## Output

After updating the spec:
1. Validate spec syntax
2. Generate HTML documentation
3. Present summary of changes
4. List any validation warnings
