---
description: "Generate Alembic data migrations for schema changes, data transformations, and backfills with rollback support"
agent: "Flask API Expert"
tools: ["search", "search/codebase", "execute/getTerminalOutput","execute/runInTerminal","read/terminalLastCommand","read/terminalSelection"]
---

# Generate Data Migration

You are an expert in Alembic migrations and data transformations. Generate safe, reversible data migration scripts for schema changes, data transformations, backfills, and cleanup operations with proper error handling and rollback support.

## Task

Create Alembic data migrations for:
- **Data backfills** after adding new columns
- **Data transformations** when changing data types or formats
- **Reference updates** when restructuring relationships
- **Cleanup operations** removing obsolete data
- **Enum migrations** when adding/removing enum values
- **JSON field migrations** transforming JSONB structures
- **Batch operations** for large datasets with progress tracking
- **Rollback scripts** to reverse data changes

## Input Variables

- `${input:migrationType}` - Type (backfill, transform, cleanup, enum, json)
- `${input:tableName}` - Table to migrate
- `${input:description}` - Migration description (e.g., "Backfill project status from active tasks")
- `${input:batchSize}` - Records per batch (default: 1000)

## Migration Types

### 1. Data Backfill Migration

Fill new columns with default or calculated values:

**Scenario**: Added `status` column to `projects` table, need to backfill based on existing data.

```python
"""Backfill project status based on task completion

Revision ID: 3f2a1b4c5d6e
Revises: 2e1a0b3c4d5e
Create Date: 2026-01-07 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision = '3f2a1b4c5d6e'
down_revision = '2e1a0b3c4d5e'
branch_labels = None
depends_on = None


def upgrade():
    """
    Backfill project status:
    - 'completed' if all tasks are done
    - 'in_progress' if has active tasks
    - 'active' otherwise (default)
    """
    # Create table reference for update operations
    projects = table('projects',
        column('id', sa.String),
        column('status', sa.String),
        column('updated_at', sa.DateTime)
    )

    connection = op.get_bind()

    # 1. Mark projects with all completed tasks as 'completed'
    connection.execute(
        projects.update()
        .values(
            status='completed',
            updated_at=sa.func.now()
        )
        .where(
            sa.and_(
                projects.c.status == None,
                # Subquery: project has no incomplete tasks
                ~sa.exists().where(
                    sa.and_(
                        sa.text('tasks.project_id = projects.id'),
                        sa.text("tasks.status != 'done'")
                    )
                ),
                # Subquery: project has at least one task
                sa.exists().where(
                    sa.text('tasks.project_id = projects.id')
                )
            )
        )
    )

    # 2. Mark projects with active tasks as 'in_progress'
    connection.execute(
        projects.update()
        .values(
            status='in_progress',
            updated_at=sa.func.now()
        )
        .where(
            sa.and_(
                projects.c.status == None,
                sa.exists().where(
                    sa.and_(
                        sa.text('tasks.project_id = projects.id'),
                        sa.text("tasks.status IN ('todo', 'in_progress')")
                    )
                )
            )
        )
    )

    # 3. Default remaining to 'active'
    connection.execute(
        projects.update()
        .values(
            status='active',
            updated_at=sa.func.now()
        )
        .where(projects.c.status == None)
    )

    # 4. Verify no NULL values remain
    result = connection.execute(
        sa.select([sa.func.count()])
        .select_from(projects)
        .where(projects.c.status == None)
    )
    null_count = result.scalar()

    if null_count > 0:
        raise Exception(f"Migration incomplete: {null_count} projects still have NULL status")

    print(f"✓ Backfilled status for all projects")


def downgrade():
    """
    Rollback: Set all status values back to NULL
    """
    projects = table('projects',
        column('status', sa.String),
        column('updated_at', sa.DateTime)
    )

    connection = op.get_bind()

    connection.execute(
        projects.update()
        .values(
            status=None,
            updated_at=sa.func.now()
        )
    )

    print(f"✓ Rolled back project status backfill")
```

**Best Practices**:
- ✅ Update in logical order (most specific first)
- ✅ Use subqueries for conditional logic
- ✅ Update `updated_at` timestamp
- ✅ Verify completion (no NULL values)
- ✅ Provide rollback (set back to NULL or original)

### 2. Data Transformation Migration

