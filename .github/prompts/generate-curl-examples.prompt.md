---
description: "Generate curl command examples for all API endpoints with authentication, headers, request bodies, and response examples"
agent: "specification"
tools: ["search", "search/codebase"]
---

# Generate Curl Examples

You are an expert in API documentation and curl commands. Generate comprehensive, copy-paste ready curl examples for all API endpoints with authentication, headers, request bodies, query parameters, and expected responses.

## Task

Create curl examples for:
- **All HTTP methods** (GET, POST, PATCH, PUT, DELETE)
- **Authentication** (JWT cookies, Bearer tokens, API keys)
- **Request headers** (Content-Type, Accept, custom headers)
- **Request bodies** (JSON, form data, multipart)
- **Query parameters** (pagination, filtering, sorting)
- **Path parameters** (resource IDs)
- **Response examples** (success and error cases)
- **Common workflows** (login → create → update → delete)
- **Environment variables** for easy customization

## Input Variables

- `${input:endpoint}` - Endpoint path (e.g., /projects, /tasks/:id)
- `${input:method}` - HTTP method (GET, POST, PATCH, DELETE)
- `${input:includeAuth}` - Include authentication (default: true)
- `${input:includeResponses}` - Include response examples (default: true)

## Curl Command Structure

### Basic Template

```bash
curl -X METHOD 'https://api.example.com/endpoint' \
  -H 'Header: Value' \
  -d 'request_body'
```

### With Environment Variables

```bash
# Set environment variables
export API_BASE_URL="https://api.example.com/v0"
export ACCESS_TOKEN="your-jwt-token-here"

# Use in curl
curl -X GET "$API_BASE_URL/projects" \
  -H "Cookie: access_token=$ACCESS_TOKEN"
```

## Authentication Examples

### 1. JWT Cookie Authentication (Waterfall Pattern)

**Login to get token**:

```bash
# Login endpoint
curl -X POST 'https://identity.example.com/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }' \
  -c cookies.txt \
  -v

# Extract token from Set-Cookie header
# Token is saved in cookies.txt file

# Use token in subsequent requests
curl -X GET 'https://api.example.com/v0/projects' \
  -b cookies.txt

# Or extract token manually
export ACCESS_TOKEN=$(grep access_token cookies.txt | awk '{print $7}')

curl -X GET 'https://api.example.com/v0/projects' \
  -H "Cookie: access_token=$ACCESS_TOKEN"
```

### 2. Bearer Token Authentication

```bash
# Set token
export ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Use in Authorization header
curl -X GET 'https://api.example.com/v0/projects' \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

### 3. API Key Authentication

```bash
export API_KEY="sk_live_1234567890abcdef"

curl -X GET 'https://api.example.com/v0/projects' \
  -H "X-API-Key: $API_KEY"
```

## CRUD Examples

### GET - List Resources

**Basic list**:

```bash
# List all projects
curl -X GET 'https://api.example.com/v0/projects' \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -H "Content-Type: application/json"

# Response (200 OK):
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Project Alpha",
      "status": "active",
      "created_at": "2026-01-01T10:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "total_pages": 3
}
```

**With pagination**:

```bash
# Page 2, 50 items per page
curl -X GET 'https://api.example.com/v0/projects?page=2&per_page=50' \
  -H "Cookie: access_token=$ACCESS_TOKEN"
```

**With filtering**:

```bash
# Filter by status
curl -X GET 'https://api.example.com/v0/projects?status=active' \
  -H "Cookie: access_token=$ACCESS_TOKEN"

# Multiple filters
curl -X GET 'https://api.example.com/v0/projects?status=active&sort=name&order=asc' \
  -H "Cookie: access_token=$ACCESS_TOKEN"

# URL encoding for special characters
curl -X GET 'https://api.example.com/v0/projects?name=Project%20Alpha' \
  -H "Cookie: access_token=$ACCESS_TOKEN"
```

**With sorting**:

```bash
# Sort by created date, descending
curl -X GET 'https://api.example.com/v0/projects?sort=created_at&order=desc' \
  -H "Cookie: access_token=$ACCESS_TOKEN"
```

### GET - Single Resource

```bash
# Get project by ID
export PROJECT_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X GET "https://api.example.com/v0/projects/$PROJECT_ID" \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -H "Content-Type: application/json"

# Response (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Project Alpha",
  "description": "Main project for Q1 2026",
  "status": "active",
  "company_id": "660e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-01T10:00:00Z",
  "updated_at": "2026-01-07T15:30:00Z"
}
```

**Not found (404)**:

```bash
curl -X GET "https://api.example.com/v0/projects/non-existent-id" \
  -H "Cookie: access_token=$ACCESS_TOKEN"

