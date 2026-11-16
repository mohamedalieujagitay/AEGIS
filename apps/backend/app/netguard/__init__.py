"""Network destination validation used by assessment engines.

Empty until scope enforcement is implemented (Phase 03).

Worker-side package (SYSTEM_ARCHITECTURE §4.5, DECISIONS D-010). It must
not import ``app.database``, ``app.models``, ``app.services``, ``app.api``,
``sqlalchemy``, ``psycopg`` or ``alembic``. An import-linter contract in
``pyproject.toml`` enforces this in CI.
"""