Transform existing data to new format:

**Scenario**: Changing `priority` from string ('low', 'medium', 'high') to integer (1, 2, 3).

```python
"""Transform task priority from string to integer

Revision ID: 4g3b2c5d6e7f
Revises: 3f2a1b4c5d6e
Create Date: 2026-01-07 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

revision = '4g3b2c5d6e7f'
down_revision = '3f2a1b4c5d6e'
branch_labels = None
depends_on = None


def upgrade():
    """
    Transform priority: string → integer

    Step 1: Add new integer column
    Step 2: Transform data
    Step 3: Drop old column
    Step 4: Rename new column
    """
    connection = op.get_bind()

    # Step 1: Add temporary column
    op.add_column('tasks',
        sa.Column('priority_int', sa.Integer(), nullable=True)
    )

    # Step 2: Transform data (string → integer)
    tasks = table('tasks',
        column('id', sa.String),
        column('priority', sa.String),
        column('priority_int', sa.Integer),
        column('updated_at', sa.DateTime)
    )

    # Mapping: string → integer
    priority_map = {
        'low': 1,
        'medium': 2,
        'high': 3
    }

    for string_val, int_val in priority_map.items():
        connection.execute(
            tasks.update()
            .values(
                priority_int=int_val,
                updated_at=sa.func.now()
            )
            .where(tasks.c.priority == string_val)
        )

    # Handle NULL or unexpected values (default to medium)
    connection.execute(
        tasks.update()
        .values(
            priority_int=2,  # medium
            updated_at=sa.func.now()
        )
        .where(
            sa.or_(
                tasks.c.priority_int == None,
                tasks.c.priority.notin_(['low', 'medium', 'high'])
            )
        )
    )

    # Verify transformation
    result = connection.execute(
        sa.select([sa.func.count()])
        .select_from(tasks)
        .where(tasks.c.priority_int == None)
    )
    null_count = result.scalar()

    if null_count > 0:
        raise Exception(f"Migration incomplete: {null_count} tasks have NULL priority_int")

    # Step 3: Drop old column
    op.drop_column('tasks', 'priority')

    # Step 4: Rename new column
    op.alter_column('tasks', 'priority_int', new_column_name='priority')

    # Step 5: Set NOT NULL constraint
    op.alter_column('tasks', 'priority', nullable=False)

    print("✓ Transformed priority from string to integer")


def downgrade():
    """
    Rollback: integer → string
    """
    connection = op.get_bind()

    # Step 1: Remove NOT NULL
    op.alter_column('tasks', 'priority', nullable=True)

    # Step 2: Rename to temp
    op.alter_column('tasks', 'priority', new_column_name='priority_int')

    # Step 3: Add string column
    op.add_column('tasks',
        sa.Column('priority', sa.String(length=20), nullable=True)
    )

    # Step 4: Transform back (integer → string)
    tasks = table('tasks',
        column('priority', sa.String),
        column('priority_int', sa.Integer),
        column('updated_at', sa.DateTime)
    )

    priority_map = {
        1: 'low',
        2: 'medium',
        3: 'high'
    }

    for int_val, string_val in priority_map.items():
        connection.execute(
            tasks.update()
            .values(
                priority=string_val,
                updated_at=sa.func.now()
            )
            .where(tasks.c.priority_int == int_val)
        )

    # Step 5: Drop integer column
    op.drop_column('tasks', 'priority_int')

    # Step 6: Set NOT NULL
    op.alter_column('tasks', 'priority', nullable=False)

    print("✓ Rolled back priority to string format")
```

### 3. Batch Migration with Progress

For large datasets, process in batches:

