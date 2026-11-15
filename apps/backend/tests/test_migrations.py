"""Alembic configuration and migration tests against a disposable PostgreSQL."""

import re
import shutil
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
        assert "def upgrade()" in source and "def downgrade()" in source


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

    class DemoBase(Base):
        __abstract__ = True
        metadata = MetaData(naming_convention=NAMING_CONVENTION)

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
    assert revision is not None and not isinstance(revision, list)
    generated = Path(revision.path).read_text(encoding="utf-8")
    assert "op.create_table('demo_items'" in generated or 'op.create_table("demo_items"' in generated
    assert "pk_demo_items" in generated and "uq_demo_items_name" in generated

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
