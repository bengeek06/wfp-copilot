---
description: "Generate Postman Collection from OpenAPI specification with authentication, examples, tests, and environment setup"
agent: "specification"
tools: ["search", "search/codebase", "web/fetch"]
---

# Generate Postman Collection

You are an expert in API documentation and Postman collections. Generate comprehensive Postman Collection v2.1 from OpenAPI 3.x specifications with authentication setup, request examples, automated tests, and environment configuration.

## Task

Create Postman collection with:
- **All endpoints** from OpenAPI spec with proper HTTP methods
- **Authentication setup** (JWT cookies, pre-request scripts)
- **Request examples** with realistic data for each endpoint
- **Response examples** showing success and error cases
- **Automated tests** validating status codes, response schema, data
- **Folder organization** by resource/feature
- **Environment variables** for base URL, tokens, IDs
- **Collection variables** for shared data
- **Documentation** from OpenAPI descriptions

## Input Variables

- `${input:openapiPath}` - Path to OpenAPI spec file (e.g., openapi/projects-api.yaml)
- `${input:serviceName}` - Service name (e.g., Projects API, Tasks API)
- `${input:baseUrl}` - Base URL (default: {{baseUrl}})
- `${input:includeTests}` - Generate test scripts (default: true)

## Workflow

### 1. Parse OpenAPI Specification

Extract key information:

```yaml
# Example OpenAPI spec
openapi: 3.0.0
info:
  title: Projects API
  version: 1.0.0
  description: Manage projects and tasks
servers:
  - url: https://api.example.com/v0
paths:
  /projects:
    get:
      summary: List projects
      operationId: listProjects
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
      responses:
        200:
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      $ref: '#/components/schemas/Project'
    post:
      summary: Create project
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProjectCreate'
      responses:
        201:
          description: Created
```

**Extract**:
- Service name, version, description
- Base URL from servers
- All paths with methods (GET, POST, PATCH, DELETE)
- Parameters (path, query, header, cookie)
- Request body schemas
- Response schemas and status codes
- Security requirements (JWT, API keys)

### 2. Create Collection Structure

Postman Collection v2.1 format:

```json
{
  "info": {
    "name": "{{serviceName}}",
    "description": "{{description}}",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    "_postman_id": "{{generateUUID}}",
    "version": "{{version}}"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{access_token}}",
        "type": "string"
      }
    ]
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "https://api.example.com/v0",
      "type": "string"
    },
    {
      "key": "access_token",
      "value": "",
      "type": "string"
    }
  ],
  "item": [
    // Folders and requests
  ]
}
```

### 3. Organize Requests into Folders

Group by resource:

```json
{
  "name": "Projects",
  "description": "Project management endpoints",
  "item": [
    {
      "name": "List Projects",
      "request": { /* ... */ }
    },
    {
      "name": "Create Project",
      "request": { /* ... */ }
    },
    {
      "name": "Get Project",
      "request": { /* ... */ }
    },
    {
      "name": "Update Project",
      "request": { /* ... */ }
    },
    {
      "name": "Delete Project",
      "request": { /* ... */ }
    }
  ]
}
```

**Folder Structure Examples**:

```
Projects API/
├── Authentication/
│   ├── Login
│   └── Refresh Token
├── Projects/
│   ├── List Projects
│   ├── Create Project
│   ├── Get Project
│   ├── Update Project
│   └── Delete Project
├── Tasks/
│   ├── List Tasks
│   ├── Create Task
│   ├── Get Task
│   ├── Update Task
│   └── Delete Task
└── Admin/
    ├── List Users
    └── Assign Roles
```

### 4. Generate Request Definitions

Create request for each endpoint:

**Example: List Projects (GET)**

