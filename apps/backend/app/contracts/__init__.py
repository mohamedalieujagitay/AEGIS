"""Job and result message schemas shared by the API and the workers.

Empty until worker job signing and result ingestion are implemented.

Worker-side package (SYSTEM_ARCHITECTURE §4.5, DECISIONS D-010). It must
not import ``app.database``, ``app.models``, ``app.services``, ``app.api``,
``sqlalchemy``, ``psycopg`` or ``alembic``. An import-linter contract in
``pyproject.toml`` enforces this in CI.
"""
