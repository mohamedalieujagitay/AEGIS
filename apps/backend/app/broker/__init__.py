"""Valkey message broker connection (DECISIONS.md D-009, D-055).

Used by the API for its readiness check and by the Celery application in
``app.workers``. It never imports database code, so worker-side packages may
use it (SYSTEM_ARCHITECTURE §4.5).
"""