```json
{
  "name": "List Projects",
  "request": {
    "method": "GET",
    "header": [
      {
        "key": "Content-Type",
        "value": "application/json",
        "type": "text"
      }
    ],
    "url": {
      "raw": "{{baseUrl}}/projects?page=1&per_page=20&status=active",
      "host": ["{{baseUrl}}"],
      "path": ["projects"],
      "query": [
        {
          "key": "page",
          "value": "1",
          "description": "Page number (default: 1)"
        },
        {
          "key": "per_page",
          "value": "20",
          "description": "Items per page (default: 20, max: 100)"
        },
        {
          "key": "status",
          "value": "active",
          "description": "Filter by status",
          "disabled": false
        },
        {
          "key": "sort",
          "value": "name",
          "description": "Sort field",
          "disabled": true
        }
      ]
    },
    "description": "Retrieve paginated list of projects for the authenticated user's company.\n\n**Permissions**: Requires `projects:list` permission in Guardian.\n\n**Query Parameters**:\n- `page`: Page number (default: 1)\n- `per_page`: Items per page (default: 20, max: 100)\n- `status`: Filter by status (active, completed, archived)\n- `sort`: Sort by field (name, created_at, updated_at)\n- `order`: Sort order (asc, desc)"
  },
  "response": [
    {
      "name": "Success - 200 OK",
      "originalRequest": { /* same as request */ },
      "status": "OK",
      "code": 200,
      "_postman_previewlanguage": "json",
      "header": [
        {
          "key": "Content-Type",
          "value": "application/json"
        }
      ],
      "body": "{\n  \"items\": [\n    {\n      \"id\": \"550e8400-e29b-41d4-a716-446655440000\",\n      \"name\": \"Project Alpha\",\n      \"description\": \"Main project\",\n      \"status\": \"active\",\n      \"company_id\": \"660e8400-e29b-41d4-a716-446655440000\",\n      \"created_at\": \"2026-01-01T10:00:00Z\",\n      \"updated_at\": \"2026-01-07T15:30:00Z\"\n    }\n  ],\n  \"total\": 42,\n  \"page\": 1,\n  \"per_page\": 20,\n  \"total_pages\": 3\n}"
    },
    {
      "name": "Error - 401 Unauthorized",
      "originalRequest": { /* same as request */ },
      "status": "Unauthorized",
      "code": 401,
      "_postman_previewlanguage": "json",
      "header": [
        {
          "key": "Content-Type",
          "value": "application/json"
        }
      ],
      "body": "{\n  \"error\": \"Unauthorized\",\n  \"message\": \"Missing or invalid authentication token\"\n}"
    }
  ]
}
```

**Example: Create Project (POST)**

```json
{
  "name": "Create Project",
  "request": {
    "method": "POST",
    "header": [
      {
        "key": "Content-Type",
        "value": "application/json",
        "type": "text"
      }
    ],
    "body": {
      "mode": "raw",
      "raw": "{\n  \"name\": \"New Project\",\n  \"description\": \"Project description\",\n  \"status\": \"active\"\n}",
      "options": {
        "raw": {
          "language": "json"
        }
      }
    },
    "url": {
      "raw": "{{baseUrl}}/projects",
      "host": ["{{baseUrl}}"],
      "path": ["projects"]
    },
    "description": "Create a new project for the authenticated user's company.\n\n**Permissions**: Requires `projects:create` permission in Guardian.\n\n**Request Body**:\n- `name` (required): Project name (3-255 characters)\n- `description` (optional): Project description (max 1000 characters)\n- `status` (optional): Project status (default: 'active')"
  },
  "response": [
    {
      "name": "Success - 201 Created",
      "originalRequest": { /* same as request */ },
      "status": "Created",
      "code": 201,
      "_postman_previewlanguage": "json",
      "header": [
        {
          "key": "Content-Type",
          "value": "application/json"
        },
        {
          "key": "Location",
          "value": "/v0/projects/550e8400-e29b-41d4-a716-446655440000"
        }
      ],
      "body": "{\n  \"id\": \"550e8400-e29b-41d4-a716-446655440000\",\n  \"name\": \"New Project\",\n  \"description\": \"Project description\",\n  \"status\": \"active\",\n  \"company_id\": \"660e8400-e29b-41d4-a716-446655440000\",\n  \"created_at\": \"2026-01-07T16:45:00Z\",\n  \"updated_at\": \"2026-01-07T16:45:00Z\"\n}"
    },
    {
      "name": "Error - 422 Validation Error",
      "originalRequest": { /* same as request */ },
      "status": "Unprocessable Entity",
      "code": 422,
      "_postman_previewlanguage": "json",
      "body": "{\n  \"errors\": {\n    \"name\": [\"Missing required field\"],\n    \"status\": [\"Must be one of: active, completed, archived\"]\n  }\n}"
    },
    {
      "name": "Error - 409 Conflict",
      "originalRequest": { /* same as request */ },
      "status": "Conflict",
      "code": 409,
      "_postman_previewlanguage": "json",
      "body": "{\n  \"error\": \"Conflict\",\n  \"message\": \"Project 'New Project' already exists\"\n}"
    }
  ]
}
```