# Response (404 Not Found):
{
  "error": "Not Found",
  "message": "Project not found"
}
```

### POST - Create Resource

**Basic create**:

```bash
# Create project
curl -X POST 'https://api.example.com/v0/projects' \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Project",
    "description": "Project description",
    "status": "active"
  }'

# Response (201 Created):
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "name": "New Project",
  "description": "Project description",
  "status": "active",
  "company_id": "660e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-07T16:45:00Z",
  "updated_at": "2026-01-07T16:45:00Z"
}
```

**With JSON file**:

```bash
# Create request body file
cat > project.json <<EOF
{
  "name": "Project from File",
  "description": "Created using JSON file",
  "status": "active"
}
EOF

# Use file in curl
curl -X POST 'https://api.example.com/v0/projects' \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d @project.json
```

**Validation error (422)**:

```bash
# Missing required field
curl -X POST 'https://api.example.com/v0/projects' \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Missing name field"
  }'

# Response (422 Unprocessable Entity):
{
  "errors": {
    "name": ["This field is required"]
  }
}
```

**Conflict error (409)**:

```bash
# Duplicate name
curl -X POST 'https://api.example.com/v0/projects' \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Existing Project"
  }'

# Response (409 Conflict):
{
  "error": "Conflict",
  "message": "Project 'Existing Project' already exists"
}
```

### PATCH - Partial Update

```bash
# Update project status
curl -X PATCH "https://api.example.com/v0/projects/$PROJECT_ID" \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }'

# Response (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Project Alpha",
  "status": "completed",
  "updated_at": "2026-01-07T17:00:00Z"
}
```

**Update multiple fields**:

```bash
curl -X PATCH "https://api.example.com/v0/projects/$PROJECT_ID" \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Project Name",
    "description": "Updated description",
    "status": "archived"
  }'
```

### PUT - Full Replace

```bash
# Replace entire resource (less common)
curl -X PUT "https://api.example.com/v0/projects/$PROJECT_ID" \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Completely New Data",
    "description": "All fields must be provided",
    "status": "active"
  }'
```

### DELETE - Remove Resource

```bash
# Delete project
curl -X DELETE "https://api.example.com/v0/projects/$PROJECT_ID" \
  -H "Cookie: access_token=$ACCESS_TOKEN"

# Response (204 No Content):
# (Empty response body)
```

**Delete with confirmation**:

```bash
# Some APIs require confirmation
curl -X DELETE "https://api.example.com/v0/projects/$PROJECT_ID" \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "confirm": true
  }'
```

## Nested Resources

**Get nested resource**:

```bash
# List tasks for a project
curl -X GET "https://api.example.com/v0/projects/$PROJECT_ID/tasks" \
  -H "Cookie: access_token=$ACCESS_TOKEN"

# Create task for project
curl -X POST "https://api.example.com/v0/projects/$PROJECT_ID/tasks" \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Task",
    "status": "todo",
    "priority": 2
  }'
```

## Batch Operations

```bash
# Create multiple projects in one request
curl -X POST 'https://api.example.com/v0/projects/batch' \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "projects": [
      {
        "name": "Project 1",
        "description": "First project"
      },
      {
        "name": "Project 2",
        "description": "Second project"
      }
    ]
  }'

# Response:
{
  "created": [
    {"id": "uuid-1", "name": "Project 1"},
    {"id": "uuid-2", "name": "Project 2"}
  ],
  "failed": []
}
```

## Advanced Query Examples

### Complex Filtering

```bash
# Multiple status values (OR)
curl -X GET 'https://api.example.com/v0/projects?status=active,completed' \
  -H "Cookie: access_token=$ACCESS_TOKEN"

# Date range filtering
curl -X GET 'https://api.example.com/v0/projects?created_after=2026-01-01&created_before=2026-01-31' \
  -H "Cookie: access_token=$ACCESS_TOKEN"

# Text search
curl -X GET 'https://api.example.com/v0/projects?search=alpha' \
  -H "Cookie: access_token=$ACCESS_TOKEN"

# Field selection (sparse fieldsets)
curl -X GET 'https://api.example.com/v0/projects?fields=id,name,status' \
  -H "Cookie: access_token=$ACCESS_TOKEN"
```

### Include Related Resources

```bash
# Include tasks in project response
curl -X GET "https://api.example.com/v0/projects/$PROJECT_ID?include=tasks" \
  -H "Cookie: access_token=$ACCESS_TOKEN"

