"""Alembic configuration and migration tests against a disposable PostgreSQL."""

import re
import shutil
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, DateTime, MetaData, String, inspect, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import Settings
from app.database.base import NAMING_CONVENTION, Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.database.session import Database

BACKEND_DIR = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_DIR / "alembic.ini"
MIGRATIONS_DIR = BACKEND_DIR / "migrations"


def _config(
    connection: Connection | None = None,
    script_location: Path = MIGRATIONS_DIR,
    target_metadata: MetaData | None = None,
) -> Config:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(script_location))
    config.attributes["configure_logger"] = False
    if connection is not None:
        config.attributes["connection"] = connection
    if target_metadata is not None:
        config.attributes["target_metadata"] = target_metadata
    return config


@contextmanager
def _connection(settings: Settings) -> Iterator[Connection]:
    database = Database(settings)
    try:
        with database.engine.begin() as connection:
            yield connection
    finally:
        database.dispose()


def test_configuration_contains_no_credentials() -> None:
    ini = ALEMBIC_INI.read_text(encoding="utf-8")
    assert "sqlalchemy.url" not in ini
    assert not re.search(r"postgres(ql)?(\+\w+)?://", ini)
    env = (MIGRATIONS_DIR / "env.py").read_text(encoding="utf-8")
    assert not re.search(r"postgres(ql)?(\+\w+)?://", env)


def test_migration_history_is_linear() -> None:
    scripts = ScriptDirectory.from_config(_config())
    assert len(scripts.get_heads()) == 1
    assert len(scripts.get_bases()) == 1
    for revision in scripts.walk_revisions():
        source = Path(revision.path).read_text(encoding="utf-8")
        assert "def upgrade()" in source
        assert "def downgrade()" in source


def test_upgrade_and_downgrade(database_settings: Settings) -> None:
    head = ScriptDirectory.from_config(_config()).get_current_head()

    with _connection(database_settings) as connection:
        command.upgrade(_config(connection), "head")
        current = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert current == head

    with _connection(database_settings) as connection:
        command.downgrade(_config(connection), "base")
        assert connection.execute(text("SELECT count(*) FROM alembic_version")).scalar_one() == 0


def test_models_and_migrations_are_in_sync(database_settings: Settings) -> None:
    import app.models  # noqa: F401  (registers every model)

    with _connection(database_settings) as connection:
        command.upgrade(_config(connection), "head")
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert differences == []