**Example: Get Project (GET with path param)**

```json
{
  "name": "Get Project",
  "request": {
    "method": "GET",
    "header": [],
    "url": {
      "raw": "{{baseUrl}}/projects/:project_id",
      "host": ["{{baseUrl}}"],
      "path": ["projects", ":project_id"],
      "variable": [
        {
          "key": "project_id",
          "value": "{{project_id}}",
          "description": "Project UUID"
        }
      ]
    },
    "description": "Retrieve a single project by ID.\n\n**Permissions**: Requires `projects:read` permission.\n\n**Path Parameters**:\n- `project_id`: UUID of the project"
  },
  "response": [
    {
      "name": "Success - 200 OK",
      "code": 200,
      "body": "{\n  \"id\": \"550e8400-e29b-41d4-a716-446655440000\",\n  \"name\": \"Project Alpha\",\n  \"description\": \"Main project\",\n  \"status\": \"active\",\n  \"company_id\": \"660e8400-e29b-41d4-a716-446655440000\",\n  \"created_at\": \"2026-01-01T10:00:00Z\",\n  \"updated_at\": \"2026-01-07T15:30:00Z\"\n}"
    },
    {
      "name": "Error - 404 Not Found",
      "code": 404,
      "body": "{\n  \"error\": \"Not Found\",\n  \"message\": \"Project not found\"\n}"
    }
  ]
}
```

### 5. Add Authentication Setup

**Collection-level authentication** (JWT Bearer):

```json
{
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{access_token}}",
        "type": "string"
      }
    ]
  }
}
```

**Authentication folder** with login endpoint:

```json
{
  "name": "Authentication",
  "description": "Authentication endpoints - run Login first to get access token",
  "item": [
    {
      "name": "Login",
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "// Extract token from Set-Cookie header",
              "const setCookie = pm.response.headers.get('Set-Cookie');",
              "if (setCookie) {",
              "    const tokenMatch = setCookie.match(/access_token=([^;]+)/);",
              "    if (tokenMatch) {",
              "        pm.collectionVariables.set('access_token', tokenMatch[1]);",
              "        console.log('Access token saved to collection variable');",
              "    }",
              "}",
              "",
              "// Parse response",
              "const response = pm.response.json();",
              "",
              "// Save user info",
              "if (response.user) {",
              "    pm.collectionVariables.set('user_id', response.user.id);",
              "    pm.collectionVariables.set('company_id', response.user.company_id);",
              "}",
              "",
              "// Tests",
              "pm.test('Status is 200', () => {",
              "    pm.response.to.have.status(200);",
              "});",
              "",
              "pm.test('Response has user data', () => {",
              "    pm.expect(response).to.have.property('user');",
              "    pm.expect(response.user).to.have.property('id');",
              "});"
            ],
            "type": "text/javascript"
          }
        }
      ],
      "request": {
        "auth": {
          "type": "noauth"
        },
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"user@example.com\",\n  \"password\": \"password123\"\n}"
        },
        "url": {
          "raw": "{{identityBaseUrl}}/auth/login",
          "host": ["{{identityBaseUrl}}"],
          "path": ["auth", "login"]
        },
        "description": "Authenticate user and receive JWT token in cookie.\n\nThe token is automatically extracted and saved to collection variables."
      }
    }
  ]
}
```

