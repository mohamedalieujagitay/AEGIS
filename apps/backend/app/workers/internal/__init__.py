"""Internal worker role (trusted).

Runs backend work that must not happen inside an API request, such as report
generation and expiry jobs. It has database access and no outbound internet
access, and never runs assessment engines or contacts assessment targets
(SYSTEM_ARCHITECTURE §6.1, DECISIONS.md D-020). No tasks exist yet.
"""
