"""Env var compatibility shim for the torale → webwhen rename.

Reads `WEBWHEN_*` first, falls back to `TORALE_*` with a once-per-var
DeprecationWarning. Centralized so SDK clients, the API, tests, and the
Pydantic settings model all agree on the same fallback policy.
"""

from __future__ import annotations

import os
import warnings

_warned: set[str] = set()


def getenv(name: str, default: str | None = None) -> str | None:
    """Read an env var with torale → webwhen back-compat.

    Args:
        name: The new-style env var name (e.g. "WEBWHEN_API_KEY").
              Must start with the WEBWHEN_ prefix.
        default: Returned if neither WEBWHEN_* nor TORALE_* is set.

    Returns:
        Value of WEBWHEN_<name> if set, else value of TORALE_<name> (with
        a one-time DeprecationWarning), else default.
    """
    if not name.startswith("WEBWHEN_"):
        raise ValueError(f"webwhen.core.env.getenv expects a WEBWHEN_-prefixed name, got: {name}")

    value = os.environ.get(name)
    if value is not None:
        return value

    legacy_name = "TORALE_" + name[len("WEBWHEN_") :]
    legacy_value = os.environ.get(legacy_name)
    if legacy_value is not None:
        if legacy_name not in _warned:
            _warned.add(legacy_name)
            warnings.warn(
                f"Environment variable {legacy_name!r} is deprecated, use {name!r} instead. "
                "The torale-prefixed env vars are scheduled for removal after 2026-11-30; "
                "see webwhen issue #364.",
                DeprecationWarning,
                stacklevel=2,
            )
        return legacy_value

    return default


def config_paths() -> list:
    """Config-file lookup order: prefer ~/.webwhen/config.json, fall back to ~/.torale/config.json.

    Returns the existing paths in preference order. Callers iterate and read
    the first that succeeds. The torale path is fallback-only; if both exist,
    webwhen wins. Use of the legacy path emits a one-time DeprecationWarning
    via the caller (the path-list itself is silent).
    """
    from pathlib import Path

    home = Path.home()
    return [home / ".webwhen" / "config.json", home / ".torale" / "config.json"]


def warn_legacy_config_path(path) -> None:
    """Emit a one-time DeprecationWarning when the legacy ~/.torale/config.json is read."""
    key = f"config:{path}"
    if key in _warned:
        return
    _warned.add(key)
    warnings.warn(
        f"Reading from legacy config path {path}. "
        "Move it to ~/.webwhen/config.json — the .torale path is scheduled to stop being "
        "read after 2026-11-30; see webwhen issue #364.",
        DeprecationWarning,
        stacklevel=2,
    )