**Pre-request script** (collection-level) to set cookies:

```javascript
// Collection pre-request script
// Ensures access_token is sent as cookie
const accessToken = pm.collectionVariables.get('access_token');

if (accessToken) {
    pm.request.headers.add({
        key: 'Cookie',
        value: `access_token=${accessToken}`
    });
}
```

### 6. Add Test Scripts

Generate test scripts for each request:

**List endpoint tests**:
```javascript
// Test script for List Projects
pm.test('Status is 200 OK', () => {
    pm.response.to.have.status(200);
});

pm.test('Response has pagination', () => {
    const response = pm.response.json();
    pm.expect(response).to.have.property('items');
    pm.expect(response).to.have.property('total');
    pm.expect(response).to.have.property('page');
    pm.expect(response).to.have.property('per_page');
    pm.expect(response.items).to.be.an('array');
});

pm.test('Items have required fields', () => {
    const response = pm.response.json();
    if (response.items.length > 0) {
        const item = response.items[0];
        pm.expect(item).to.have.property('id');
        pm.expect(item).to.have.property('name');
        pm.expect(item).to.have.property('company_id');
        pm.expect(item).to.have.property('created_at');
        pm.expect(item).to.have.property('updated_at');
    }
});

pm.test('Response time is acceptable', () => {
    pm.expect(pm.response.responseTime).to.be.below(500);
});
```

**Create endpoint tests**:
```javascript
// Test script for Create Project
pm.test('Status is 201 Created', () => {
    pm.response.to.have.status(201);
});

pm.test('Response has Location header', () => {
    pm.response.to.have.header('Location');
});

pm.test('Created resource has ID', () => {
    const response = pm.response.json();
    pm.expect(response).to.have.property('id');

    // Save ID for subsequent requests
    pm.collectionVariables.set('project_id', response.id);
});

pm.test('Created resource matches request', () => {
    const response = pm.response.json();
    const request = JSON.parse(pm.request.body.raw);

    pm.expect(response.name).to.equal(request.name);
    pm.expect(response.description).to.equal(request.description);
});

pm.test('Has timestamps', () => {
    const response = pm.response.json();
    pm.expect(response).to.have.property('created_at');
    pm.expect(response).to.have.property('updated_at');
});
```

**Get endpoint tests**:
```javascript
// Test script for Get Project
pm.test('Status is 200 OK', () => {
    pm.response.to.have.status(200);
});

pm.test('Response matches schema', () => {
    const schema = {
        type: 'object',
        required: ['id', 'name', 'company_id', 'created_at', 'updated_at'],
        properties: {
            id: { type: 'string', format: 'uuid' },
            name: { type: 'string' },
            description: { type: ['string', 'null'] },
            status: { type: 'string', enum: ['active', 'completed', 'archived'] },
            company_id: { type: 'string', format: 'uuid' },
            created_at: { type: 'string', format: 'date-time' },
            updated_at: { type: 'string', format: 'date-time' }
        }
    };

    pm.response.to.have.jsonSchema(schema);
});
```

**Update endpoint tests**:
```javascript
// Test script for Update Project
pm.test('Status is 200 OK', () => {
    pm.response.to.have.status(200);
});

pm.test('Updated fields match request', () => {
    const response = pm.response.json();
    const request = JSON.parse(pm.request.body.raw);

    Object.keys(request).forEach(key => {
        pm.expect(response[key]).to.equal(request[key]);
    });
});

pm.test('updated_at is recent', () => {
    const response = pm.response.json();
    const updatedAt = new Date(response.updated_at);
    const now = new Date();
    const diffSeconds = (now - updatedAt) / 1000;

    pm.expect(diffSeconds).to.be.below(10); // Updated within 10 seconds
});
```

