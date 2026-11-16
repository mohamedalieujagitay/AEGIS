"""Assessment worker role (untrusted).

The Celery entry point is ``worker`` (roadmap task 1.5). No assessment
engines exist yet; they are added by Phases 03 and 04.

Worker-side package (SYSTEM_ARCHITECTURE §4.5, DECISIONS D-010). It must
not import ``app.database``, ``app.models``, ``app.services``, ``app.api``,
``sqlalchemy``, ``psycopg`` or ``alembic``. An import-linter contract in
``pyproject.toml`` enforces this in CI.
"""
