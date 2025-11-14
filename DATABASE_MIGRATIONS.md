# Database Migrations Guide

This project uses **Alembic** for database schema version control and migrations.

## Quick Start

### Apply Migrations (PostgreSQL)
```bash
# Using helper script (recommended)
python migrate.py upgrade

# Or directly with Alembic
alembic upgrade head
```

### Check Current Migration Version
```bash
python migrate.py current
# Output: da45db127282 (head)
```

### View Migration History
```bash
python migrate.py history
```

## Creating New Migrations

### Step 1: Create Migration File
```bash
# Using helper script
python migrate.py create add_new_column

# Or directly with Alembic
alembic revision -m "add_new_column"
```

This creates a file in `alembic/versions/` with `upgrade()` and `downgrade()` functions.

### Step 2: Edit Migration File
Edit the generated file in `alembic/versions/`:

```python
def upgrade() -> None:
    """Add new column to signals table"""
    op.add_column('signals', 
        sa.Column('new_field', sa.String(50), nullable=True)
    )

def downgrade() -> None:
    """Remove new column from signals table"""
    op.drop_column('signals', 'new_field')
```

### Step 3: Apply Migration
```bash
python migrate.py upgrade
```

## Migration Commands

| Command | Description |
|---------|-------------|
| `python migrate.py upgrade` | Apply all pending migrations |
| `python migrate.py downgrade` | Rollback last migration |
| `python migrate.py current` | Show current migration version |
| `python migrate.py history` | Show all migrations |
| `python migrate.py create <msg>` | Create new migration |

## Direct Alembic Commands

### Upgrade to specific revision
```bash
alembic upgrade <revision_id>
```

### Downgrade to specific revision
```bash
alembic downgrade <revision_id>
```

### Show SQL without executing
```bash
alembic upgrade head --sql
```

## Database Schema

### Current Tables
1. **signals** - Main signal history (LONG/SHORT/NEUTRAL)
2. **signal_outcomes** - AI verdict accuracy tracking
3. **hype_history** - Social sentiment and pump risk tracking

### Schema Location
- **PostgreSQL**: Managed by Alembic migrations (`alembic/versions/`)
- **SQLite**: Manual schema in `app/storage/database.py` (for Replit compatibility)

## Migration Workflow

### For Schema Changes:
1. **Create migration**: `python migrate.py create my_change`
2. **Edit migration file**: Add `upgrade()` and `downgrade()` logic
3. **Test locally**: `python migrate.py upgrade`
4. **Verify**: Check database with `psql` or database tool
5. **Commit**: Add migration file to git

### For Team Collaboration:
1. **Pull latest code**: `git pull`
2. **Apply migrations**: `python migrate.py upgrade`
3. **Create new migration**: `python migrate.py create my_feature`
4. **Push to repo**: `git push`

## Troubleshooting

### "relation already exists" error
Database schema already exists. Mark current state as baseline:
```bash
alembic stamp head
```

### SSL connection issues
Alembic env.py automatically handles PostgreSQL SSL mode conversion.

### Check migration status
```bash
python migrate.py current
# Should show: da45db127282 (head)
```

### Reset migrations (DANGER: Data loss!)
```bash
# Drop all tables
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Re-run migrations
python migrate.py upgrade
```

## Architecture

```
alembic/
├── versions/           # Migration files
│   └── 20251114_1335_da45db127282_initial_schema.py
├── env.py             # Alembic environment (async PostgreSQL)
└── script.py.mako     # Migration template

alembic.ini            # Alembic configuration
migrate.py             # Helper script (user-friendly)
```

## Best Practices

✅ **DO:**
- Always create migrations for schema changes
- Write both `upgrade()` and `downgrade()` functions
- Test migrations locally before committing
- Use descriptive migration messages
- Review generated SQL before applying

❌ **DON'T:**
- Modify applied migrations in production
- Skip migrations or apply them out of order
- Manually edit database schema (use migrations)
- Delete migration files from version control

## PostgreSQL vs SQLite

| Feature | PostgreSQL | SQLite |
|---------|-----------|--------|
| Migrations | Alembic managed | Manual schema |
| Location | Neon database | `cryptosatx.db` file |
| Schema updates | `python migrate.py upgrade` | Auto on connect |
| Version control | Yes (Alembic) | No |

## Integration with Application

The application checks for migrations on startup:

```python
# app/storage/database.py
async def init_schema(self):
    if self.use_postgres:
        # Check if alembic_version table exists
        result = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables 
             WHERE table_name = 'alembic_version')"
        )
        if not result:
            print("[WARNING] Run: alembic upgrade head")
```

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL asyncpg](https://magicstack.github.io/asyncpg/)
