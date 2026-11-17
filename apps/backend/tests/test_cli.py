"""The administration CLI (``python -m app.cli``)."""

import io
import logging
from collections.abc import Iterator
from datetime import timedelta

import pytest
from helpers import FakeClock
from sqlalchemy import select

from app import cli
from app.core.config import Settings
from app.core.security import verify_password
from app.database.session import Database
from app.models.session import UserSession
from app.models.user import User
from app.services import accounts

PASSWORD = "correct horse battery staple"


@pytest.fixture
def database(migrated_settings: Settings, monkeypatch: pytest.MonkeyPatch) -> Iterator[Database]:
    """Point the CLI's settings (read from the environment) at the test database."""
    for name, value in {
        "AEGIS_ENVIRONMENT": "test",
        "AEGIS_DATABASE_HOST": migrated_settings.database_host or "",
        "AEGIS_DATABASE_PORT": str(migrated_settings.database_port),
        "AEGIS_DATABASE_USER": migrated_settings.database_user,
        "AEGIS_DATABASE_NAME": migrated_settings.database_name,
        "AEGIS_DATABASE_SSLMODE": "disable",
    }.items():
        monkeypatch.setenv(name, value)
    database = Database(migrated_settings)
    yield database
    database.dispose()


def run(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], *argv: str, stdin: str = ""
) -> tuple[int, str, str]:
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
    code = cli.main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


def users(database: Database) -> list[User]:
    with database.session() as db:
        return list(db.scalars(select(User)))


