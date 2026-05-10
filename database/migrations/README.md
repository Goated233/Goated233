# Database migrations

Alpha Omega Arcade uses Alembic with SQLAlchemy models as the migration source.

## Common commands

```bash
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "describe change"
```

The initial revision creates all current platform tables: users, profiles, inventory, game sessions/results, leaderboards, economy transactions, clans, quests, notifications, admin roles/permissions, audit logs, punishments, exploit flags, and maintenance state.

For local development, run `python scripts/reset_dev_db.py` to drop/recreate tables and seed starter content.
