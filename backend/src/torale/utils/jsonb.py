"""Utilities for parsing JSONB columns from the database."""

import json
import logging

logger = logging.getLogger(__name__)


def parse_jsonb(raw: object, field_name: str, expected_type: type, default: object) -> object:
    """Parse a JSONB column that may be a string, already-deserialized, or None."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Corrupt %s JSON in execution row: %s", field_name, raw[:200])
            return default
    if not isinstance(raw, expected_type):
        if raw is not None:
            logger.warning("Unexpected %s type %s in execution row", field_name, type(raw).__name__)
        return default
    return raw