# Include multiple relations
curl -X GET "https://api.example.com/v0/projects/$PROJECT_ID?include=tasks,members" \
  -H "Cookie: access_token=$ACCESS_TOKEN"
```

## Error Handling Examples

### 401 Unauthorized

```bash
# Missing authentication
curl -X GET 'https://api.example.com/v0/projects'

# Response (401 Unauthorized):
{
  "error": "Unauthorized",
  "message": "Missing or invalid authentication token"
}
```

### 403 Forbidden

```bash
# Insufficient permissions
curl -X DELETE "https://api.example.com/v0/projects/$PROJECT_ID" \
  -H "Cookie: access_token=$ACCESS_TOKEN"

# Response (403 Forbidden):
{
  "error": "Forbidden",
  "message": "Insufficient permissions to delete project"
}
```

### 429 Rate Limit

```bash
# Too many requests
curl -X POST 'https://api.example.com/v0/projects' \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'

# Response (429 Too Many Requests):
{
  "error": "Rate Limit Exceeded",
  "message": "Too many requests. Retry after 60 seconds.",
  "retry_after": 60
}

# Response headers:
# Retry-After: 60
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 0
# X-RateLimit-Reset: 1704729600
```

## Complete Workflow Examples

### Workflow 1: Create Project with Tasks

```bash
#!/bin/bash
# Complete workflow: Login → Create Project → Add Tasks

# Step 1: Login
echo "Step 1: Login"
curl -X POST 'https://identity.example.com/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }' \
  -c cookies.txt \
  -s | jq '.'

# Step 2: Create Project
echo -e "\nStep 2: Create Project"
PROJECT_ID=$(curl -X POST 'https://api.example.com/v0/projects' \
  -b cookies.txt \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Q1 2026 Project",
    "description": "Main project for Q1",
    "status": "active"
  }' \
  -s | jq -r '.id')

echo "Created project: $PROJECT_ID"

# Step 3: Create Tasks
echo -e "\nStep 3: Create Tasks"
for i in {1..3}; do
  curl -X POST 'https://api.example.com/v0/tasks' \
    -b cookies.txt \
    -H 'Content-Type: application/json' \
    -d "{
      \"title\": \"Task $i\",
      \"description\": \"Task description $i\",
      \"status\": \"todo\",
      \"priority\": 2,
      \"project_id\": \"$PROJECT_ID\"
    }" \
    -s | jq '{id, title, status}'
done

# Step 4: List Project Tasks
echo -e "\nStep 4: List Project Tasks"
curl -X GET "https://api.example.com/v0/projects/$PROJECT_ID/tasks" \
  -b cookies.txt \
  -s | jq '.items[] | {id, title, status}'

# Step 5: Update Task Status
echo -e "\nStep 5: Update First Task to In Progress"
TASK_ID=$(curl -X GET "https://api.example.com/v0/projects/$PROJECT_ID/tasks" \
  -b cookies.txt \
  -s | jq -r '.items[0].id')

curl -X PATCH "https://api.example.com/v0/tasks/$TASK_ID" \
  -b cookies.txt \
  -H 'Content-Type: application/json' \
  -d '{
    "status": "in_progress"
  }' \
  -s | jq '{id, title, status}'

echo -e "\nWorkflow complete!"
```

### Workflow 2: Search and Filter

```bash
#!/bin/bash
# Search workflow

export API_BASE_URL="https://api.example.com/v0"
export ACCESS_TOKEN="your-token-here"

# Search projects by name
echo "Search projects containing 'Alpha':"
curl -X GET "$API_BASE_URL/projects?search=Alpha" \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -s | jq '.items[] | {id, name}'

# Filter by status and sort
echo -e "\nActive projects, sorted by name:"
curl -X GET "$API_BASE_URL/projects?status=active&sort=name&order=asc" \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -s | jq '.items[] | {name, status}'

# Paginate through results
echo -e "\nPaginated results:"
for page in {1..3}; do
  echo "Page $page:"
  curl -X GET "$API_BASE_URL/projects?page=$page&per_page=5" \
    -H "Cookie: access_token=$ACCESS_TOKEN" \
    -s | jq '.items[] | .name'
done
```

## Environment Setup Script

```bash
#!/bin/bash
# setup-api-env.sh - Configure environment for API testing

# Choose environment
ENV=${1:-development}

