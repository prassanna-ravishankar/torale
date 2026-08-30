"""Back-compat shim: `torale` was renamed to `webwhen`.

Importing `torale` itself does not emit a warning — that would punish
anyone whose unrelated tooling happens to put this package on the path.
The DeprecationWarning fires lazily, only when a symbol is actually
accessed by its old name (`from torale import Torale`,
`torale.Torale`, etc.).

When you see a warning, replace the import:

    from torale import Torale       →   from webwhen import Webwhen
    from torale import ToraleAsync  →   from webwhen import WebwhenAsync
    from torale.sdk import Torale   →   from webwhen.sdk import Webwhen

The canonical class names (`Webwhen*`) work the same way the old
`Torale*` names used to. The `Torale*` aliases inside `webwhen` are
pure identity aliases (`Torale is Webwhen`), so nothing about runtime
behavior differs — only the names.

The torale-prefixed env vars (`TORALE_API_KEY`, `TORALE_NOAUTH`, etc.)
remain readable through the same once-per-var DeprecationWarning;
that's handled separately in `webwhen.core.env`.
"""

from __future__ import annotations

import importlib
import warnings

# Map of old-name → (canonical module path, canonical attr name).
# All values resolve to the same Python objects exposed under
# `webwhen.*` — these are not duplicate definitions.
_DEPRECATED: dict[str, tuple[str, str]] = {
    "Webwhen": ("webwhen", "Webwhen"),
    "WebwhenAsync": ("webwhen", "WebwhenAsync"),
    "WebwhenError": ("webwhen", "WebwhenError"),
    "Torale": ("webwhen", "Webwhen"),
    "ToraleAsync": ("webwhen", "WebwhenAsync"),
    "ToraleError": ("webwhen", "WebwhenError"),
    "monitor": ("webwhen", "monitor"),
    "MonitorBuilder": ("webwhen", "MonitorBuilder"),
    "TasksResource": ("webwhen", "TasksResource"),
    "AsyncTasksResource": ("webwhen", "AsyncTasksResource"),
    "WebhooksResource": ("webwhen", "WebhooksResource"),
    "AsyncWebhooksResource": ("webwhen", "AsyncWebhooksResource"),
    "AuthenticationError": ("webwhen", "AuthenticationError"),
    "NotFoundError": ("webwhen", "NotFoundError"),
    "ValidationError": ("webwhen", "ValidationError"),
    "RateLimitError": ("webwhen", "RateLimitError"),
    "APIError": ("webwhen", "APIError"),
    "__version__": ("webwhen", "__version__"),
}

_warned: set[str] = set()


def __getattr__(name: str):
    """PEP 562 — fires only when a symbol is actually accessed."""
    if name in _DEPRECATED:
        module_path, new_name = _DEPRECATED[name]
        if name not in _warned:
            _warned.add(name)
            warnings.warn(
                f"'torale.{name}' is deprecated, use '{module_path}.{new_name}' instead. "
                "The 'torale' package is scheduled for removal after 2026-11-30; "
                "see webwhen issue #364.",
                DeprecationWarning,
                stacklevel=2,
            )
        module = importlib.import_module(module_path)
        return getattr(module, new_name)
    raise AttributeError(f"module 'torale' has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(_DEPRECATED.keys())
