"""Tests for the Playwright summary printed by the smoke test (DECISIONS.md D-073).

The browser tests run in a child process whose output is captured. Only the
lines that ``playwright_summary`` keeps reach the CI log, so these tests pin
what is kept, what is dropped and what is redacted.
"""

import importlib.util
import re
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

SMOKE_TEST = Path(__file__).resolve().parents[1] / "scripts" / "smoke_test.py"


def load_smoke_test() -> ModuleType:
    spec = importlib.util.spec_from_file_location("smoke_test", SMOKE_TEST)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


smoke = load_smoke_test()
summary: Callable[..., str] = smoke.playwright_summary
DIAGNOSTICS = smoke.REGISTRATION_DIAGNOSTICS
PASSWORD = "correct horse battery 0123456789ab"


def test_keeps_the_counts_and_failed_titles() -> None:
    output = "\n".join(
        [
            "Running 24 tests using 1 worker",
            "  ok  1 [chromium] > sign in works (1.0s)",
            "  x  2 [chromium] > registration > visitor registers (30.1s)",
            "",
            "  1) [chromium] > registration > visitor registers",
            "    Error: Test timeout of 30000ms exceeded.",
            "  23 passed (51.1s)",
            "  1 failed",
        ]
    )

    text = summary(output, [])

    assert "23 passed (51.1s)" in text
    assert "1 failed" in text
    assert "1) [chromium] > registration > visitor registers" in text
    assert "Error: Test timeout of 30000ms exceeded." in text


def test_keeps_every_registration_diagnostic_line() -> None:
    lines = [
        f"{DIAGNOSTICS} when an administrator enables it, a visitor can register",
        f"{DIAGNOSTICS}   test status: failed",
        f"{DIAGNOSTICS}   /auth/options: status 200, registration_enabled true",
        f"{DIAGNOSTICS}   /auth/me: status 401",
        f"{DIAGNOSTICS}   current path: /register",
        f"{DIAGNOSTICS}   registration form shown: false",
        f"{DIAGNOSTICS}   visible alerts: none",
    ]

    text = summary("\n".join(["  x  1 [chromium] > registration", *lines]), [])

    for line in lines:
        assert line.strip() in text
    assert text.count(DIAGNOSTICS) == len(lines)


def test_drops_unrelated_output() -> None:
    output = "\n".join(
        [
            "  attachment #1: screenshot (image/png)",
            "    <html><body>visitor@example.test</body></html>",
            "  - text: Email address",
            '  textbox "Email address": e2e-1234@example.test',
        ]
    )

    assert summary(output, []) == ""


def test_redacts_the_administrator_password_everywhere() -> None:
    password = "correct horse battery 0123456789ab"
    output = "\n".join(
        [
            "Error: login failed for admin with " + password,
            f"{DIAGNOSTICS}   alerts: sign-in failed near {password}",
        ]
    )

    text = summary(output, [password])

    assert password not in text
    assert text.count("[REDACTED]") == 2


def test_limits_the_number_of_diagnostic_lines_and_says_so() -> None:
    output = "\n".join(f"{DIAGNOSTICS} line {index}" for index in range(100))

    text = summary(output, [])

    assert text.count(DIAGNOSTICS) == smoke.MAX_DIAGNOSTIC_LINES + 1
    assert "line 0" in text
    assert "line 99" not in text
    assert "70 more diagnostic line(s) omitted" in text


def test_bounds_long_diagnostic_values_and_marks_the_cut() -> None:
    long_value = "x" * 5000

    text = summary(f"{DIAGNOSTICS} visible alerts: {long_value}", [])

    assert text.count("[truncated]") == 1
    assert len(text) <= smoke.MAX_SUMMARY_CHARS // 4 + len(" [truncated]")


def test_a_password_crossing_the_diagnostic_cut_is_fully_redacted() -> None:
    # The diagnostic line is cut after MAX_SUMMARY_CHARS // 4 characters. This places
    # the first 20 characters of the password before the cut, so a partial value is
    # what a cut-then-redact filter would leave in the log.
    width = smoke.MAX_SUMMARY_CHARS // 4
    prefix = f"{DIAGNOSTICS} visible alerts: "
    filler = "x" * (width - len(prefix) - 20)
    output = prefix + filler + PASSWORD + " trailing text"

    text = summary(output, [PASSWORD])

    assert PASSWORD[:12] not in text
    assert PASSWORD[-12:] not in text
    assert "[REDACTED]" in text


def test_a_password_crossing_the_summary_cut_is_fully_redacted() -> None:
    # Error lines are cut to their last MAX_SUMMARY_CHARS characters. The tail below
    # starts inside the password, so the surviving part is its last 20 characters.
    output = "Error: " + PASSWORD + "y" * 1480

    text = summary(output, [PASSWORD])

    assert PASSWORD[14:] not in text
    assert "[REDACTED]" in text


def test_the_browser_test_prints_the_marker_the_filter_keeps() -> None:
    spec = (
        Path(__file__).resolve().parents[2] / "apps" / "frontend" / "e2e" / "authentication.spec.ts"
    )
    match = re.search(r"const DIAGNOSTICS_MARKER = '([^']+)'", spec.read_text(encoding="utf-8"))

    assert match is not None
    assert match.group(1) == smoke.REGISTRATION_DIAGNOSTICS