def test_create_admin_from_standard_input(
    database: Database, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, err = run(
        monkeypatch,
        capsys,
        "create-admin",
        "--email",
        "Admin@Example.com",
        "--username",
        "Admin",
        "--password-stdin",
        stdin=PASSWORD + "\n",
    )
    assert code == 0
    assert out == "Created instance administrator admin (admin@example.com).\n"
    assert '"event": "database.engine_created"' in err  # logs go to standard error
    assert PASSWORD not in out
    [user] = users(database)
    assert user.is_instance_admin
    assert verify_password(user.password_hash, PASSWORD)


def test_create_user_prompts_twice(
    database: Database, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    answers = iter([PASSWORD, PASSWORD])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(answers))
    code, out, _ = run(
        monkeypatch, capsys, "create-user", "--email", "u@example.com", "--username", "user1"
    )
    assert code == 0
    assert "Created user user1" in out
    [user] = users(database)
    assert not user.is_instance_admin


def test_mismatched_prompts_are_refused(
    database: Database, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    answers = iter([PASSWORD, PASSWORD + "x"])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(answers))
    code, _, err = run(
        monkeypatch, capsys, "create-user", "--email", "u@example.com", "--username", "user1"
    )
    assert code == 1
    assert "do not match" in err
    assert users(database) == []


@pytest.mark.parametrize(
    ("argv", "stdin", "message"),
    [
        (["--email", "bad", "--username", "user1"], PASSWORD, "valid email"),
        (["--email", "u@example.com", "--username", "x"], PASSWORD, "3 to 32"),
        (["--email", "u@example.com", "--username", "user1"], "short", "at least 12"),
        (["--email", "u@example.com", "--username", "user1"], "", "No password"),
    ],
)
def test_invalid_input_is_reported(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    stdin: str,
    message: str,
) -> None:
    code, _, err = run(
        monkeypatch, capsys, "create-user", *argv, "--password-stdin", stdin=stdin + "\n"
    )
    assert code == 1
    assert message in err
    assert "Traceback" not in err
    assert users(database) == []


def test_duplicate_accounts_are_refused(
    database: Database, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = ["create-user", "--email", "u@example.com", "--username", "user1", "--password-stdin"]
    assert run(monkeypatch, capsys, *argv, stdin=PASSWORD)[0] == 0
    code, _, err = run(monkeypatch, capsys, *argv, stdin=PASSWORD)
    assert code == 1
    assert err.strip()
    assert len(users(database)) == 1


def test_reset_password_signs_out_every_session(
    database: Database, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from app.core import clock
    from app.services.sessions import SessionPolicy, create_session

    with database.session() as db:
        user = accounts.create_account(
            db, email="u@example.com", username="user1", password=PASSWORD
        )
        policy = SessionPolicy.from_settings(Settings())
        for _ in range(2):
            create_session(db, user, policy, clock.utcnow(), client_ip=None, user_agent=None)

    new_password = "a completely different passphrase"
    code, out, _ = run(
        monkeypatch,
        capsys,
        "reset-password",
        "--email",
        "U@example.com",
        "--password-stdin",
        stdin=new_password,
    )
    assert code == 0
    assert "2 session(s) signed out" in out
    [user] = users(database)
    assert verify_password(user.password_hash, new_password)
    with database.session() as db:
        assert all(s.revoked_at is not None for s in db.scalars(select(UserSession)))


def test_reset_password_for_an_unknown_account(
    database: Database, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, _, err = run(
        monkeypatch, capsys, "reset-password", "--email", "x@example.com", "--password-stdin"
    )
    assert code == 1
    assert "No account" in err


def test_registration_switch(
    database: Database, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert "disabled" in run(monkeypatch, capsys, "registration", "show")[1]
    assert "enabled" in run(monkeypatch, capsys, "registration", "enable")[1]
    with database.session() as db:
        assert accounts.registration_enabled(db)
    assert "disabled" in run(monkeypatch, capsys, "registration", "disable")[1]


def test_purge_expired(
    database: Database, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, _ = run(monkeypatch, capsys, "purge-expired")
    assert code == 0
    assert out == (
        "Removed 0 ended session(s), 0 used or expired reset token(s) "
        "and 0 ended trusted device(s).\n"
    )


def test_passwords_are_never_command_line_arguments() -> None:
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(
            ["create-admin", "--email", "a@example.com", "--username", "a", "--password", "x"]
        )


def test_cli_logs_contain_no_password(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.DEBUG):
        run(
            monkeypatch,
            capsys,
            "create-admin",
            "--email",
            "a@example.com",
            "--username",
            "admin",
            "--password-stdin",
            stdin=PASSWORD,
        )
    assert PASSWORD not in caplog.text


def test_cli_password_reset_records_the_operator_without_creating_an_account(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The operator is the OS account name, unverified; no identity is invented (D-072)."""
    with database.session() as db:
        accounts.create_account(db, email="u@example.com", username="user1", password=PASSWORD)
    monkeypatch.setattr(cli, "_operator", lambda: "ops-account")
    with caplog.at_level(logging.INFO, logger="app.security"):
        code, _, _ = run(
            monkeypatch,
            capsys,
            "reset-password",
            "--email",
            "u@example.com",
            "--password-stdin",
            stdin="another passphrase for ops\n",
        )
    assert code == 0
    [record] = [
        r for r in caplog.records if getattr(r, "event", None) == "auth.password_reset_completed"
    ]
    assert record.__dict__["operator"] == "ops-account"
    assert record.__dict__["method"] == "cli"
    assert len(users(database)) == 1  # no account for the operator


def test_purge_removes_reset_tokens_that_ended_long_ago(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    clock: FakeClock,
) -> None:
    from app.services import password_reset

    with database.session() as db:
        user = accounts.create_account(
            db, email="u@example.com", username="user1", password=PASSWORD
        )
        password_reset.issue_reset_token(
            db, user, issued_by=None, method="admin", ttl=timedelta(minutes=60), now=clock()
        )
    clock.advance(days=8)
    code, out, _ = run(monkeypatch, capsys, "purge-expired")
    assert code == 0
    assert out == (
        "Removed 0 ended session(s), 1 used or expired reset token(s) "
        "and 0 ended trusted device(s).\n"
    )
