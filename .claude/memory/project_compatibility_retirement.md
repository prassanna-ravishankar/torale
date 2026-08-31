---
name: compatibility-retirement
description: Dated removal windows for temporary protocol and rebrand shims
type: project
---

# Compatibility retirement windows

- Remove the `torale`/`torale.sdk` import shims, `TORALE_*` environment
  fallbacks, and `~/.torale/config.json` fallback after **2026-11-30**, in the
  next SDK major release. Tracking:
  [#364](https://github.com/prassanna-ravishankar/webwhen/issues/364).

Do not add new consumers of these compatibility paths. Canonical code, docs,
and deployment configuration use `webwhen`, `WEBWHEN_*`, and `~/.webwhen`.