def test_migrations_read_connection_from_environment(
    database_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name, value in {
        "AEGIS_ENVIRONMENT": "test",
        "AEGIS_DATABASE_HOST": str(database_settings.database_host),
        "AEGIS_DATABASE_PORT": str(database_settings.database_port),
        "AEGIS_DATABASE_USER": database_settings.database_user,
        "AEGIS_DATABASE_NAME": database_settings.database_name,
        "AEGIS_DATABASE_SSLMODE": "disable",
    }.items():
        monkeypatch.setenv(name, value)

    command.upgrade(_config(), "head")  # no connection supplied: env.py uses settings

    with _connection(database_settings) as connection:
        assert inspect(connection).has_table("alembic_version")


def test_offline_mode_generates_sql_without_connecting(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "test")
    monkeypatch.setenv("AEGIS_DATABASE_HOST", "unreachable.invalid")
    command.upgrade(_config(), "head", sql=True)
    output = capsys.readouterr().out
    assert "CREATE TABLE alembic_version" in output


def test_a_migration_can_be_generated_and_applied(
    database_settings: Settings, tmp_path: Path
) -> None:
    """Autogenerate a migration for a new model in a copy of the scripts, then apply it."""
    script_location = tmp_path / "migrations"
    shutil.copytree(MIGRATIONS_DIR, script_location, ignore=shutil.ignore_patterns("__pycache__"))

    # The demo model is added to a copy of the application's metadata, so
    # autogenerate sees the existing tables and only adds the new one.
    import app.models  # noqa: F401  (registers every model)

    demo_metadata = MetaData(naming_convention=NAMING_CONVENTION)
    for table in Base.metadata.sorted_tables:
        table.to_metadata(demo_metadata)

    class DemoBase(Base):
        __abstract__ = True
        metadata = demo_metadata

    class DemoItem(UUIDPrimaryKeyMixin, TimestampMixin, DemoBase):
        __tablename__ = "demo_items"
        name: Mapped[str] = mapped_column(String(100), unique=True)

    metadata = DemoItem.metadata

    with _connection(database_settings) as connection:
        command.upgrade(_config(connection, script_location), "head")

    with _connection(database_settings) as connection:
        revision = command.revision(
            _config(connection, script_location, metadata),
            message="add demo items",
            autogenerate=True,
        )
    assert revision is not None
    assert not isinstance(revision, list)
    generated = Path(revision.path).read_text(encoding="utf-8")
    assert any(f"op.create_table({quote}demo_items{quote}" in generated for quote in ("'", '"'))
    assert "pk_demo_items" in generated
    assert "uq_demo_items_name" in generated

    with _connection(database_settings) as connection:
        command.upgrade(_config(connection, script_location, metadata), "head")
    with _connection(database_settings) as connection:
        inspector = inspect(connection)
        assert inspector.has_table("demo_items")
        columns = {c["name"]: c for c in inspector.get_columns("demo_items")}
        created_at_type = columns["created_at"]["type"]
        assert isinstance(created_at_type, DateTime)
        assert created_at_type.timezone is True

    with _connection(database_settings) as connection:
        command.downgrade(_config(connection, script_location, metadata), "-1")
    with _connection(database_settings) as connection:
        assert not inspect(connection).has_table("demo_items")

    # The repository's migration directory was not modified.
    assert not any(MIGRATIONS_DIR.joinpath("versions").glob("*demo_items*"))


# --- Migration metadata permissions (DECISIONS.md D-054, D-060) -------------


@contextmanager
def _deployment_roles(settings: Settings) -> Iterator[tuple[str, str]]:
    """Owner and runtime roles set up like infrastructure/docker/postgres/initdb.

    The runtime role gets data access to every table the owner creates
    through default privileges, exactly as in a deployment. Both roles are
    removed afterwards.
    """
    suffix = uuid.uuid4().hex[:8]
    owner, app_role = f"test_owner_{suffix}", f"test_app_{suffix}"
    database = Database(settings)
    try:
        with database.engine.begin() as connection:
            for role in (owner, app_role):
                connection.execute(text(f'CREATE ROLE "{role}" LOGIN'))
            connection.execute(text(f'ALTER SCHEMA public OWNER TO "{owner}"'))
            connection.execute(text(f'GRANT USAGE ON SCHEMA public TO "{app_role}"'))
            connection.execute(
                text(
                    f'ALTER DEFAULT PRIVILEGES FOR ROLE "{owner}" IN SCHEMA public '
                    f'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "{app_role}"'
                )
            )
        yield owner, app_role
    finally:
        with database.engine.begin() as connection:
            connection.execute(text(f'ALTER SCHEMA public OWNER TO "{settings.database_user}"'))
            for role in (owner, app_role):
                connection.execute(
                    text(f'REASSIGN OWNED BY "{role}" TO "{settings.database_user}"')
                )
                connection.execute(text(f'DROP OWNED BY "{role}"'))
                connection.execute(text(f'DROP ROLE "{role}"'))
        database.dispose()


def _as_role(settings: Settings, role: str, sql: str) -> None:
    database = Database(settings.model_copy(update={"database_user": role}))
    try:
        with database.engine.begin() as connection:
            connection.execute(text(sql))
    finally:
        database.dispose()


def test_runtime_role_cannot_access_migration_metadata(database_settings: Settings) -> None:
    with _deployment_roles(database_settings) as (owner, app_role):
        owner_settings = database_settings.model_copy(update={"database_user": owner})
        with _connection(owner_settings) as connection:
            command.upgrade(_config(connection), "head")

        for sql in (
            "SELECT version_num FROM alembic_version",
            "UPDATE alembic_version SET version_num = 'tampered'",
            "DELETE FROM alembic_version",
            "INSERT INTO alembic_version (version_num) VALUES ('tampered')",
            "TRUNCATE alembic_version",
            "DROP TABLE alembic_version",
        ):
            with pytest.raises(ProgrammingError) as excinfo:
                _as_role(database_settings, app_role, sql)
            assert "permission denied" in str(excinfo.value.orig) or "must be owner" in str(
                excinfo.value.orig
            )

        # The owner can still run migrations: an upgrade and a new table.
        with _connection(owner_settings) as connection:
            command.upgrade(_config(connection), "head")
            head = ScriptDirectory.from_config(_config()).get_current_head()
            current = connection.execute(text("SELECT version_num FROM alembic_version"))
            assert current.scalar_one() == head
            connection.execute(text("CREATE TABLE app_records (id int PRIMARY KEY, note text)"))


def test_runtime_role_keeps_data_access_to_application_tables(
    database_settings: Settings,
) -> None:
    with _deployment_roles(database_settings) as (owner, app_role):
        owner_settings = database_settings.model_copy(update={"database_user": owner})
        with _connection(owner_settings) as connection:
            command.upgrade(_config(connection), "head")
            # Stands in for a table created by a future migration.
            connection.execute(text("CREATE TABLE app_records (id int PRIMARY KEY, note text)"))

        for sql in (
            "INSERT INTO app_records (id, note) VALUES (1, 'a')",
            "UPDATE app_records SET note = 'b' WHERE id = 1",
            "SELECT note FROM app_records",
            "DELETE FROM app_records WHERE id = 1",
        ):
            _as_role(database_settings, app_role, sql)

        for sql in ("ALTER TABLE app_records ADD COLUMN extra int", "DROP TABLE app_records"):
            with pytest.raises(ProgrammingError):
                _as_role(database_settings, app_role, sql)


def test_restriction_is_idempotent_and_leaves_owner_access(database_settings: Settings) -> None:
    with _connection(database_settings) as connection:
        command.upgrade(_config(connection), "head")
        command.upgrade(_config(connection), "head")
        acl = connection.execute(
            text("SELECT relacl::text FROM pg_class WHERE oid = 'alembic_version'::regclass")
        ).scalar_one_or_none()
    # Only the owner's own privileges remain (or none were ever granted).
    assert acl is None or all(
        entry.startswith(f"{database_settings.database_user}=")
        for entry in acl.strip("{}").split(",")
    )


def test_offline_sql_includes_the_restriction(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "test")
    monkeypatch.setenv("AEGIS_DATABASE_HOST", "unreachable.invalid")
    command.upgrade(_config(), "head", sql=True)
    assert "REVOKE ALL ON TABLE %s FROM PUBLIC" in capsys.readouterr().out
