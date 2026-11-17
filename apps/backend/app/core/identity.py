"""Account identifiers and the password policy (DECISIONS.md D-063).

Email addresses and usernames are normalized before they are stored or
compared, so the same person cannot register twice with different letter
case. Email addresses are only checked for a valid structure: AEGIS sends no
email in v0.1.0 and performs no DNS lookups (D-019).
"""

import re
from typing import Final

EMAIL_MAX_LENGTH: Final = 254
USERNAME_PATTERN: Final = re.compile(r"[a-z0-9._-]{3,32}")
PASSWORD_MIN_LENGTH: Final = 12
PASSWORD_MAX_LENGTH: Final = 128

_LOCAL_PART: Final = re.compile(r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]{1,64}")
_DOMAIN_LABEL: Final = re.compile(r"(?!-)[A-Za-z0-9-]{1,63}(?<!-)")


def normalize_email(value: str) -> str:
    """Return the normalized address, or raise ``ValueError`` if it is not valid.

    The whole address is lower-cased. International domain names are
    converted to their ASCII (IDNA) form.
    """
    candidate = value.strip()
    if candidate.count("@") != 1:
        raise ValueError("Enter a valid email address.")
    local, domain = candidate.split("@")
    if not _LOCAL_PART.fullmatch(local) or local.startswith(".") or local.endswith("."):
        raise ValueError("Enter a valid email address.")
    if ".." in local:
        raise ValueError("Enter a valid email address.")
    try:
        ascii_domain = domain.encode("idna").decode("ascii")
    except UnicodeError as error:
        raise ValueError("Enter a valid email address.") from error
    labels = ascii_domain.split(".")
    if len(labels) < 2 or not all(_DOMAIN_LABEL.fullmatch(label) for label in labels):
        raise ValueError("Enter a valid email address.")
    normalized = f"{local}@{ascii_domain}".lower()
    if len(normalized) > EMAIL_MAX_LENGTH:
        raise ValueError("Enter a valid email address.")
    return normalized


def normalize_email_for_lookup(value: str) -> str:
    """The form used to find an account or to key rate limits (DECISIONS.md D-071).

    The same normalization as :func:`normalize_email`, so ``user@Bücher.example``
    and ``user@xn--bcher-kva.example`` name the same account and share one set
    of rate-limit counters. Input that is not a valid address never raises: it
    is only lower-cased, which cannot match a stored address, so sign-in fails
    with the usual generic error.
    """
    try:
        return normalize_email(value)
    except ValueError:
        if any(ord(character) < 32 or ord(character) == 127 for character in value):
            # Control characters cannot be stored (PostgreSQL rejects NUL) and never match.
            return ""
        return value.strip().lower()


def normalize_username(value: str) -> str:
    """Return the lower-cased username, or raise ``ValueError`` if it is not valid."""
    candidate = value.strip().lower()
    if not USERNAME_PATTERN.fullmatch(candidate):
        raise ValueError("Use 3 to 32 characters: letters, digits, dots, hyphens and underscores.")
    return candidate


def password_problems(password: str, *, email: str, username: str) -> list[str]:
    """Reasons why ``password`` is not acceptable for this account (empty if it is).

    Length rules follow NIST SP 800-63B: no composition rules, at least 12
    characters, at most 128. Passwords that contain the username or the
    local part of the email address are rejected.
    """
    problems: list[str] = []
    if len(password) < PASSWORD_MIN_LENGTH:
        problems.append(f"Use at least {PASSWORD_MIN_LENGTH} characters.")
    if len(password) > PASSWORD_MAX_LENGTH:
        problems.append(f"Use at most {PASSWORD_MAX_LENGTH} characters.")
    lowered = password.lower()
    local_part = email.split("@", 1)[0].lower()
    if username and username.lower() in lowered:
        problems.append("Do not include your username.")
    if len(local_part) >= 3 and local_part in lowered:
        problems.append("Do not include your email address.")
    return problems