**Delete endpoint tests**:
```javascript
// Test script for Delete Project
pm.test('Status is 204 No Content', () => {
    pm.response.to.have.status(204);
});

pm.test('Response body is empty', () => {
    pm.expect(pm.response.text()).to.be.empty;
});
```

### 7. Set Up Variables

**Collection variables**:
```json
{
  "variable": [
    {
      "key": "baseUrl",
      "value": "https://api.example.com/v0",
      "type": "string"
    },
    {
      "key": "identityBaseUrl",
      "value": "https://identity.example.com/api/v1",
      "type": "string"
    },
    {
      "key": "access_token",
      "value": "",
      "type": "string"
    },
    {
      "key": "user_id",
      "value": "",
      "type": "string"
    },
    {
      "key": "company_id",
      "value": "",
      "type": "string"
    },
    {
      "key": "project_id",
      "value": "",
      "type": "string",
      "description": "Set automatically after creating a project"
    },
    {
      "key": "task_id",
      "value": "",
      "type": "string",
      "description": "Set automatically after creating a task"
    }
  ]
}
```

**Environment variables** (create separate environment):
```json
{
  "name": "Development",
  "values": [
    {
      "key": "baseUrl",
      "value": "http://localhost:5000/v0",
      "enabled": true
    },
    {
      "key": "identityBaseUrl",
      "value": "http://localhost:5001/api/v1",
      "enabled": true
    }
  ]
}
```

```json
{
  "name": "Staging",
  "values": [
    {
      "key": "baseUrl",
      "value": "https://api.staging.example.com/v0",
      "enabled": true
    },
    {
      "key": "identityBaseUrl",
      "value": "https://identity.staging.example.com/api/v1",
      "enabled": true
    }
  ]
}
```

### 8. Add Collection Events

**Collection-level pre-request script**:
```javascript
// Set authentication cookie
const accessToken = pm.collectionVariables.get('access_token');
if (accessToken) {
    pm.request.headers.add({
        key: 'Cookie',
        value: `access_token=${accessToken}`
    });
}

// Log request info
console.log(`[${pm.request.method}] ${pm.request.url.toString()}`);
```

**Collection-level test script**:
```javascript
// Common tests for all requests
pm.test('Content-Type is JSON', () => {
    if (pm.response.code !== 204) { // Except for 204 No Content
        pm.response.to.have.header('Content-Type');
        pm.expect(pm.response.headers.get('Content-Type')).to.include('application/json');
    }
});

pm.test('Response time is reasonable', () => {
    pm.expect(pm.response.responseTime).to.be.below(2000);
});

// Log response info
console.log(`Status: ${pm.response.code} ${pm.response.status}`);
console.log(`Response Time: ${pm.response.responseTime}ms`);
```

### 9. Generate Complete Collection

Full collection structure:

```json
{
  "info": {
    "name": "Projects API",
    "description": "Manage projects and tasks with authentication and authorization",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    "version": "1.0.0"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{access_token}}",
        "type": "string"
      }
    ]
  },
  "event": [
    {
      "listen": "prerequest",
      "script": {
        "type": "text/javascript",
        "exec": [
          "// Collection-level pre-request script",
          "const accessToken = pm.collectionVariables.get('access_token');",
          "if (accessToken) {",
          "    pm.request.headers.add({",
          "        key: 'Cookie',",
          "        value: `access_token=${accessToken}`",
          "    });",
          "}"
        ]
      }
    },
    {
      "listen": "test",
      "script": {
        "type": "text/javascript",
        "exec": [
          "// Collection-level test script",
          "pm.test('Response time is reasonable', () => {",
          "    pm.expect(pm.response.responseTime).to.be.below(2000);",
          "});"
        ]
      }
    }
  ],
  "variable": [
    {
      "key": "baseUrl",
      "value": "https://api.example.com/v0",
      "type": "string"
    },
    {
      "key": "access_token",
      "value": "",
      "type": "string"
    }
  ],
  "item": [
    {
      "name": "Authentication",
      "description": "Login to get access token",
      "item": [
        // Login request
      ]
    },
    {
      "name": "Projects",
      "description": "Project CRUD operations",
      "item": [
        // List, Create, Get, Update, Delete
      ]
    },
    {
      "name": "Tasks",
      "description": "Task CRUD operations",
      "item": [
        // List, Create, Get, Update, Delete
      ]
    }
  ]
}
```

