"""Container health check with a short timeout and explicit failure exit code."""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request


host = os.getenv("APEX_HEALTHCHECK_HOST", "127.0.0.1")
port = os.getenv("APEX_PORT", "8000")
url = f"http://{host}:{port}/api/health"

try:
    with urllib.request.urlopen(url, timeout=3) as response:
        if response.status != 200:
            raise RuntimeError(f"health endpoint returned HTTP {response.status}")
except (OSError, urllib.error.URLError, RuntimeError) as exc:
    print(f"APEX health check failed: {exc}", file=sys.stderr)
    raise SystemExit(1)

raise SystemExit(0)