```python
"""Backfill task estimated_hours based on priority

Revision ID: 5h4c3d6e7f8g
Revises: 4g3b2c5d6e7f
Create Date: 2026-01-07 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

revision = '5h4c3d6e7f8g'
down_revision = '4g3b2c5d6e7f'
branch_labels = None
depends_on = None

BATCH_SIZE = 1000


def upgrade():
    """
    Backfill estimated_hours based on priority:
    - priority 1 (low): 2 hours
    - priority 2 (medium): 4 hours
    - priority 3 (high): 8 hours

    Process in batches for large datasets.
    """
    connection = op.get_bind()

    tasks = table('tasks',
        column('id', sa.String),
        column('priority', sa.Integer),
        column('estimated_hours', sa.Float),
        column('updated_at', sa.DateTime)
    )

    # Get total count
    result = connection.execute(
        sa.select([sa.func.count()])
        .select_from(tasks)
        .where(tasks.c.estimated_hours == None)
    )
    total = result.scalar()

    if total == 0:
        print("✓ No tasks to backfill")
        return

    print(f"Backfilling {total} tasks in batches of {BATCH_SIZE}...")

    processed = 0
    offset = 0

    while True:
        # Get batch of task IDs
        result = connection.execute(
            sa.select([tasks.c.id, tasks.c.priority])
            .where(tasks.c.estimated_hours == None)
            .order_by(tasks.c.id)
            .limit(BATCH_SIZE)
            .offset(offset)
        )

        batch = result.fetchall()

        if not batch:
            break

        # Update batch by priority
        for priority, hours in [(1, 2.0), (2, 4.0), (3, 8.0)]:
            task_ids = [row[0] for row in batch if row[1] == priority]

            if task_ids:
                connection.execute(
                    tasks.update()
                    .values(
                        estimated_hours=hours,
                        updated_at=sa.func.now()
                    )
                    .where(tasks.c.id.in_(task_ids))
                )

        processed += len(batch)
        progress = (processed / total) * 100
        print(f"  Progress: {processed}/{total} ({progress:.1f}%)")

        offset += BATCH_SIZE

    # Verify
    result = connection.execute(
        sa.select([sa.func.count()])
        .select_from(tasks)
        .where(tasks.c.estimated_hours == None)
    )
    remaining = result.scalar()

    if remaining > 0:
        raise Exception(f"Migration incomplete: {remaining} tasks still NULL")

    print(f"✓ Backfilled estimated_hours for {processed} tasks")


def downgrade():
    """
    Rollback: Clear estimated_hours
    """
    connection = op.get_bind()

    tasks = table('tasks',
        column('estimated_hours', sa.Float),
        column('updated_at', sa.DateTime)
    )

    connection.execute(
        tasks.update()
        .values(
            estimated_hours=None,
            updated_at=sa.func.now()
        )
    )

    print("✓ Rolled back estimated_hours backfill")
```

### 4. Enum Migration

Add or remove enum values:

```python
"""Add 'blocked' status to task status enum

Revision ID: 6i5d4e7f8g9h
Revises: 5h4c3d6e7f8g
Create Date: 2026-01-07 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '6i5d4e7f8g9h'
down_revision = '5h4c3d6e7f8g'
branch_labels = None
depends_on = None

# Old enum values
old_values = ['todo', 'in_progress', 'done']
# New enum values (added 'blocked')
new_values = ['todo', 'in_progress', 'blocked', 'done']


def upgrade():
    """
    Add 'blocked' status to task_status enum.

    PostgreSQL doesn't support ALTER TYPE ADD VALUE in transaction,
    so we recreate the enum.
    """
    # For PostgreSQL: Use ALTER TYPE (outside transaction)
    # Note: This won't work in transaction, handle appropriately

    # Option 1: ALTER TYPE (PostgreSQL 9.1+)
    # Run with: op.execute("ALTER TYPE task_status ADD VALUE 'blocked' AFTER 'in_progress'")

    # Option 2: Recreate enum (works in all databases)
    # Step 1: Create new enum
    op.execute("ALTER TABLE tasks ALTER COLUMN status TYPE VARCHAR(20)")

    # Step 2: Drop old enum if exists
    op.execute("DROP TYPE IF EXISTS task_status")

    # Step 3: Create new enum with added value
    task_status_enum = sa.Enum(*new_values, name='task_status')
    task_status_enum.create(op.get_bind(), checkfirst=True)

    # Step 4: Convert column back to enum
    op.execute(
        "ALTER TABLE tasks ALTER COLUMN status TYPE task_status "
        "USING status::task_status"
    )

    print("✓ Added 'blocked' to task_status enum")


def downgrade():
    """
    Remove 'blocked' status.

    WARNING: If any tasks have 'blocked' status, this will fail.
    """
    connection = op.get_bind()

    # Check if any tasks are blocked
    result = connection.execute(
        sa.text("SELECT COUNT(*) FROM tasks WHERE status = 'blocked'")
    )
    blocked_count = result.scalar()

    if blocked_count > 0:
        # Option 1: Fail (safe)
        raise Exception(
            f"Cannot remove 'blocked' status: {blocked_count} tasks are blocked. "
            f"Migrate these tasks to another status first."
        )

        # Option 2: Auto-migrate to 'todo' (dangerous)
        # connection.execute(
        #     "UPDATE tasks SET status = 'todo' WHERE status = 'blocked'"
        # )

    # Recreate enum without 'blocked'
    op.execute("ALTER TABLE tasks ALTER COLUMN status TYPE VARCHAR(20)")
    op.execute("DROP TYPE IF EXISTS task_status")

    task_status_enum = sa.Enum(*old_values, name='task_status')
    task_status_enum.create(op.get_bind(), checkfirst=True)

    op.execute(
        "ALTER TABLE tasks ALTER COLUMN status TYPE task_status "
        "USING status::task_status"
    )

    print("✓ Removed 'blocked' from task_status enum")
```

