"""API container health check: ``python -m app.healthcheck [live|ready]``.

Requests the API's own health endpoint on the loopback interface and exits
0 on HTTP 200, 1 otherwise. Uses only the standard library; no shell or
HTTP tools are installed in the image.
"""

import sys
import urllib.error
import urllib.request

API_PORT = 8000
TIMEOUT_SECONDS = 4
CHECKS = ("live", "ready")


def main(argv: list[str]) -> int:
    check = argv[1] if len(argv) > 1 else "ready"
    if check not in CHECKS:
        print(f"usage: python -m app.healthcheck [{'|'.join(CHECKS)}]", file=sys.stderr)  # noqa: T201
        return 2
    url = f"http://127.0.0.1:{API_PORT}/api/v1/health/{check}"
    try:
        # Fixed http://127.0.0.1 URL; the only variable part is checked above.
        with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as response:
            return 0 if response.status == 200 else 1
    except (urllib.error.URLError, OSError):
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