case $ENV in
  development)
    export API_BASE_URL="http://localhost:5000/v0"
    export IDENTITY_BASE_URL="http://localhost:5001/api/v1"
    ;;
  staging)
    export API_BASE_URL="https://api.staging.example.com/v0"
    export IDENTITY_BASE_URL="https://identity.staging.example.com/api/v1"
    ;;
  production)
    export API_BASE_URL="https://api.example.com/v0"
    export IDENTITY_BASE_URL="https://identity.example.com/api/v1"
    ;;
  *)
    echo "Unknown environment: $ENV"
    echo "Usage: source setup-api-env.sh [development|staging|production]"
    return 1
    ;;
esac

# Login function
login() {
  local email=${1:-"user@example.com"}
  local password=${2:-"password"}
  
  echo "Logging in as $email..."
  
  curl -X POST "$IDENTITY_BASE_URL/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{
      \"email\": \"$email\",
      \"password\": \"$password\"
    }" \
    -c ~/.api-cookies.txt \
    -s | jq '.'
  
  export ACCESS_TOKEN=$(grep access_token ~/.api-cookies.txt | awk '{print $7}')
  echo "Logged in successfully. Token saved."
}

# Helper function for authenticated requests
api_get() {
  curl -X GET "$API_BASE_URL/$1" \
    -H "Cookie: access_token=$ACCESS_TOKEN" \
    -s | jq '.'
}

api_post() {
  local endpoint=$1
  local data=$2
  
  curl -X POST "$API_BASE_URL/$endpoint" \
    -H "Cookie: access_token=$ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$data" \
    -s | jq '.'
}

echo "Environment: $ENV"
echo "API Base URL: $API_BASE_URL"
echo ""
echo "Available commands:"
echo "  login <email> <password>  - Authenticate"
echo "  api_get <endpoint>        - GET request"
echo "  api_post <endpoint> <json> - POST request"
echo ""
echo "Example:"
echo "  login user@example.com password123"
echo "  api_get projects"
echo "  api_post projects '{\"name\":\"Test\"}'"
```

**Usage**:

```bash
# Source the environment setup
source setup-api-env.sh staging

# Login
login user@example.com SecurePass123!

# Use helper functions
api_get projects
api_post projects '{"name": "New Project", "status": "active"}'
```

## Debugging Options

### Verbose Output

```bash
# Show request and response headers
curl -v -X GET 'https://api.example.com/v0/projects' \
  -H "Cookie: access_token=$ACCESS_TOKEN"

# Show timing information
curl -w "\nTime Total: %{time_total}s\nTime Connect: %{time_connect}s\n" \
  -X GET 'https://api.example.com/v0/projects' \
  -H "Cookie: access_token=$ACCESS_TOKEN"

# Include response headers in output
curl -i -X GET 'https://api.example.com/v0/projects' \
  -H "Cookie: access_token=$ACCESS_TOKEN"
```

### Save Response to File

```bash
# Save response body
curl -X GET 'https://api.example.com/v0/projects' \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -o projects.json

# Save with response headers
curl -i -X GET 'https://api.example.com/v0/projects' \
  -H "Cookie: access_token=$ACCESS_TOKEN" \
  -o projects-with-headers.txt
```

## Best Practices

### ✅ DO

- **Use environment variables** for base URLs and tokens
- **Include `-H "Content-Type: application/json"`** for JSON requests
- **Use `jq`** for pretty-printing JSON responses
- **Save cookies** with `-c cookies.txt` for session management
- **Use verbose mode** (`-v`) for debugging
- **Quote URLs** to handle special characters
- **Add comments** explaining each step
- **Test error cases** (401, 403, 404, 422)
- **Show expected responses** with examples

### ❌ DON'T

- Don't hardcode production tokens in examples
- Don't forget authentication headers
- Don't skip error handling examples
- Don't use invalid JSON in examples
- Don't forget to URL-encode query parameters
- Don't omit required headers

## Quality Checklist

Before publishing curl examples:
- [ ] All CRUD operations covered
- [ ] Authentication shown clearly
- [ ] Query parameters demonstrated
- [ ] Error cases included
- [ ] Environment variables used
- [ ] Complete workflows provided
- [ ] Response examples included
- [ ] Comments explain each command
- [ ] Copy-paste ready (tested)
- [ ] Helper scripts provided

## Example Usage

```
@specification /generate-curl-examples

Endpoint: /projects
Method: All (GET, POST, PATCH, DELETE)
Include Auth: true
Include Responses: true

# Agent generates:
# 1. Complete curl examples for all methods
# 2. Authentication setup (login flow)
# 3. Query parameter examples (pagination, filtering)
# 4. Error case examples (401, 403, 404, 422)
# 5. Complete workflow script
# 6. Environment setup helper
# 7. Response examples for all cases
```

---

**Note**: These examples use Waterfall's JWT cookie authentication. Adjust authentication method based on your API's requirements.