### 5. JSON Field Migration

Transform JSONB structures:

```python
"""Migrate project metadata JSON structure

Revision ID: 7j6e5f8g9h0i
Revises: 6i5d4e7f8g9h
Create Date: 2026-01-07 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects.postgresql import JSONB
import json

revision = '7j6e5f8g9h0i'
down_revision = '6i5d4e7f8g9h'
branch_labels = None
depends_on = None


def upgrade():
    """
    Migrate metadata JSON structure:

    Old format:
    {
      "tags": "tag1,tag2,tag3",
      "owner": "user@example.com"
    }

    New format:
    {
      "tags": ["tag1", "tag2", "tag3"],
      "owner": {
        "email": "user@example.com",
        "id": null
      }
    }
    """
    connection = op.get_bind()

    projects = table('projects',
        column('id', sa.String),
        column('metadata', JSONB),
        column('updated_at', sa.DateTime)
    )

    # Get all projects with metadata
    result = connection.execute(
        sa.select([projects.c.id, projects.c.metadata])
        .where(projects.c.metadata != None)
    )

    migrated = 0

    for project_id, metadata in result:
        if not metadata:
            continue

        # Transform metadata
        new_metadata = {}

        # Transform tags: string → array
        if 'tags' in metadata and isinstance(metadata['tags'], str):
            new_metadata['tags'] = [
                tag.strip() for tag in metadata['tags'].split(',')
                if tag.strip()
            ]
        elif 'tags' in metadata:
            new_metadata['tags'] = metadata['tags']

        # Transform owner: string → object
        if 'owner' in metadata and isinstance(metadata['owner'], str):
            new_metadata['owner'] = {
                'email': metadata['owner'],
                'id': None
            }
        elif 'owner' in metadata:
            new_metadata['owner'] = metadata['owner']

        # Preserve other fields
        for key, value in metadata.items():
            if key not in ('tags', 'owner'):
                new_metadata[key] = value

        # Update project
        connection.execute(
            projects.update()
            .values(
                metadata=new_metadata,
                updated_at=sa.func.now()
            )
            .where(projects.c.id == project_id)
        )

        migrated += 1

    print(f"✓ Migrated metadata for {migrated} projects")


def downgrade():
    """
    Rollback: array → string, object → string
    """
    connection = op.get_bind()

    projects = table('projects',
        column('id', sa.String),
        column('metadata', JSONB),
        column('updated_at', sa.DateTime)
    )

    result = connection.execute(
        sa.select([projects.c.id, projects.c.metadata])
        .where(projects.c.metadata != None)
    )

    migrated = 0

    for project_id, metadata in result:
        if not metadata:
            continue

        old_metadata = {}

        # Transform tags: array → string
        if 'tags' in metadata and isinstance(metadata['tags'], list):
            old_metadata['tags'] = ','.join(metadata['tags'])
        elif 'tags' in metadata:
            old_metadata['tags'] = metadata['tags']

        # Transform owner: object → string
        if 'owner' in metadata and isinstance(metadata['owner'], dict):
            old_metadata['owner'] = metadata['owner'].get('email', '')
        elif 'owner' in metadata:
            old_metadata['owner'] = metadata['owner']

        # Preserve other fields
        for key, value in metadata.items():
            if key not in ('tags', 'owner'):
                old_metadata[key] = value

        connection.execute(
            projects.update()
            .values(
                metadata=old_metadata,
                updated_at=sa.func.now()
            )
            .where(projects.c.id == project_id)
        )

        migrated += 1

    print(f"✓ Rolled back metadata for {migrated} projects")
```

