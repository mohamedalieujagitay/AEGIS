"""PostgreSQL access through SQLAlchemy 2.x (synchronous API) and psycopg 3.

- ``config``: builds the connection URL from settings.
- ``engine``: creates the engine and its connection pool.
- ``session``: the ``Database`` lifecycle object and the per-request session.
- ``base``: the declarative ``Base`` and model conventions.
- ``errors``: maps database failures to safe API errors.

Worker-side code must never import this package (SYSTEM_ARCHITECTURE.md §4.5).
"""
