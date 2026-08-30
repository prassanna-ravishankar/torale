"""Back-compat shim for `torale.sdk` (renamed to `webwhen.sdk`).

Lazy proxy: only emits a DeprecationWarning when a symbol is actually accessed,
not at import time. Each name resolves to the same canonical object exposed by
`webwhen.sdk` — these are aliases, not duplicate classes.
"""

from __future__ import annotations

import importlib
import warnings

_DEPRECATED: dict[str, tuple[str, str]] = {
    "Webwhen": ("webwhen.sdk", "Webwhen"),
    "WebwhenAsync": ("webwhen.sdk", "WebwhenAsync"),
    "WebwhenClient": ("webwhen.sdk.client", "WebwhenClient"),
    "WebwhenAsyncClient": ("webwhen.sdk.async_client", "WebwhenAsyncClient"),
    "WebwhenError": ("webwhen.sdk.exceptions", "WebwhenError"),
    "Torale": ("webwhen.sdk", "Webwhen"),
    "ToraleAsync": ("webwhen.sdk", "WebwhenAsync"),
    "ToraleClient": ("webwhen.sdk.client", "WebwhenClient"),
    "ToraleAsyncClient": ("webwhen.sdk.async_client", "WebwhenAsyncClient"),
    "ToraleError": ("webwhen.sdk.exceptions", "WebwhenError"),
    "monitor": ("webwhen.sdk", "monitor"),
    "MonitorBuilder": ("webwhen.sdk", "MonitorBuilder"),
    "TasksResource": ("webwhen.sdk", "TasksResource"),
    "AsyncTasksResource": ("webwhen.sdk", "AsyncTasksResource"),
    "WebhooksResource": ("webwhen.sdk", "WebhooksResource"),
    "AsyncWebhooksResource": ("webwhen.sdk", "AsyncWebhooksResource"),
    "AuthenticationError": ("webwhen.sdk.exceptions", "AuthenticationError"),
    "NotFoundError": ("webwhen.sdk.exceptions", "NotFoundError"),
    "ValidationError": ("webwhen.sdk.exceptions", "ValidationError"),
    "RateLimitError": ("webwhen.sdk.exceptions", "RateLimitError"),
    "APIError": ("webwhen.sdk.exceptions", "APIError"),
}

_warned: set[str] = set()


def __getattr__(name: str):
    if name in _DEPRECATED:
        module_path, new_name = _DEPRECATED[name]
        if name not in _warned:
            _warned.add(name)
            warnings.warn(
                f"'torale.sdk.{name}' is deprecated, use '{module_path}.{new_name}' instead. "
                "The 'torale' package is scheduled for removal after 2026-11-30; "
                "see webwhen issue #364.",
                DeprecationWarning,
                stacklevel=2,
            )
        module = importlib.import_module(module_path)
        return getattr(module, new_name)
    raise AttributeError(f"module 'torale.sdk' has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(_DEPRECATED.keys())
