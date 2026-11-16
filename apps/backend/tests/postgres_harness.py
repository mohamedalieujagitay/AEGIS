"""Disposable PostgreSQL server for tests.

Tests never use a developer's or production database. Instead, a temporary
cluster is created with the local PostgreSQL binaries (``initdb``,
``pg_ctl``) in a temporary directory, listening only on 127.0.0.1 on a free
port with trust authentication, and destroyed after the test session.

Binaries are looked up in ``AEGIS_TEST_POSTGRES_BIN``, then on ``PATH``,
then in the standard Windows installation directory. If none are found,
database tests are skipped.
"""

import os
import shutil
import socket
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

TEST_DATABASE_USER = "aegis_test"


@dataclass(frozen=True)
class PostgresServer:
    host: str
    port: int
    user: str


def find_postgres_bin() -> Path | None:
    configured = os.environ.get("AEGIS_TEST_POSTGRES_BIN")
    if configured:
        return Path(configured)
    initdb = shutil.which("initdb")
    if initdb:
        return Path(initdb).parent
    if sys.platform == "win32":
        root = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "PostgreSQL"
        candidates = [
            path
            for path in root.glob("*/bin")
            if (path / "initdb.exe").exists() and path.parent.name.isdigit()
        ]
        if candidates:
            return max(candidates, key=lambda path: int(path.parent.name))
    return None


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
        return port


def _run(arguments: list[str], log_file: Path | None = None) -> None:
    """Run a PostgreSQL tool with a fixed argument list (never a shell).

    With ``log_file``, output is not captured: the server started by
    ``pg_ctl start`` would inherit the pipes and keep them open, so waiting
    for them would never finish. Its own log is reported on failure instead.
    """
    if log_file is None:
        # Fixed argument lists built by this module, never a shell (S603).
        captured = subprocess.run(  # noqa: S603
            arguments, capture_output=True, text=True, check=False
        )
        returncode, detail = captured.returncode, captured.stderr.strip()
    else:
        returncode = subprocess.run(  # noqa: S603
            arguments,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        detail = (
            log_file.read_text(encoding="utf-8", errors="replace")[-2000:]
            if log_file.exists()
            else ""
        )
    if returncode != 0:
        raise RuntimeError(f"{Path(arguments[0]).name} failed ({returncode}): {detail}")


@contextmanager
def temporary_postgres(bin_dir: Path, data_root: Path) -> Iterator[PostgresServer]:
    data_dir = data_root / "data"
    log_file = data_root / "postgres.log"
    port = _free_port()
    suffix = ".exe" if sys.platform == "win32" else ""
    initdb = str(bin_dir / f"initdb{suffix}")
    pg_ctl = str(bin_dir / f"pg_ctl{suffix}")

    _run(
        [
            initdb,
            "-D",
            str(data_dir),
            "-U",
            TEST_DATABASE_USER,
            "-A",
            "trust",
            "-E",
            "UTF8",
            "--no-locale",
            "--no-instructions",
        ]
    )
    # The local socket goes in the temporary directory (-k), so no shared
    # system directory is used and no shell quoting is needed on any platform.
    options = (
        f"-p {port} -c listen_addresses=127.0.0.1 -k {data_root} "
        "-c fsync=off -c synchronous_commit=off -c full_page_writes=off"
    )
    _run(
        [pg_ctl, "-D", str(data_dir), "-l", str(log_file), "-o", options, "-w", "start"],
        log_file=log_file,
    )
    try:
        yield PostgresServer(host="127.0.0.1", port=port, user=TEST_DATABASE_USER)
    finally:
        _run([pg_ctl, "-D", str(data_dir), "-m", "immediate", "-w", "stop"])
