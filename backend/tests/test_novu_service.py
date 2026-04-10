"""Tests for Novu notification helpers."""

import pytest

from torale.notifications.novu_service import _format_confidence


class TestFormatConfidence:
    """Confidence arrives as int 0-100 (MonitoringResponse schema).

    Regression: a prior version multiplied by 100, producing "9500%"/"10000%"
    in notification emails.
    """

    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, None),
            (0, "0%"),
            (50, "50%"),
            (95, "95%"),
            (100, "100%"),
        ],
    )
    def test_format(self, value, expected):
        assert _format_confidence(value) == expected
