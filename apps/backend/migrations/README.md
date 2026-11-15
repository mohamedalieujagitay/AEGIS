# Database migrations

Alembic migrations for the AEGIS PostgreSQL schema. Every schema change must have a migration, and migrations are version-controlled.

The connection is configured with the `AEGIS_DATABASE_*` environment variables (see `apps/backend/.env.example`), never in `alembic.ini`.

Run from `apps/backend`:

```bash
alembic upgrade head                                   # apply all migrations
alembic downgrade -1                                   # revert the latest migration
alembic revision --autogenerate -m "add example table" # generate from model changes
alembic check                                          # fail if models and migrations differ
alembic upgrade head --sql                             # print SQL without connecting
```

Rules:

- Register new model modules in `app/models/__init__.py`, or autogenerate will not see them.
- Always review generated migrations before committing them.
- Every migration must implement `downgrade()`.
- Destructive migrations (dropping tables or columns with data) need explicit approval (CONTRIBUTING.md).
- Never edit a migration that has been committed and applied; add a new one.
