"""AEGIS backend application.

Package layout (SYSTEM_ARCHITECTURE.md §4.1). Packages are added when the
roadmap task that needs them begins:

- ``app.main``: application factory.
- ``app.api``: HTTP routing. Versioned public routes live in ``app.api.v1``.
- ``app.core``: cross-cutting concerns such as configuration.
"""

__version__ = "0.1.0"