## Request Naming Convention

Use clear, action-oriented names:

| Endpoint | Method | Name |
|----------|--------|------|
| `/projects` | GET | List Projects |
| `/projects` | POST | Create Project |
| `/projects/:id` | GET | Get Project |
| `/projects/:id` | PATCH | Update Project |
| `/projects/:id` | PUT | Replace Project |
| `/projects/:id` | DELETE | Delete Project |
| `/projects/:id/tasks` | GET | List Project Tasks |
| `/projects/search` | POST | Search Projects |

## Best Practices

### ✅ DO

- **Organize by resource**: Group related endpoints in folders
- **Add descriptions**: Document each request with OpenAPI descriptions
- **Include examples**: Provide success and error response examples
- **Add tests**: Validate status codes, schemas, and data
- **Use variables**: `{{baseUrl}}`, `{{project_id}}` for reusability
- **Save dynamic data**: Store created IDs in collection variables
- **Extract tokens**: Auto-save JWT from login response
- **Version environments**: Development, Staging, Production
- **Document permissions**: List required Guardian roles per endpoint
- **Add pre-request scripts**: Set up authentication, headers

### ❌ DON'T

- Don't hardcode URLs (use `{{baseUrl}}`)
- Don't hardcode IDs (use variables)
- Don't skip authentication setup
- Don't forget error examples
- Don't omit test scripts
- Don't use production tokens in collection
- Don't expose secrets in exported collection

## Output Format

Generate collection as JSON file:

```
docs/postman/
├── Projects-API.postman_collection.json
├── Development.postman_environment.json
├── Staging.postman_environment.json
└── README.md
```

**README.md** with usage instructions:

```markdown
# Postman Collection - Projects API

## Setup

1. Import `Projects-API.postman_collection.json` into Postman
2. Import environment (`Development.postman_environment.json` or `Staging.postman_environment.json`)
3. Select environment in top-right dropdown

## Authentication

1. Open "Authentication" folder
2. Run "Login" request with valid credentials
3. Access token is automatically extracted and saved
4. All subsequent requests use this token

## Usage

### Create a Project
1. Open "Projects" folder
2. Run "Create Project" request
3. Project ID is saved to `{{project_id}}` variable
4. Use this ID in "Get Project", "Update Project", "Delete Project"

### Run All Tests
Click "Run" button on collection to execute all requests in sequence.

## Variables

- `baseUrl`: API base URL (set in environment)
- `access_token`: JWT token (set by Login request)
- `project_id`: Created project ID (set by Create Project)
- `task_id`: Created task ID (set by Create Task)
```

## Quality Checklist

Before exporting collection:
- [ ] All endpoints from OpenAPI spec included
- [ ] Requests organized into logical folders
- [ ] Authentication setup (login + token extraction)
- [ ] Request examples with realistic data
- [ ] Response examples (success + errors)
- [ ] Test scripts for all requests
- [ ] Variables for base URL, tokens, IDs
- [ ] Descriptions from OpenAPI spec
- [ ] Pre-request scripts for auth
- [ ] Collection-level events configured
- [ ] Environment files created
- [ ] README with usage instructions

## Example Usage

```
@specification /generate-postman-collection

OpenAPI Path: openapi/projects-api.yaml
Service Name: Projects API
Base URL: {{baseUrl}}
Include Tests: true

# Agent generates:
# 1. Complete Postman Collection v2.1 JSON
# 2. Development and Staging environment files
# 3. README with setup and usage instructions
# 4. All CRUD operations with tests
# 5. Authentication setup with token extraction
```

---

**Note**: This collection format is compatible with Postman v10+ and can be imported directly or used with Newman for automated testing.
