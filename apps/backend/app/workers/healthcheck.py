"""Worker container health check: ``python -m app.workers.healthcheck``.

Exits 0 when the worker's heartbeat file is fresh (the worker is connected
to the broker and consuming), 1 otherwise. No shell is involved.
"""

import sys
from pathlib import Path

from app.core.config import get_settings
from app.workers.heartbeat import is_fresh


def main() -> int:
    return 0 if is_fresh(Path(get_settings().worker_heartbeat_file)) else 1


if __name__ == "__main__":
    sys.exit(main())