### 6. Cleanup Migration

Remove obsolete data:

```python
"""Clean up archived projects older than 2 years

Revision ID: 8k7f6g9h0i1j
Revises: 7j6e5f8g9h0i
Create Date: 2026-01-07 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from datetime import datetime, timedelta

revision = '8k7f6g9h0i1j'
down_revision = '7j6e5f8g9h0i'
branch_labels = None
depends_on = None


def upgrade():
    """
    Delete archived projects older than 2 years.

    WARNING: This permanently deletes data.
    Ensure backups exist before running.
    """
    connection = op.get_bind()

    projects = table('projects',
        column('id', sa.String),
        column('status', sa.String),
        column('updated_at', sa.DateTime)
    )

    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=730)  # 2 years

    # Count projects to delete
    result = connection.execute(
        sa.select([sa.func.count()])
        .select_from(projects)
        .where(
            sa.and_(
                projects.c.status == 'archived',
                projects.c.updated_at < cutoff_date
            )
        )
    )
    count_to_delete = result.scalar()

    if count_to_delete == 0:
        print("✓ No archived projects to clean up")
        return

    print(f"⚠️  Deleting {count_to_delete} archived projects older than {cutoff_date.date()}")

    # Delete projects (cascade will delete tasks)
    connection.execute(
        projects.delete()
        .where(
            sa.and_(
                projects.c.status == 'archived',
                projects.c.updated_at < cutoff_date
            )
        )
    )

    print(f"✓ Deleted {count_to_delete} archived projects")


def downgrade():
    """
    Cannot restore deleted data.
    """
    print("⚠️  WARNING: Cannot restore deleted projects. Restore from backup if needed.")
    # No-op: data is permanently deleted
    pass
```

## Best Practices

### ✅ DO

- **Test on staging first**: Always test migrations on copy of production data
- **Add verification**: Check data integrity after migration
- **Batch large operations**: Process in chunks (1000-5000 records)
- **Log progress**: Print progress for long-running migrations
- **Handle errors**: Wrap in try/except, rollback on failure
- **Update timestamps**: Set `updated_at` when changing data
- **Provide rollback**: Make migrations reversible when possible
- **Document limitations**: Note when rollback isn't possible
- **Backup first**: Ensure backups before destructive operations
- **Use table objects**: Not raw SQL (easier to test)

### ❌ DON'T

- Don't run large migrations in single transaction (risk timeout)
- Don't delete data without verification and backups
- Don't assume data format (validate before transforming)
- Don't modify production directly (use migration files)
- Don't skip downgrade implementation
- Don't ignore NULL values (handle explicitly)
- Don't use auto-commit (use explicit commits)
- Don't forget to test rollback

## Migration Checklist

Before running data migration:
- [ ] Migration tested on staging with production-like data
- [ ] Backup created (database dump)
- [ ] Batch size appropriate for dataset
- [ ] Progress logging implemented
- [ ] Verification checks included
- [ ] Error handling in place
- [ ] Rollback script tested
- [ ] Downtime estimated and communicated
- [ ] Monitoring ready (watch for errors)
- [ ] Team notified (in case of issues)

## Testing Migrations

```bash
# Test upgrade
flask db upgrade

# Verify data
flask shell
>>> from app.models import Project
>>> Project.query.filter_by(status=None).count()  # Should be 0

# Test downgrade
flask db downgrade -1

# Verify rollback
flask shell
>>> Project.query.filter_by(status=None).count()  # Should be restored

# Re-upgrade
flask db upgrade
```

## Example Usage

```
@flask-api-expert /generate-data-migration

Type: backfill
Table: projects
Description: Backfill project status based on task completion
Batch Size: 1000

# Agent generates:
# 1. Alembic migration file with revision ID
# 2. Upgrade function with batch processing
# 3. Downgrade function for rollback
# 4. Verification checks
# 5. Progress logging
# 6. Error handling
```

---

**Note**: Always test data migrations on staging environment with production-like data before running on production. Ensure backups exist and team is ready to respond to issues.
