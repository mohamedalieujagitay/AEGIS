"""Create the secret files used by Docker Compose (DECISIONS.md D-053).

    python infrastructure/scripts/init_dev_secrets.py [--secrets-dir DIR]

Creates random passwords, the API's server secret key and the Valkey ACL
file in ``secrets/`` at the repository root (gitignored) or in
``--secrets-dir``. Existing files are
never overwritten: running the script again only creates what is missing.
Secret values are never printed.

The ACL file stores SHA-256 hashes of the Valkey passwords, not the
passwords. If it already exists, the script checks that its hashes still
match the password files and stops with an error if they do not, instead of
rewriting it.

Uses only the Python standard library (Python 3.11 or later).
"""

import argparse
import hashlib
import os
import re
import secrets
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SECRETS_DIR = REPOSITORY_ROOT / "secrets"

PASSWORD_FILES = (
    "postgres_superuser_password",
    "postgres_owner_password",
    "postgres_app_password",
    "valkey_api_password",
    "valkey_internal_password",
    "valkey_assessment_password",
    "valkey_healthcheck_password",
    # Server secret for CSRF tokens and rate-limit key names (DECISIONS.md D-065).
    "aegis_secret_key",
)
ACL_FILE = "valkey_users.acl"

# Commands every client needs to connect: AUTH and HELLO are always allowed.
_CONNECT = "+ping +client|setname +client|setinfo +select"
# Sending tasks: kombu declares the queue binding, checks the queue length in
# a transaction and pushes the message (verified with the ACL log, D-055).
_PRODUCER = "+lpush +sadd +smembers +llen +multi +exec"
# Consuming tasks: blocking pop, plus kombu's bookkeeping of unacknowledged
# messages (sorted set, hash and mutex key) and message restore. The mutex is
# released by a Lua script (EVALSHA); a script runs with the calling user's
# ACL, so it can use only these commands on the role's own keys.
_CONSUMER = (
    "+brpop +lpush +rpush +llen +sadd +smembers +del +multi +exec +watch +unwatch"
    " +zadd +zrem +zrange +zrangebyscore +zrevrangebyscore +hset +hget +hdel +set +get +expire"
    " +evalsha +script|load"
)


# Authentication rate limiting (DECISIONS.md D-066). A selector grants these
# commands only on "ratelimit:*" keys: the API user cannot use them on the
# task queues, and cannot read or change anything else. (redis-py's incr()
# sends INCRBY.)
_RATE_LIMIT = "(~ratelimit:* +mget +pttl +incrby +expire +set +del +multi +exec)"


def _namespace_keys(*roles: str) -> str:
    patterns: list[str] = []
    for role in roles:
        patterns += [
            f"~{role}.*",
            f"~_kombu.binding.{role}",
            f"~_kombu.binding_permanent.{role}",
        ]
    return " ".join(patterns)


# User name -> (password file, permissions). Every user starts with no
# commands, no keys and no Pub/Sub channels.
ACL_USERS = {
    "aegis-api": (
        "valkey_api_password",
        f"{_CONNECT} {_PRODUCER} {_namespace_keys('internal', 'assessment')} {_RATE_LIMIT}",
    ),
    "worker-internal": (
        "valkey_internal_password",
        f"{_CONNECT} {_CONSUMER} {_namespace_keys('internal')}",
    ),
    "worker-assessment": (
        "valkey_assessment_password",
        f"{_CONNECT} {_CONSUMER} {_namespace_keys('assessment')}",
    ),
    # Container health check of the valkey service: PING only, no keys and no
    # channels. It has its own password like every other user (D-060).
    "healthcheck": ("valkey_healthcheck_password", "+ping"),
}

_ACL_LINE = re.compile(r"^user (\S+) on #([0-9a-f]{64}) ")


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_new(path: Path, content: str) -> None:
    """Create ``path`` with ``content``; fail instead of replacing an existing file."""
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    # Readable by the container users that receive the file as a Docker
    # secret (bind-mounted, so the container sees the host mode). The
    # directory itself is 0700, so other users on the host cannot reach it.
    path.chmod(0o644)


def build_acl(passwords: dict[str, str]) -> str:
    # Valkey ACL files accept only "user" lines (no comments). Passwords are
    # stored as SHA-256 hashes ("#<hex>").
    lines = [
        "user default off resetkeys resetchannels -@all",
    ]
    for user, (password_file, permissions) in ACL_USERS.items():
        digest = _sha256(passwords[password_file])
        lines.append(f"user {user} on #{digest} resetkeys resetchannels -@all {permissions}")
    return "\n".join(lines) + "\n"


def check_acl(acl: str, passwords: dict[str, str]) -> list[str]:
    """Return the users whose hash in the ACL file does not match their password file."""
    hashes = {
        match.group(1): match.group(2)
        for line in acl.splitlines()
        if (match := _ACL_LINE.match(line)) is not None
    }
    return [
        user
        for user, (password_file, _) in ACL_USERS.items()
        if hashes.get(user) != _sha256(passwords[password_file])
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--secrets-dir", type=Path, default=DEFAULT_SECRETS_DIR)
    args = parser.parse_args(argv)
    directory: Path = args.secrets_dir

    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name == "posix":
        directory.chmod(0o700)

    passwords: dict[str, str] = {}
    for name in PASSWORD_FILES:
        path = directory / name
        if path.exists():
            print(f"kept     {name}")
        else:
            _write_new(path, secrets.token_urlsafe(32))
            print(f"created  {name}")
        passwords[name] = path.read_text(encoding="utf-8").strip()
        if not passwords[name]:
            print(f"error: {path} is empty", file=sys.stderr)
            return 1

    acl_path = directory / ACL_FILE
    if acl_path.exists():
        existing = acl_path.read_text(encoding="utf-8")
        mismatched = check_acl(existing, passwords)
        if mismatched:
            print(
                f"error: {acl_path} does not match the password files for: "
                f"{', '.join(mismatched)}. It was not changed. Delete it to regenerate it.",
                file=sys.stderr,
            )
            return 1
        if existing != build_acl(passwords):
            print(
                f"error: {acl_path} is out of date with the current ACL rules. It was not "
                "changed. Delete it and run this script again to regenerate it (the passwords "
                "are kept), then recreate the valkey container.",
                file=sys.stderr,
            )
            return 1
        print(f"kept     {ACL_FILE}")
    else:
        _write_new(acl_path, build_acl(passwords))
        print(f"created  {ACL_FILE}")

    print(f"Secrets directory: {directory}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
