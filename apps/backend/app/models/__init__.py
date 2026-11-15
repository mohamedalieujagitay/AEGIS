"""ORM model registry.

Import every model module here so its tables are registered on
``app.database.base.Base.metadata``. Alembic imports this package to compare
the models with the database when generating migrations.

No business models exist yet: they are added by the roadmap phases that
build each feature (Phase 02 onwards).
"""
