"""Contracts mirrored by the frontend must stay aligned with the backend."""

import re
from pathlib import Path

from webwhen.connectors.client import ConnectionStatus

FRONTEND_TYPES = Path(__file__).resolve().parents[2] / "frontend" / "src" / "types" / "index.ts"


def test_frontend_connection_status_matches_backend_enum() -> None:
    source = FRONTEND_TYPES.read_text()
    declaration = re.search(
        r"export type ConnectionStatus\s*=\s*(.*?);",
        source,
        flags=re.DOTALL,
    )
    assert declaration is not None, "frontend ConnectionStatus declaration not found"

    frontend_values = set(re.findall(r'["\']([^"\']+)["\']', declaration.group(1)))
    backend_values = {status.value for status in ConnectionStatus}

    assert frontend_values == backend_values
