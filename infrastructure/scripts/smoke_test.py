"""Container smoke test for the AEGIS stack (DECISIONS.md D-058).

    python infrastructure/scripts/smoke_test.py [--build] [--keep]

Starts the production-like stack (docker-compose.yml only, no development
override) as a separate Compose project, "aegis-smoke", with its own
temporary secrets, subnets, host port and volumes, and checks it from the
outside and from inside the containers:

- every service becomes healthy; migrations run explicitly and reach head;
- the frontend serves the app and proxies the API; health endpoints work;
- the API sends no Server header; forwarding headers are trusted only from
  the frontend;
- PostgreSQL roles: the runtime role cannot change the schema;
- worker isolation: the assessment worker cannot resolve or reach
  PostgreSQL, has no database credentials, and its Valkey user cannot touch
  the internal namespace or run administrative commands;
- tasks are routed through Valkey to the right worker role;
- authentication: CLI account creation, sign-in with secure cookies, CSRF
  protection, sessions, sign-out, administrator password reset, rate
  limiting in Valkey, and no secrets in the logs;
- containers run as non-root with read-only root filesystems, no
  capabilities, no-new-privileges, resource limits and no Docker socket;
- only the frontend port is published, on 127.0.0.1;
- secret values do not appear in the images;
- every service shuts down gracefully.

It never touches the developer's "aegis" project. At the end it removes only
the "aegis-smoke" containers, networks and volumes, and the temporary secrets
(unless --keep is given). Uses only the Python standard library and the
Docker CLI; no shell is used.
"""

import argparse
import http.client
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "aegis-smoke"
SUBNET_PREFIX = "10.214"
HTTP_PORT = 18080
BASE_URL = f"http://127.0.0.1:{HTTP_PORT}"
SERVICES = ("postgres", "valkey", "backend", "worker-internal", "worker-assessment", "frontend")
EXPECTED_NETWORKS = {
    "postgres": {"data"},
    "valkey": {"queue"},
    "backend": {"edge", "data", "queue", "ingest"},
    "worker-internal": {"data", "queue"},
    "worker-assessment": {"queue", "ingest", "egress"},
    "frontend": {"edge"},
}
INTERNAL_NETWORKS = {"data", "queue", "ingest"}

if PROJECT == "aegis":  # pragma: no cover - guard against editing mistakes
    raise SystemExit("refusing to run against the developer project")


# --- Helpers ------------------------------------------------------------------


@dataclass
class Results:
    passed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)

    def check(self, name: str, condition: bool, detail: str = "") -> bool:
        if condition:
            self.passed.append(name)
            print(f"PASS  {name}")
        else:
            self.failed.append(f"{name}: {detail}" if detail else name)
            print(f"FAIL  {name}{': ' + detail if detail else ''}")
        return condition


