---
description: "Design database schema from specification with tables, columns, types, constraints, indexes, and relationships"
agent: "API Architect"
tools: ["search", "search/codebase", "edit", "read/problems"]
---

# Design Database Schema

You are an expert database architect. Transform API specification into a complete, optimized database schema with proper types, constraints, indexes, and relationships for PostgreSQL.

## Task

Generate comprehensive database schema including:
- **Table definitions** with columns and types
- **Primary and foreign keys**
- **Unique constraints** and check constraints
- **Indexes** for performance (filters, sorts, searches)
- **Relationships** (one-to-one, one-to-many, many-to-many)
- **Migration strategy** (Alembic)

## Input Variables

- `${input:specFile}` - Path to specification file (e.g., `spec/schema-api-projects-crud.md`)
- `${input:resourceName}` - Resource name (e.g., `projects`)

## Workflow

### 1. Parse Specification

Read specification:
```
${specFile}
```

Extract:
- Entity name and description
- All fields with types, constraints, descriptions
- Required vs optional fields
- Unique constraints
- Relationships to other entities
- Business rules

### 2. Map Spec Types to Database Types

**String mappings**:
- `string` (short) → `VARCHAR(255)`
- `string` (long) → `TEXT`
- `string` (with maxLength) → `VARCHAR(maxLength)`
- `email` → `VARCHAR(320)` with check constraint
- `url` → `TEXT` with check constraint
- `uuid` → `UUID` (PostgreSQL native)

**Numeric mappings**:
- `integer` → `INTEGER`
- `number` → `NUMERIC` or `DOUBLE PRECISION`
- `decimal` → `NUMERIC(precision, scale)`

**Boolean**:
- `boolean` → `BOOLEAN`

**Date/Time**:
- `date` → `DATE`
- `datetime` / `timestamp` → `TIMESTAMP` (use `TIMESTAMPTZ` for timezone awareness)
- `time` → `TIME`

**JSON**:
- `object` / `json` → `JSONB` (preferred over JSON for performance)
- `array` → `JSONB` or dedicated table (if relational)

**Special types**:
- `enum` → `VARCHAR` with CHECK constraint or PostgreSQL ENUM
- `file` / `binary` → `BYTEA` or external storage (S3)

### 3. Design Table Structure

For the main resource:

```sql
-- Table: ${resource_plural}
-- Description: ${description}
CREATE TABLE ${resource_plural} (
    -- Primary key (UUID)
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Required fields from spec
    ${field_name} ${field_type} NOT NULL,

    -- Optional fields from spec
    ${optional_field} ${field_type} NULL,

    -- Foreign keys
    ${related_entity}_id UUID NOT NULL REFERENCES ${related_table}(id) ON DELETE CASCADE,

    -- Tenant isolation (multi-tenancy)
    company_id UUID NOT NULL,

    -- Soft delete (if needed)
    is_active BOOLEAN DEFAULT true NOT NULL,
    deleted_at TIMESTAMP NULL,

    -- Audit timestamps (automatic)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT ${table}_pkey PRIMARY KEY (id),
    CONSTRAINT ${table}_company_fk FOREIGN KEY (company_id) REFERENCES companies(id),
    CONSTRAINT uq_${table}_${field1}_${field2} UNIQUE (${field1}, ${field2}),
    CONSTRAINT ck_${table}_${field}_length CHECK (length(${field}) >= min AND length(${field}) <= max),
    CONSTRAINT ck_${table}_${field}_range CHECK (${field} >= min AND ${field} <= max),
    CONSTRAINT ck_${table}_email_format CHECK (${field} ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Comments for documentation
COMMENT ON TABLE ${resource_plural} IS '${description}';
COMMENT ON COLUMN ${resource_plural}.${field} IS '${field_description}';
```

### 4. Add Indexes

