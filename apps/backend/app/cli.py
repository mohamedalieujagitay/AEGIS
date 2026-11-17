"""Server-side administration commands (PRD FR-AUTH-005, FR-AUTH-006; DECISIONS.md D-061).

    python -m app.cli create-admin --email EMAIL --username NAME
    python -m app.cli create-user --email EMAIL --username NAME
    python -m app.cli reset-password --email EMAIL
    python -m app.cli registration {show,enable,disable}
    python -m app.cli purge-expired

In Docker Compose, run them in the API container, for example
``docker compose exec backend python -m app.cli create-admin ...``.

Logs go to standard error; results to standard output.

Passwords are never accepted as command-line arguments (they would be visible
in the process list and shell history). They are read with a hidden prompt,
entered twice, or, for automation, from standard input with
``--password-stdin``. Nothing secret is printed.
"""

import argparse
import getpass
import sys
from collections.abc import Callable, Sequence

from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.identity import normalize_email, normalize_username
from app.core.logging import configure_logging
from app.core.security import configure_password_hashing
from app.database.session import Database
from app.services import accounts, password_reset, sessions, trusted_devices

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2


class CliError(Exception):
    """An error reported to the operator without a traceback."""


def read_password(use_stdin: bool, prompt: Callable[[str], str] | None = None) -> str:
    if use_stdin:
        password = sys.stdin.readline().rstrip("\r\n")
        if not password:
            raise CliError("No password on standard input.")
        return password
    ask = prompt or getpass.getpass
    first = ask("Password: ")
    if first != ask("Repeat password: "):
        raise CliError("The passwords do not match.")
    return first


def _identity(args: argparse.Namespace) -> tuple[str, str]:
    try:
        return normalize_email(args.email), normalize_username(args.username)
    except ValueError as error:
        raise CliError(str(error)) from error


def _create(db: Session, args: argparse.Namespace, admin: bool) -> str:
    email, username = _identity(args)
    password = read_password(args.password_stdin)
    user = accounts.create_account(
        db, email=email, username=username, password=password, instance_admin=admin
    )
    role = "instance administrator" if admin else "user"
    return f"Created {role} {user.username} ({user.email})."


def _operator() -> str:
    """The operating-system account running this command (not verified; see D-072)."""
    try:
        return getpass.getuser()
    except (OSError, KeyError):
        return "unknown"


def _reset(db: Session, args: argparse.Namespace) -> str:
    try:
        email = normalize_email(args.email)
    except ValueError as error:
        raise CliError(str(error)) from error
    user = accounts.find_user_by_email(db, email)
    if user is None:
        raise CliError("No account uses this email address.")
    password = read_password(args.password_stdin)
    revoked = password_reset.reset_password_directly(
        db, user, password, clock.utcnow(), operator=_operator()
    )
    return f"Password reset for {user.username}; {revoked} session(s) signed out."


def _registration(db: Session, args: argparse.Namespace) -> str:
    if args.action != "show":
        accounts.set_registration_enabled(db, args.action == "enable")
    state = "enabled" if accounts.registration_enabled(db) else "disabled"
    return f"Open registration is {state}."


def _purge(db: Session, _: argparse.Namespace) -> str:
    now = clock.utcnow()
    removed_sessions = sessions.purge_expired_sessions(db, now)
    removed_tokens = password_reset.purge_ended_reset_tokens(db, now)
    removed_devices = trusted_devices.purge_ended(db, now)
    return (
        f"Removed {removed_sessions} ended session(s), "
        f"{removed_tokens} used or expired reset token(s) and "
        f"{removed_devices} ended trusted device(s)."
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        ("create-admin", "Create an instance administrator (the first account of an instance)."),
        ("create-user", "Create a user account."),
    ):
        command = commands.add_parser(name, help=text, description=text)
        command.add_argument("--email", required=True)
        command.add_argument("--username", required=True)
        command.add_argument(
            "--password-stdin", action="store_true", help="read the password from standard input"
        )
    reset = commands.add_parser(
        "reset-password",
        help="Set a new password for a user and sign out all their sessions.",
    )
    reset.add_argument("--email", required=True)
    reset.add_argument("--password-stdin", action="store_true")
    registration = commands.add_parser("registration", help="Show or change open registration.")
    registration.add_argument("action", choices=["show", "enable", "disable"])
    commands.add_parser(
        "purge-expired",
        help="Delete sessions, reset tokens and trusted devices that ended more than 7 days ago.",
    )
    return parser


HANDLERS: dict[str, Callable[[Session, argparse.Namespace], str]] = {
    "create-admin": lambda db, args: _create(db, args, admin=True),
    "create-user": lambda db, args: _create(db, args, admin=False),
    "reset-password": _reset,
    "registration": _registration,
    "purge-expired": _purge,
}


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    configure_logging(settings, service="aegis-cli", stream=sys.stderr)
    configure_password_hashing(settings.password_hash_concurrency)
    database = Database(settings)
    try:
        with database.session() as db:
            message = HANDLERS[args.command](db, args)
    except accounts.PasswordRejectedError as error:
        print("The password was not accepted: " + " ".join(error.problems), file=sys.stderr)
        return EXIT_ERROR
    except (CliError, AppError) as error:
        print(str(error) if isinstance(error, CliError) else error.message, file=sys.stderr)
        return EXIT_ERROR
    finally:
        database.dispose()
    print(message)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
