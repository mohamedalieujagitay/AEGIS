"""Structured security events (DECISIONS.md D-067).

Authentication events are written to the ``app.security`` logger with a
stable ``event`` name, so they can be collected and alerted on. Persistent
audit-log storage is roadmap task 2.6.

Never pass passwords, tokens, cookies, session identifiers or reset tokens.
As a safety net, the log formatter redacts fields whose names look sensitive
(``app.core.logging``), which is why identifiers are named ``user_id``,
``actor_id`` and ``client_ip``.
"""

import logging

logger = logging.getLogger("app.security")


def security_event(
    event: str, message: str, *, level: int = logging.INFO, **fields: object
) -> None:
    logger.log(level, message, extra={"event": event, **fields})