Create indexes for:
- **Foreign keys**: Always index FKs for JOIN performance
- **Filter columns**: Columns used in WHERE clauses (company_id, status, is_active)
- **Sort columns**: Columns used in ORDER BY (created_at, updated_at, name)
- **Search columns**: Full-text search, LIKE queries
- **Composite indexes**: Multi-column filters (company_id, status)

```sql
-- Index naming convention: idx_{table}_{column(s)}

-- Foreign key indexes (always!)
CREATE INDEX idx_${resource_plural}_company_id
    ON ${resource_plural}(company_id);
CREATE INDEX idx_${resource_plural}_${related}_id
    ON ${resource_plural}(${related_entity}_id);

-- Filter indexes
CREATE INDEX idx_${resource_plural}_is_active
    ON ${resource_plural}(is_active)
    WHERE is_active = true;  -- Partial index for active records only

-- Sort indexes (DESC for typical newest-first)
CREATE INDEX idx_${resource_plural}_created_at
    ON ${resource_plural}(created_at DESC);

-- Composite indexes (order matters! Most selective first)
CREATE INDEX idx_${resource_plural}_company_active
    ON ${resource_plural}(company_id, is_active)
    WHERE is_active = true;

-- Full-text search (if applicable)
CREATE INDEX idx_${resource_plural}_name_search
    ON ${resource_plural} USING GIN (to_tsvector('english', name));
```

**Index Guidelines**:
- Index foreign keys ALWAYS
- Index columns used in WHERE (high selectivity first)
- Index columns used in ORDER BY
- Use partial indexes for filtered queries (WHERE is_active = true)
- Use composite indexes for multi-column filters
- Don't over-index (slows writes)

### 5. Define Relationships

**One-to-Many**:
```sql
-- Parent table
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    ...
);

-- Child table
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    ...
);

CREATE INDEX idx_tasks_project_id ON tasks(project_id);
```

**Many-to-Many** (junction table):
```sql
-- Entity tables
CREATE TABLE users (id UUID PRIMARY KEY, ...);
CREATE TABLE roles (id UUID PRIMARY KEY, ...);

-- Junction table
CREATE TABLE user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
```

**Self-referencing** (tree/hierarchy):
```sql
CREATE TABLE categories (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    parent_id UUID NULL REFERENCES categories(id) ON DELETE CASCADE,
    ...
);

CREATE INDEX idx_categories_parent_id ON categories(parent_id);
```

### 6. Add Triggers for Updated At

PostgreSQL trigger to auto-update `updated_at`:

