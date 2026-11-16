"""Business logic used by API routes and the internal worker.

The first service is the readiness check (``health``, roadmap task 1.5).
Worker-side packages must not import this package (SYSTEM_ARCHITECTURE §4.5).
"""