def run(
    args: Sequence[str],
    env: dict[str, str] | None = None,
    check: bool = True,
    timeout: float = 600,
    stdin: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command with a fixed argument list (never through a shell).

    ``stdin`` is written to the command's standard input; secrets are passed
    this way so they never appear in a command line.
    """
    # Arguments are built by this script (docker CLI calls), never from input.
    result = subprocess.run(  # noqa: S603
        list(args),
        env=env,
        input=stdin,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(args)}\n"
            f"{result.stdout[-3000:]}\n{result.stderr[-3000:]}"
        )
    return result


class Stack:
    def __init__(self, secrets_dir: Path) -> None:
        self.secrets_dir = secrets_dir
        # The administrator created by check_authentication, for the browser tests.
        self.admin_email = ""
        self.admin_password = ""
        self.env = os.environ | {
            "AEGIS_SECRETS_DIR": str(secrets_dir),
            "AEGIS_SUBNET_PREFIX": SUBNET_PREFIX,
            "AEGIS_HTTP_PORT": str(HTTP_PORT),
        }

    def compose(
        self, *args: str, check: bool = True, timeout: float = 600
    ) -> subprocess.CompletedProcess[str]:
        command = [
            "docker",
            "compose",
            "--project-name",
            PROJECT,
            "--file",
            str(ROOT / "docker-compose.yml"),
            *args,
        ]
        return run(command, env=self.env, check=check, timeout=timeout)

    def exec(
        self,
        service: str,
        *command: str,
        extra_env: dict[str, str] | None = None,
        stdin: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env_args: list[str] = []
        for key, value in (extra_env or {}).items():
            env_args += ["--env", f"{key}={value}"]
        compose = [
            "docker",
            "compose",
            "--project-name",
            PROJECT,
            "--file",
            str(ROOT / "docker-compose.yml"),
            "exec",
            "-T",
            *env_args,
            service,
            *command,
        ]
        return run(compose, env=self.env, check=False, timeout=120, stdin=stdin)

    def python(self, service: str, code: str) -> subprocess.CompletedProcess[str]:
        return self.exec(service, "python", "-c", code)

    def container(self, service: str) -> dict[str, Any]:
        container_id = self.compose("ps", "--all", "--quiet", service).stdout.strip()
        inspected: list[dict[str, Any]] = json.loads(
            run(["docker", "inspect", container_id]).stdout
        )
        return inspected[0]

    def secret(self, name: str) -> str:
        return (self.secrets_dir / name).read_text(encoding="utf-8").strip()


def http_get(path: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], str]:
    # BASE_URL is a fixed http://127.0.0.1 address; paths are constants in this script.
    request = urllib.request.Request(BASE_URL + path, headers=headers or {})  # noqa: S310
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 (fixed local URL)
            return (
                response.status,
                {k.lower(): v for k, v in response.headers.items()},
                response.read().decode(),
            )
    except urllib.error.HTTPError as error:
        return error.code, {k.lower(): v for k, v in error.headers.items()}, error.read().decode()


def wait_for(condition: Callable[[], bool], timeout: float, interval: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(interval)
    return condition()


# --- Checks -------------------------------------------------------------------


def check_health(stack: Stack, results: Results) -> None:
    rows = [
        json.loads(line)
        for line in stack.compose("ps", "--format", "json").stdout.splitlines()
        if line
    ]
    states = {row["Service"]: (row["State"], row.get("Health", "")) for row in rows}
    for service in SERVICES:
        state = states.get(service)
        results.check(
            f"{service} is running and healthy", state == ("running", "healthy"), str(state)
        )


def check_http(stack: Stack, results: Results) -> None:
    status, headers, body = http_get("/")
    results.check(
        "frontend serves the application", status == 200 and '<div id="root">' in body, str(status)
    )
    results.check(
        "frontend sends a strict CSP",
        "default-src 'self'" in headers.get("content-security-policy", ""),
    )
    results.check(
        "frontend sends security headers",
        headers.get("x-frame-options") == "DENY"
        and headers.get("x-content-type-options") == "nosniff",
    )
    results.check(
        "nginx version is not disclosed",
        headers.get("server") == "nginx",
        headers.get("server", ""),
    )
    status, _, body = http_get("/findings")
    results.check(
        "client-side routes fall back to index.html",
        status == 200 and '<div id="root">' in body,
        str(status),
    )

    status, headers, body = http_get("/api/v1/health/live")
    results.check(
        "liveness through the frontend proxy",
        status == 200 and json.loads(body) == {"status": "ok"},
        f"{status} {body}",
    )
    results.check("API responses are not cached", headers.get("cache-control") == "no-store")
    status, _, body = http_get("/api/v1/health/ready")
    expected = {"status": "ready", "checks": {"database": "ok", "broker": "ok"}}
    results.check(
        "readiness through the frontend proxy",
        status == 200 and json.loads(body) == expected,
        f"{status} {body}",
    )
    for path in ("/api/docs", "/api/openapi.json"):
        status, _, _ = http_get(path)
        results.check(f"{path} is disabled in production", status == 404, str(status))

    probe = (
        "import urllib.request as u\n"
        "r = u.urlopen('http://127.0.0.1:8000/api/v1/health/live', timeout=5)\n"
        "print(r.headers.get('server'))"
    )
    output = stack.python("backend", probe).stdout.strip()
    results.check("the API sends no Server header (--no-server-header)", output == "None", output)

    command = stack.container("backend")["Config"]["Cmd"]
    frontend_ip = stack.container("frontend")["NetworkSettings"]["Networks"][f"{PROJECT}_edge"][
        "IPAddress"
    ]
    trusted = [arg.split("=", 1)[1] for arg in command if arg.startswith("--forwarded-allow-ips=")]
    results.check(
        "forwarding headers are trusted only from the frontend",
        trusted == [frontend_ip] == [f"{SUBNET_PREFIX}.0.10"],
        f"{trusted} vs {frontend_ip}",
    )


def check_database(stack: Stack, results: Results) -> None:
    head = stack.exec("backend", "alembic", "heads").stdout.split()[0]
    current = stack.exec(
        "postgres",
        "psql",
        "--username=postgres",
        "--dbname=aegis",
        "--tuples-only",
        "--no-align",
        "--command=SELECT version_num FROM alembic_version",
    ).stdout.strip()
    results.check(
        "migrations are at head", bool(head) and current == head, f"head={head} current={current}"
    )

    def as_role(role: str, password: str, sql: str) -> subprocess.CompletedProcess[str]:
        return stack.exec(
            "postgres",
            "psql",
            "--host=127.0.0.1",
            f"--username={role}",
            "--dbname=aegis",
            "--no-psqlrc",
            "--set=ON_ERROR_STOP=1",
            f"--command={sql}",
            extra_env={"PGPASSWORD": password},
        )

    app_password = stack.secret("postgres_app_password")
    owner_password = stack.secret("postgres_owner_password")
    for sql in (
        # Migration metadata belongs to the owner only (D-060).
        "SELECT version_num FROM alembic_version",
        "UPDATE alembic_version SET version_num = 'tampered'",
        "DELETE FROM alembic_version",
        "INSERT INTO alembic_version (version_num) VALUES ('tampered')",
        # No schema changes.
        "CREATE TABLE smoke_check (id int)",
        "DROP TABLE alembic_version",
        "ALTER TABLE alembic_version ADD COLUMN smoke int",
        "TRUNCATE alembic_version",
        "CREATE SCHEMA smoke",
    ):
        denied = as_role("aegis_app", app_password, sql)
        message = denied.stderr.lower()
        refused = denied.returncode != 0 and (
            "permission denied" in message or "must be owner" in message
        )
        results.check(f"runtime role is denied: {sql}", refused, denied.stderr.strip()[:120])
    owner = as_role(
        "aegis_owner", owner_password, "BEGIN; CREATE TABLE smoke_owner_check (id int); ROLLBACK;"
    )
    results.check(
        "migration owner can change the schema", owner.returncode == 0, owner.stderr.strip()[:120]
    )
    owner_metadata = as_role(
        "aegis_owner",
        owner_password,
        "BEGIN; UPDATE alembic_version SET version_num = version_num; ROLLBACK;",
    )
    results.check(
        "migration owner can change migration metadata",
        owner_metadata.returncode == 0,
        owner_metadata.stderr.strip()[:120],
    )

    # A table created by the owner (as future migrations will) stays usable
    # by the runtime role for data, but not for schema changes.
    created = as_role(
        "aegis_owner", owner_password, "CREATE TABLE smoke_app_records (id int PRIMARY KEY)"
    )
    results.check("owner can create an application table", created.returncode == 0)
    data_access = all(
        as_role("aegis_app", app_password, sql).returncode == 0
        for sql in (
            "INSERT INTO smoke_app_records (id) VALUES (1)",
            "UPDATE smoke_app_records SET id = 2 WHERE id = 1",
            "SELECT id FROM smoke_app_records",
            "DELETE FROM smoke_app_records",
        )
    )
    results.check("runtime role can read and change application data", data_access)
    alter = as_role("aegis_app", app_password, "ALTER TABLE smoke_app_records ADD COLUMN x int")
    results.check("runtime role cannot alter application tables", alter.returncode != 0)
    as_role("aegis_owner", owner_password, "DROP TABLE smoke_app_records")
    flags = stack.exec(
        "postgres",
        "psql",
        "--username=postgres",
        "--dbname=aegis",
        "--tuples-only",
        "--no-align",
        "--command=SELECT string_agg(rolname || ':' || rolsuper || rolcreatedb || rolcreaterole,"
        " ',' ORDER BY rolname) FROM pg_roles WHERE rolname LIKE 'aegis_%'",
    ).stdout.strip()
    results.check(
        "AEGIS roles are not privileged",
        flags == "aegis_app:falsefalsefalse,aegis_owner:falsefalsefalse",
        flags,
    )
    superuser = stack.exec(
        "postgres",
        "psql",
        "--host=127.0.0.1",
        "--username=postgres",
        "--dbname=aegis",
        "--command=SELECT 1",
        extra_env={"PGPASSWORD": stack.secret("postgres_superuser_password")},
    )
    results.check(
        "superuser cannot connect over the network",
        superuser.returncode != 0 and "pg_hba.conf rejects" in superuser.stderr,
        superuser.stderr.strip()[:120],
    )


ISOLATION_PROBE = """
import json, os, socket, redis
result = {}
try:
    socket.getaddrinfo("postgres", 5432)
    result["resolves_postgres"] = True
except socket.gaierror:
    result["resolves_postgres"] = False
try:
    socket.create_connection((POSTGRES_IP, 5432), timeout=3).close()
    result["reaches_postgres"] = True
except OSError:
    result["reaches_postgres"] = False
result["database_env"] = sorted(k for k in os.environ if k.startswith("AEGIS_DATABASE"))
result["secrets"] = sorted(os.listdir("/run/secrets"))
password = open("/run/secrets/aegis_valkey_password").read().strip()
client = redis.Redis(
    host="valkey",
    username=os.environ["AEGIS_VALKEY_USERNAME"],
    password=password,
    socket_timeout=5,
)
denied = {}
for command in COMMANDS:
    try:
        client.execute_command(*command)
        denied[" ".join(command)] = False
    except redis.exceptions.NoPermissionError:
        denied[" ".join(command)] = True
    except redis.exceptions.ResponseError as error:
        # DEBUG and MODULE are also disabled server-wide (valkey.conf), which
        # refuses them before the ACL is checked.
        denied[" ".join(command)] = "not allowed" in str(error)
result["denied"] = denied
try:
    redis.Redis(host="valkey", socket_timeout=5).ping()
    result["default_user"] = "accepted"
except redis.exceptions.AuthenticationError:
    result["default_user"] = "rejected"
print(json.dumps(result))
"""

FORBIDDEN_FOR_ALL = [
    ["KEYS", "*"],
    ["FLUSHALL"],
    ["FLUSHDB"],
    ["CONFIG", "GET", "*"],
    ["DEBUG", "SLEEP", "0"],
    ["MODULE", "LIST"],
    ["ACL", "LIST"],
    ["PUBLISH", "celery.pidbox", "x"],
    ["SHUTDOWN", "NOSAVE"],
]


def _isolation(
    stack: Stack, service: str, postgres_ip: str, commands: list[list[str]]
) -> dict[str, Any]:
    code = ISOLATION_PROBE.replace("POSTGRES_IP", repr(postgres_ip)).replace(
        "COMMANDS", repr(commands)
    )
    output = stack.python(service, code)
    if output.returncode != 0:
        raise RuntimeError(f"isolation probe failed in {service}: {output.stderr[-2000:]}")
    result: dict[str, Any] = json.loads(output.stdout.strip().splitlines()[-1])
    return result


def check_isolation(stack: Stack, results: Results) -> None:
    postgres_ip = stack.container("postgres")["NetworkSettings"]["Networks"][f"{PROJECT}_data"][
        "IPAddress"
    ]

    other_namespace = [
        ["LLEN", "internal.default"],
        ["HGETALL", "internal.unacked"],
        ["SMEMBERS", "_kombu.binding.internal"],
        ["LPUSH", "internal.default", "x"],
    ]
    assessment = _isolation(
        stack,
        "worker-assessment",
        postgres_ip,
        other_namespace + FORBIDDEN_FOR_ALL + [["LLEN", "assessment.default"]],
    )
    results.check(
        "assessment worker cannot resolve postgres", assessment["resolves_postgres"] is False
    )
    results.check(
        "assessment worker cannot reach postgres by address",
        assessment["reaches_postgres"] is False,
    )
    results.check(
        "assessment worker has no database settings",
        assessment["database_env"] == [],
        str(assessment["database_env"]),
    )
    results.check(
        "assessment worker receives only its Valkey secret",
        assessment["secrets"] == ["aegis_valkey_password"],
        str(assessment["secrets"]),
    )
    for command, denied in assessment["denied"].items():
        if command == "LLEN assessment.default":
            results.check("assessment worker can use its own queue", denied is False)
        else:
            results.check(f"assessment worker's Valkey user is denied: {command}", denied is True)
    results.check(
        "Valkey rejects unauthenticated clients", assessment["default_user"] == "rejected"
    )

    other_namespace = [
        ["LLEN", "assessment.default"],
        ["HGETALL", "assessment.unacked"],
        ["LPUSH", "assessment.default", "x"],
    ]
    internal = _isolation(
        stack, "worker-internal", postgres_ip, other_namespace + FORBIDDEN_FOR_ALL
    )
    results.check(
        "internal worker can reach postgres",
        internal["resolves_postgres"] and internal["reaches_postgres"],
    )
    results.check(
        "internal worker receives only its own secrets",
        internal["secrets"] == ["aegis_database_password", "aegis_valkey_password"],
        str(internal["secrets"]),
    )
    results.check(
        "internal worker's Valkey user is denied the assessment namespace and admin commands",
        all(internal["denied"].values()),
        str(internal["denied"]),
    )

    api = _isolation(
        stack,
        "backend",
        postgres_ip,
        [
            *FORBIDDEN_FOR_ALL,
            ["BRPOP", "internal.default", "1"],
            # Rate-limit commands only on rate-limit keys (D-066).
            ["SET", "internal.default", "x"],
            ["DEL", "_kombu.binding.internal"],
            ["INCRBY", "other:smoke", "1"],
            ["GET", "ratelimit:smoke"],
            ["KEYS", "ratelimit:*"],
        ],
    )
    results.check(
        "API's Valkey user can only send tasks and use rate-limit counters",
        all(api["denied"].values()),
        str(api["denied"]),
    )
    allowed = _isolation(
        stack,
        "backend",
        postgres_ip,
        [
            ["INCRBY", "ratelimit:smoke", "1"],
            ["EXPIRE", "ratelimit:smoke", "60", "NX"],
            ["MGET", "ratelimit:smoke"],
            ["PTTL", "ratelimit:smoke"],
            ["SET", "ratelimit:smoke-block", "1", "PX", "1000"],
            ["DEL", "ratelimit:smoke", "ratelimit:smoke-block"],
        ],
    )
    results.check(
        "API's Valkey user can use rate-limit counters",
        not any(allowed["denied"].values()),
        str(allowed["denied"]),
    )

    for service, expected in EXPECTED_NETWORKS.items():
        networks = {
            name.removeprefix(f"{PROJECT}_")
            for name in stack.container(service)["NetworkSettings"]["Networks"]
        }
        results.check(
            f"{service} is attached only to {sorted(expected)}",
            networks == expected,
            str(sorted(networks)),
        )
    for network in ("edge", "data", "queue", "ingest", "egress"):
        details = json.loads(run(["docker", "network", "inspect", f"{PROJECT}_{network}"]).stdout)[
            0
        ]
        results.check(
            f"network {network} internal={network in INTERNAL_NETWORKS}",
            details["Internal"] is (network in INTERNAL_NETWORKS),
        )


def check_task_routing(stack: Stack, results: Results) -> None:
    sender = (
        "from celery.exceptions import QueueNotFound\n"
        "from app.core.config import get_settings\n"
        "from app.workers.celery_app import WorkerRole, create_celery_app\n"
        "app = create_celery_app(WorkerRole.API, get_settings())\n"
        "app.send_task('aegis.internal.smoke_test')\n"
        "app.send_task('aegis.assessment.smoke_test')\n"
        "try:\n"
        "    app.send_task('unrouted.smoke_test')\n"
        "    print('unrouted-sent')\n"
        "except QueueNotFound:\n"
        "    print('unrouted-refused')\n"
    )
    output = stack.python("backend", sender)
    results.check(
        "API sends tasks through Valkey as its own ACL user",
        output.returncode == 0,
        output.stderr[-300:],
    )
    results.check(
        "tasks without a route are refused",
        output.stdout.strip().endswith("unrouted-refused"),
        output.stdout,
    )

    def logs(service: str) -> str:
        return stack.compose("logs", "--no-color", service).stdout

    received = wait_for(
        lambda: (
            "aegis.internal.smoke_test" in logs("worker-internal")
            and "aegis.assessment.smoke_test" in logs("worker-assessment")
        ),
        timeout=30,
    )
    results.check("each worker receives the task for its own queue", received)
    results.check(
        "internal worker never receives assessment tasks",
        "aegis.assessment.smoke_test" not in logs("worker-internal"),
    )
    results.check(
        "assessment worker never receives internal tasks",
        "aegis.internal.smoke_test" not in logs("worker-assessment"),
    )
    all_logs = stack.compose("logs", "--no-color").stdout
    results.check(
        "no Valkey permission errors in any log",
        "NOPERM" not in all_logs and "NoPermissionError" not in all_logs,
    )


@dataclass
class Browser:
    """A minimal browser for the authentication checks.

    It keeps cookies itself, because urllib does not send ``Secure`` cookies
    over plain HTTP (browsers do for 127.0.0.1, see the Chromium check). It
    records each Set-Cookie header so the cookie attributes can be checked.
    """

    cookies: dict[str, str] = field(default_factory=dict)
    set_cookie_headers: list[str] = field(default_factory=list)

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], Any]:
        connection = http.client.HTTPConnection("127.0.0.1", HTTP_PORT, timeout=15)
        all_headers = {"Accept": "application/json", **(headers or {})}
        if self.cookies:
            all_headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        payload = None
        if body is not None:
            payload = json.dumps(body)
            all_headers["Content-Type"] = "application/json"
        try:
            connection.request(method, path, body=payload, headers=all_headers)
            response = connection.getresponse()
            raw = response.read().decode()
            for header in response.headers.get_all("Set-Cookie") or []:
                self.set_cookie_headers.append(header)
                name, _, rest = header.partition("=")
                value = rest.split(";", 1)[0].strip().strip('"')
                if value and "max-age=0" not in header.lower():
                    self.cookies[name] = value
                else:
                    self.cookies.pop(name, None)
            data = json.loads(raw) if raw else None
            return response.status, {k.lower(): v for k, v in response.getheaders()}, data
        finally:
            connection.close()

    def post(
        self, path: str, body: dict[str, Any] | None = None, token: str = "", **extra: str
    ) -> tuple[int, dict[str, str], Any]:
        headers = {"Origin": BASE_URL, **extra}
        if token:
            headers["X-CSRF-Token"] = token
        return self.request("POST", path, body, headers)

    def csrf(self) -> str:
        status, _, data = self.request("GET", "/api/v1/auth/csrf")
        if status != 200:
            raise RuntimeError(f"GET /api/v1/auth/csrf returned {status}")
        token: str = data["csrf_token"]
        return token

    def login(self, email: str, password: str) -> tuple[int, Any]:
        status, _, data = self.post(
            "/api/v1/auth/login", {"email": email, "password": password}, self.csrf()
        )
        return status, data


def _cookie_attributes(header: str) -> set[str]:
    return {part.strip().split("=", 1)[0].lower() for part in header.split(";")[1:]}


def _cli(stack: Stack, *args: str, password: str) -> subprocess.CompletedProcess[str]:
    """Run the administration CLI in the API container; the password goes to stdin."""
    return stack.exec(
        "backend", "python", "-m", "app.cli", *args, "--password-stdin", stdin=password + "\n"
    )


def check_authentication(stack: Stack, results: Results) -> None:
    """Authentication on the real stack (roadmap 2.1, DECISIONS.md D-061 to D-068)."""
    # Random passphrases that pass the policy (no username or email local part).
    admin_password = "correct horse battery " + os.urandom(6).hex()
    stack.admin_email = "admin@smoke.test"
    stack.admin_password = admin_password
    user_password = "purple monkey dishwasher " + os.urandom(6).hex()
    new_password = "tangerine lighthouse orbit " + os.urandom(6).hex()
    api = "/api/v1/auth"

    created = _cli(
        stack,
        "create-admin",
        "--email",
        "admin@smoke.test",
        "--username",
        "smokeadmin",
        password=admin_password,
    )
    results.check(
        "CLI creates the first administrator (password from standard input)",
        created.returncode == 0 and "Created instance administrator" in created.stdout,
        created.stderr[-300:],
    )
    results.check(
        "CLI output contains no password", admin_password not in created.stdout + created.stderr
    )
    created = _cli(
        stack,
        "create-user",
        "--email",
        "user@smoke.test",
        "--username",
        "smokeuser",
        password=user_password,
    )
    results.check("CLI creates a user", created.returncode == 0, created.stderr[-300:])

    anonymous = Browser()
    status, _, _ = anonymous.request("GET", f"{api}/me")
    results.check("unauthenticated requests are refused", status == 401, str(status))
    status, _, data = anonymous.post(
        f"{api}/login", {"email": "user@smoke.test", "password": user_password}
    )
    results.check(
        "sign-in without a CSRF token is refused (login CSRF)",
        status == 403 and data["error"]["code"] == "csrf_failed",
        str(status),
    )
    status, _, _ = anonymous.post(
        f"{api}/login",
        {"email": "user@smoke.test", "password": user_password},
        anonymous.csrf(),
        Origin="https://evil.example",
    )
    results.check("a cross-origin sign-in is refused", status == 403, str(status))
    anonymous_token = anonymous.csrf()

    user = Browser()
    status, data = user.login("user@smoke.test", user_password)
    results.check("sign-in succeeds through the frontend proxy", status == 200, str(status))
    expected = {"httponly", "secure", "samesite", "path"}
    for name in ("__Host-aegis_session", "__Host-aegis_csrf"):
        cookies = [h for h in user.set_cookie_headers if h.startswith(name + "=")]
        last = cookies[-1] if cookies else ""
        results.check(
            f"{name} is HttpOnly, Secure, SameSite=Strict, Path=/, without Domain or expiry",
            _cookie_attributes(last) == expected
            and "samesite=strict" in last.lower()
            and "path=/" in last.lower(),
            json.dumps(sorted(_cookie_attributes(last))),  # attribute names only, never the value
        )
    session_token = user.cookies.get("__Host-aegis_session", "")
    results.check(
        "the session token is not in the response body",
        bool(session_token) and session_token not in json.dumps(data),
    )
    user_csrf = data["csrf_token"] if status == 200 else ""
    status, _, me = user.request("GET", f"{api}/me")
    results.check(
        "the session identifies the user",
        status == 200 and me["username"] == "smokeuser",
        str(status),
    )
    # Trusted browsers (D-070): listed without their token, and revocable one by one.
    status, _, devices = user.request("GET", f"{api}/devices")
    results.check(
        "the signed-in browser is listed as trusted, without its token",
        status == 200
        and isinstance(devices, list)
        and len(devices) == 1
        and devices[0]["current"] is True
        and session_token not in json.dumps(devices)
        and user.cookies.get("__Host-aegis_device", "") not in json.dumps(devices),
        str(status),
    )
    device_id = (
        devices[0]["id"] if status == 200 and devices else "00000000-0000-4000-8000-000000000000"
    )
    status, _, _ = user.request(
        "DELETE",
        f"{api}/devices/{device_id}",
        headers={"Origin": BASE_URL, "X-CSRF-Token": "not-the-token"},
    )
    results.check(
        "revoking a device without a valid CSRF token is refused", status == 403, str(status)
    )
    status, _, _ = user.request(
        "DELETE",
        f"{api}/devices/{device_id}",
        headers={"Origin": BASE_URL, "X-CSRF-Token": user_csrf},
    )
    results.check(
        "the signed-in user can revoke their own trusted browser", status == 204, str(status)
    )
    status, _, after = user.request("GET", f"{api}/devices")
    results.check(
        "a revoked trusted browser is no longer listed",
        status == 200 and after == [],
        str(after),
    )
    user.cookies["__Host-aegis_csrf"] = anonymous_token
    status, _, _ = user.post(f"{api}/logout", token=anonymous_token)
    results.check("an anonymous CSRF token is refused once signed in", status == 403, str(status))
    user.cookies["__Host-aegis_csrf"] = user_csrf

    admin = Browser()
    status, data = admin.login("admin@smoke.test", admin_password)
    admin_csrf = data["csrf_token"] if status == 200 else ""
    status, _, _ = user.post("/api/v1/admin/password-resets", {"email": "x@smoke.test"}, user_csrf)
    results.check("only instance administrators can issue reset links", status == 403, str(status))
    status, headers, issued = admin.post(
        "/api/v1/admin/password-resets", {"email": "user@smoke.test"}, admin_csrf
    )
    reset_token = issued["reset_token"] if status == 201 else ""
    results.check(
        "administrator issues a reset link (token in the URL fragment)",
        status == 201
        and issued["reset_path"] == f"/reset-password#token={reset_token}"
        and headers.get("cache-control") == "no-store",
        str(status),
    )
    forged = "v1.0.forged.signature"  # deliberately invalid CSRF token
    status, _, _ = user.post(f"{api}/logout", token=forged)
    results.check("an invalid CSRF token is refused", status == 403, str(status))

    visitor = Browser()
    status, _, _ = visitor.post(
        f"{api}/password/reset",
        {"token": reset_token, "new_password": new_password},
        visitor.csrf(),
    )
    results.check("the reset link sets a new password", status == 204, str(status))
    status, _, _ = user.request("GET", f"{api}/me")
    results.check("a password reset signs out every session", status == 401, str(status))
    status, _, _ = visitor.post(
        f"{api}/password/reset",
        {"token": reset_token, "new_password": "another passphrase 123"},
        visitor.csrf(),
    )
    results.check("reset links are single-use", status == 400, str(status))
    status, _ = Browser().login("user@smoke.test", user_password)
    results.check("the old password no longer works", status == 401, str(status))

    fresh = Browser()
    status, data = fresh.login("user@smoke.test", new_password)
    results.check("the new password works", status == 200, str(status))
    stolen = fresh.cookies.get("__Host-aegis_session", "")
    status, _, _ = fresh.post(f"{api}/logout", token=data["csrf_token"] if status == 200 else "")
    results.check("sign-out succeeds", status == 204, str(status))
    replay = Browser(cookies={"__Host-aegis_session": stolen})
    status, _, _ = replay.request("GET", f"{api}/me")
    results.check("a signed-out session cannot be replayed", status == 401, str(status))

    attacker = Browser()
    statuses = [attacker.login("admin@smoke.test", "wrong password guess")[0] for _ in range(6)]
    status, headers, data = attacker.post(
        f"{api}/login",
        {"email": "admin@smoke.test", "password": admin_password},
        attacker.csrf(),
    )
    results.check(
        "repeated failures are throttled in Valkey (429 with Retry-After)",
        statuses == [401] * 6 and status == 429 and headers.get("retry-after") == "30",
        f"{statuses} then {status} {headers.get('retry-after')}",
    )
    results.check(
        "throttled responses are generic",
        status == 429 and data["error"]["code"] == "too_many_requests",
    )

    logs = stack.compose("logs", "--no-color", "backend").stdout
    for event in (
        "auth.login_succeeded",
        "auth.login_failed",
        "auth.csrf_rejected",
        "auth.password_reset_issued",
        "auth.password_reset_completed",
        "auth.logout",
        "auth.rate_limited",
    ):
        results.check(f"security event logged: {event}", f'"event": "{event}"' in logs)
    leaked = [
        label
        for label, value in (
            ("admin password", admin_password),
            ("user password", user_password),
            ("new password", new_password),
            ("session token", session_token),
            ("reset token", reset_token),
            ("CSRF token", user_csrf),
            ("secret key", stack.secret("aegis_secret_key")),
        )
        if value and value in logs
    ]
    results.check("no passwords, tokens or secret key in the API logs", not leaked, str(leaked))
    results.check("no email addresses in the API logs", "smoke.test" not in logs)


def check_browser(stack: Stack, results: Results) -> None:
    """Run the Playwright authentication tests against this stack (roadmap 2.1, CLAUDE.md §10).

    They need Node.js, the frontend's dependencies (npm ci) and Playwright's
    Chromium (npx playwright install chromium). The tests create accounts in this
    disposable stack only. Output is scrubbed of the generated passwords.
    """
    npx = shutil.which("npx")
    if npx is None:
        results.check("Node.js (npx) is available for the browser tests", False)
        return
    # The throttling checks above leave a short block on the administrator's
    # address. Wait for the block to end before the browser run signs in as it.
    administrator_ready = wait_for(
        lambda: _signs_in(stack.admin_email, stack.admin_password), timeout=90, interval=2
    )
    if not administrator_ready:
        results.check("the administrator can sign in for the browser tests", False)
        return
    env = stack.env | {
        # The browser tests may run service steps in this disposable project only.
        "AEGIS_E2E_COMPOSE_PROJECT": PROJECT,
        "AEGIS_E2E_COMPOSE_FILE": str(ROOT / "docker-compose.yml"),
        "AEGIS_E2E_BASE_URL": BASE_URL,
        "AEGIS_E2E_ADMIN_EMAIL": stack.admin_email,
        "AEGIS_E2E_ADMIN_PASSWORD": stack.admin_password,
    }
    # Fixed arguments; the working directory is the frontend project.
    result = subprocess.run(  # noqa: S603
        [npx, "playwright", "test"],
        cwd=ROOT / "apps" / "frontend",
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    # Playwright's list reporter ends with counts such as "15 passed" and "2 skipped".
    # Failed-test titles and their first lines are kept as well.
    summary = "\n".join(
        line.strip()
        for line in (result.stdout + result.stderr).splitlines()
        if re.match(r"^\s*(\d+ (passed|failed|skipped|flaky|did not run)|\d+\) )", line)
        or line.strip().startswith(("✘", "Error"))
    )[-1500:]
    summary = summary.replace(stack.admin_password, "[REDACTED]")
    # Printed on every run, so the counts are visible even when the step passes.
    print(f"Playwright summary:\n{summary or '(no summary lines)'}")
    results.check(
        "browser tests pass (Playwright, chromium)",
        result.returncode == 0,
        summary or f"exit {result.returncode}",
    )


def _signs_in(email: str, password: str) -> bool:
    connection = http.client.HTTPConnection("127.0.0.1", HTTP_PORT, timeout=15)
    try:
        connection.request("GET", "/api/v1/auth/csrf", headers={"Accept": "application/json"})
        csrf_response = connection.getresponse()
        csrf_body = json.loads(csrf_response.read().decode())
        cookies = [c.split(";", 1)[0] for c in csrf_response.headers.get_all("Set-Cookie") or []]
        connection.close()
        connection = http.client.HTTPConnection("127.0.0.1", HTTP_PORT, timeout=15)
        connection.request(
            "POST",
            "/api/v1/auth/login",
            body=json.dumps({"email": email, "password": password}),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": BASE_URL,
                "X-CSRF-Token": csrf_body["csrf_token"],
                "Cookie": "; ".join(cookies),
            },
        )
        return connection.getresponse().status == 200
    finally:
        connection.close()


def check_valkey_healthcheck(stack: Stack, results: Results) -> None:
    """The healthcheck ACL user needs its password and may only run PING (D-060).

    Commands, including AUTH with the password, are sent on standard input,
    so the password never appears in a command line.
    """
    password = stack.secret("valkey_healthcheck_password")

    def cli(commands: str) -> list[str]:
        # valkey-cli prints a blank line after each error reply when it reads
        # commands from standard input; only the replies themselves are kept.
        output = stack.exec("valkey", "valkey-cli", stdin=commands)
        return [line for line in output.stdout.splitlines() if line.strip()]

    unauthenticated = cli("PING\n")
    results.check(
        "Valkey refuses an unauthenticated PING",
        bool(unauthenticated) and unauthenticated[0].startswith("NOAUTH"),
        str(unauthenticated),
    )
    wrong = cli("AUTH healthcheck not-the-password\nPING\n")
    results.check(
        "Valkey refuses the healthcheck user with a wrong password",
        len(wrong) == 2 and wrong[0].startswith("WRONGPASS") and wrong[1].startswith("NOAUTH"),
        str(wrong),
    )
    forbidden = [
        "LLEN internal.default",
        "LLEN assessment.default",
        "GET anything",
        "KEYS *",
        "CONFIG GET maxmemory",
        "FLUSHALL",
        "ACL LIST",
        "PUBLISH celery.pidbox x",
    ]
    lines = cli(f"AUTH healthcheck {password}\nPING\n")
    results.check(
        "healthcheck user authenticates and can PING", lines == ["OK", "PONG"], str(lines)
    )
    # One session per command, so every reply is attributed to its command.
    for command in forbidden:
        reply = cli(f"AUTH healthcheck {password}\n{command}\n")
        denied = reply[:1] == ["OK"] and len(reply) == 2 and reply[1].startswith("NOPERM")
        results.check(f"healthcheck user is denied: {command}", denied, str(reply))

    info = stack.container("valkey")
    inspected = json.dumps(info)
    results.check(
        "healthcheck password is not in the container environment, command or health log",
        password not in inspected,
    )
    health = (info["State"].get("Health") or {}).get("Log") or []
    results.check(
        "Docker's own Valkey health check passes",
        bool(health) and health[-1].get("ExitCode") == 0,
        str(health[-1:])[:200],
    )


def check_probe_logging(stack: Stack, results: Results) -> None:
    """Routine health probes are not access-logged; other requests are (D-060)."""
    for _ in range(3):
        http_get("/api/v1/health/live")
        http_get("/api/v1/health/ready")
    status, _, _ = http_get("/api/v1/smoke-not-found")
    results.check("a non-probe request is answered", status == 404, str(status))
    time.sleep(1)
    backend = stack.compose("logs", "--no-color", "backend").stdout
    frontend = stack.compose("logs", "--no-color", "frontend").stdout
    probe_lines = [line for line in backend.splitlines() if '"event": "http.request"' in line]
    results.check(
        "API does not log routine health probes at INFO",
        not any("/api/v1/health/" in line for line in probe_lines),
        str([line[-160:] for line in probe_lines if "/api/v1/health/" in line][:2]),
    )
    results.check(
        "API still logs other requests",
        any("/api/v1/smoke-not-found" in line for line in probe_lines),
    )
    results.check(
        "nginx does not access-log routine health probes",
        "GET /api/v1/health/" not in frontend,
    )
    results.check("nginx still access-logs other requests", "/api/v1/smoke-not-found" in frontend)


def check_container_security(stack: Stack, results: Results) -> None:
    for service in SERVICES:
        info = stack.container(service)
        host = info["HostConfig"]
        user = info["Config"]["User"]
        uid = stack.exec(service, "id", "-u").stdout.strip()
        results.check(
            f"{service} runs as non-root (uid {uid})",
            uid not in ("", "0") and user not in ("", "0", "root"),
            f"user={user!r} uid={uid!r}",
        )
        results.check(f"{service} has a read-only root filesystem", host["ReadonlyRootfs"] is True)
        write = stack.exec(service, "touch", "/aegis-write-check")
        results.check(f"{service} cannot write to its root filesystem", write.returncode != 0)
        results.check(
            f"{service} drops all capabilities",
            host["CapDrop"] == ["ALL"] and not host["CapAdd"],
            f"{host['CapDrop']} {host['CapAdd']}",
        )
        results.check(
            f"{service} sets no-new-privileges",
            "no-new-privileges:true" in (host["SecurityOpt"] or []),
        )
        results.check(f"{service} is not privileged", host["Privileged"] is False)
        results.check(
            f"{service} has memory and process limits",
            host["Memory"] > 0 and (host["PidsLimit"] or 0) > 0,
        )
        mounts = [mount.get("Source", "") for mount in info["Mounts"]]
        results.check(
            f"{service} has no Docker socket",
            not any("docker.sock" in source for source in mounts),
            str(mounts),
        )
        ports = {
            port: bindings
            for port, bindings in (info["NetworkSettings"]["Ports"] or {}).items()
            if bindings
        }
        if service == "frontend":
            published = [
                (b["HostIp"], b["HostPort"]) for bindings in ports.values() for b in bindings
            ]
            results.check(
                "frontend is published only on 127.0.0.1",
                published == [("127.0.0.1", str(HTTP_PORT))],
                str(published),
            )
        else:
            results.check(f"{service} publishes no host port", not ports, str(ports))


def check_images(stack: Stack, results: Results) -> None:
    values = [
        path.read_text(encoding="utf-8").strip()
        for path in stack.secrets_dir.iterdir()
        if path.is_file()
    ]
    for image in ("aegis/backend:local", "aegis/frontend:local"):
        text = (
            run(["docker", "history", "--no-trunc", image]).stdout
            + run(["docker", "image", "inspect", image]).stdout
        )
        leaked = [value[:4] + "..." for value in values if value and value in text]
        results.check(f"{image} contains no secret values in its metadata", not leaked, str(leaked))
    listing = run(
        [
            "docker",
            "run",
            "--rm",
            "--name",
            f"{PROJECT}-image-check",
            "--entrypoint",
            "python",
            "aegis/backend:local",
            "-c",
            "import pathlib; print([str(p) for p in pathlib.Path('/app').rglob('*')"
            " if p.name in ('.env', 'secrets') or p.suffix == '.acl'])",
        ]
    ).stdout.strip()
    results.check("backend image contains no .env, secrets or ACL files", listing == "[]", listing)


def check_shutdown(stack: Stack, results: Results) -> None:
    started = time.monotonic()
    stack.compose("stop", timeout=900)
    elapsed = time.monotonic() - started
    rows = [
        json.loads(line)
        for line in stack.compose("ps", "--all", "--format", "json").stdout.splitlines()
        if line
    ]
    codes = {row["Service"]: row.get("ExitCode") for row in rows if row["Service"] in SERVICES}
    logs = stack.compose("logs", "--no-color").stdout
    for service in SERVICES:
        code = codes.get(service)
        if service == "backend":
            # Uvicorn re-raises the SIGTERM it received after its graceful
            # shutdown (uvicorn/server.py), so the process ends with 143.
            graceful = code == 0 or (code == 143 and "Finished server process" in logs)
            results.check(
                "backend stopped gracefully (0, or 143 after a clean Uvicorn shutdown)",
                graceful,
                str(code),
            )
        else:
            results.check(f"{service} stopped gracefully (exit code 0)", code == 0, str(code))
    results.check("the stack stops within 60 seconds when idle", elapsed < 60, f"{elapsed:.1f}s")
    for service, marker in (
        ("backend", "Finished server process"),
        ("postgres", "database system is shut down"),
        ("valkey", "ready to exit, bye bye"),
        ("worker-internal", "Warm shutdown"),
        ("worker-assessment", "Warm shutdown"),
    ):
        service_logs = "\n".join(line for line in logs.splitlines() if line.startswith(service))
        results.check(
            f"{service} logged a clean shutdown", marker.lower() in service_logs.lower(), marker
        )


# --- Main ---------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="AEGIS container smoke test")
    parser.add_argument("--build", action="store_true", help="build the images first")
    parser.add_argument(
        "--keep", action="store_true", help="leave the aegis-smoke stack and secrets in place"
    )
    parser.add_argument(
        "--e2e",
        action="store_true",
        help="also run the Playwright browser tests (needs Node.js and Chromium; see CONTRIBUTING)",
    )
    args = parser.parse_args()

    secrets_dir = Path(tempfile.mkdtemp(prefix="aegis-smoke-secrets-"))
    stack = Stack(secrets_dir)
    results = Results()
    try:
        run(
            [
                sys.executable,
                str(ROOT / "infrastructure/scripts/init_dev_secrets.py"),
                "--secrets-dir",
                str(secrets_dir),
            ]
        )
        if args.build:
            print("Building images...")
            stack.compose("build", timeout=1800)
        print("Starting postgres and valkey...")
        stack.compose(
            "up", "--detach", "--wait", "--wait-timeout", "180", "postgres", "valkey", timeout=300
        )
        print("Running migrations explicitly (production flow)...")
        migrate = stack.compose(
            "--profile", "migrate", "run", "--rm", "migrate", check=False, timeout=300
        )
        results.check(
            "migration job (alembic upgrade head) succeeds",
            migrate.returncode == 0,
            migrate.stderr[-500:],
        )
        print("Starting all services...")
        stack.compose("up", "--detach", "--wait", "--wait-timeout", "300", timeout=600)

        steps = [
            check_health,
            check_http,
            check_database,
            check_isolation,
            check_task_routing,
            check_authentication,
        ]
        if args.e2e:
            steps.append(check_browser)
        steps += [
            check_valkey_healthcheck,
            check_probe_logging,
            check_container_security,
            check_images,
            check_shutdown,
        ]
        for step in steps:
            print(f"--- {step.__name__.removeprefix('check_').replace('_', ' ')}")
            try:
                step(stack, results)
            except Exception as error:  # report and continue with the next group
                results.check(
                    f"{step.__name__} completed", False, f"{type(error).__name__}: {error}"
                )
    except Exception as error:
        results.check("stack started", False, f"{type(error).__name__}: {error}")
        print(stack.compose("logs", "--no-color", "--tail", "40", check=False).stdout[-6000:])
    finally:
        if args.keep:
            print(f"Kept project {PROJECT} and secrets in {secrets_dir}")
        else:
            stack.compose("down", "--volumes", "--remove-orphans", check=False, timeout=600)
            shutil.rmtree(secrets_dir, ignore_errors=True)

    print(f"\n{len(results.passed)} passed, {len(results.failed)} failed")
    for failure in results.failed:
        print(f"  FAILED: {failure}")
    return 1 if results.failed else 0


if __name__ == "__main__":
    sys.exit(main())