```sql
-- Generic function (create once)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to table
CREATE TRIGGER update_${resource_plural}_updated_at
    BEFORE UPDATE ON ${resource_plural}
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### 7. Generate Alembic Migration

Create Alembic migration script:

```python
"""Add ${resource_plural} table

Revision ID: ${revision_id}
Revises: ${previous_revision}
Create Date: ${date}
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '${revision_id}'
down_revision = '${previous_revision}'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create ${resource_plural} table with indexes and constraints."""

    # Create table
    op.create_table(
        '${resource_plural}',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP')),

        # Constraints
        sa.PrimaryKeyConstraint('id', name='${resource_plural}_pkey'),
        sa.UniqueConstraint('name', 'company_id',
                           name='uq_${resource_plural}_name_company'),
        sa.CheckConstraint('length(name) >= 3 AND length(name) <= 255',
                          name='ck_${resource_plural}_name_length'),
    )

    # Create indexes
    op.create_index('idx_${resource_plural}_company_id',
                    '${resource_plural}', ['company_id'])
    op.create_index('idx_${resource_plural}_created_at',
                    '${resource_plural}', ['created_at'],
                    postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_${resource_plural}_is_active',
                    '${resource_plural}', ['is_active'],
                    postgresql_where=sa.text('is_active = true'))

    # Create trigger for updated_at
    op.execute("""
        CREATE TRIGGER update_${resource_plural}_updated_at
            BEFORE UPDATE ON ${resource_plural}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop ${resource_plural} table."""

    # Drop trigger first
    op.execute('DROP TRIGGER IF EXISTS update_${resource_plural}_updated_at ON ${resource_plural}')

    # Drop indexes (automatically dropped with table, but explicit for clarity)
    op.drop_index('idx_${resource_plural}_is_active', table_name='${resource_plural}')
    op.drop_index('idx_${resource_plural}_created_at', table_name='${resource_plural}')
    op.drop_index('idx_${resource_plural}_company_id', table_name='${resource_plural}')

    # Drop table (CASCADE removes dependent objects)
    op.drop_table('${resource_plural}')
```

### 8. Generate Schema Documentation

Create comprehensive documentation:

```markdown
# Database Schema: ${Resource_Plural}

## Table: \`${resource_plural}\`

**Description**: ${description}

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NOT NULL | gen_random_uuid() | Primary key |
| name | VARCHAR(255) | NOT NULL | - | ${field_description} |
| description | TEXT | NULL | - | ${field_description} |
| company_id | UUID | NOT NULL | - | Tenant isolation |
| is_active | BOOLEAN | NOT NULL | true | Soft delete flag |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Last update timestamp |

### Constraints

#### Primary Key
- **PK**: \`id\`

#### Foreign Keys
- **FK**: \`company_id\` → \`companies(id)\`

#### Unique Constraints
- **UQ**: \`(name, company_id)\` - Name unique per company

#### Check Constraints
- **CK**: \`length(name) >= 3 AND length(name) <= 255\` - Name length validation

### Indexes

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| idx_${resource_plural}_company_id | company_id | B-tree | Filter by company |
| idx_${resource_plural}_created_at | created_at DESC | B-tree | Sort by creation date |
| idx_${resource_plural}_is_active | is_active (partial) | B-tree | Filter active records |

### Relationships

- **One-to-Many**: \`projects\` → \`tasks\` (project_id FK)
- **Many-to-One**: \`${resource_plural}\` → \`companies\` (company_id FK)

### Triggers

- **update_${resource_plural}_updated_at**: Auto-update \`updated_at\` on row modification

### Storage Estimates

**Assumptions**:
- Average row size: ~500 bytes (with indexes)
- 10,000 rows per company
- 100 companies

**Calculations**:
- Data: 10,000 × 100 × 500 bytes = 500 MB
- Indexes: ~30% overhead = 150 MB
- Total: ~650 MB

### Performance Considerations

- **Reads**: Excellent (indexed on company_id, created_at)
- **Writes**: Good (3 indexes, acceptable overhead)
- **Joins**: Excellent (FK indexes present)
- **Searches**: Good (can add GIN index for full-text if needed)

### Migration

**Upgrade**:
\`\`\`bash
flask db migrate -m "Add ${resource_plural} table"
flask db upgrade
\`\`\`

**Rollback**:
\`\`\`bash
flask db downgrade
\`\`\`
```

## Quality Checklist

Before completing:
- [ ] All spec fields mapped to database columns
- [ ] All required fields marked NOT NULL
- [ ] Primary key defined (UUID)
- [ ] Foreign keys with proper ON DELETE behavior
- [ ] Unique constraints match business rules
- [ ] Check constraints for validation
- [ ] Indexes on foreign keys (always!)
- [ ] Indexes on filter/sort columns
- [ ] updated_at trigger created
- [ ] Alembic migration script complete
- [ ] Migration reversible (downgrade works)
- [ ] Documentation generated

## Example Usage

```
@api-architect /design-database-schema
Spec: spec/schema-api-projects-crud.md
Resource: projects
```

Output:
1. Complete SQL DDL with constraints and indexes
2. Alembic migration script (upgrade/downgrade)
3. Schema documentation with relationships and performance notes

---

**Note**: Schema follows wfp-flask-template patterns with UUIDMixin, TimestampMixin, and multi-tenancy (company_id).
