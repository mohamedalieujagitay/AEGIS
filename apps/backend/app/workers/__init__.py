"""Celery worker roles (SYSTEM_ARCHITECTURE §6, DECISIONS.md D-020, D-055).

- ``celery_app``: the Celery application factory shared by the API and both roles.
- ``assessment``: the untrusted assessment worker (worker-side, §4.5).
- ``internal``: the trusted internal worker.
- ``heartbeat`` and ``healthcheck``: worker container health checks.

Only ``assessment`` is worker-side in the sense of the import contract, but
the modules it imports from here (``celery_app``, ``heartbeat``) must also
stay free of database code; import-linter checks this transitively.
"""
