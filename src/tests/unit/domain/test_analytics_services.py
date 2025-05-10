from datetime import date

import pytest

from src.domain.analytics import services as analytics_service
from src.infrastructure.errors import UserError


@pytest.mark.parametrize(
    "payload,expected_range",
    [
        (
            "2022",
            (
                date(year=2022, month=1, day=1),
                date(year=2022, month=12, day=31),
            ),
        ),
        (
            "2021-2022",
            (
                date(year=2021, month=1, day=1),
                date(year=2022, month=12, day=31),
            ),
        ),
        (
            "2023-02",
            (
                date(year=2023, month=2, day=1),
                date(year=2023, month=2, day=28),
            ),
        ),
        (
            "2023-2",
            (
                date(year=2023, month=2, day=1),
                date(year=2023, month=2, day=28),
            ),
        ),
        (
            "2023-02 - 2023-03",
            (
                date(year=2023, month=2, day=1),
                date(year=2023, month=3, day=31),
            ),
        ),
        (
            "2023-2-4-2023-6-5",
            (
                date(year=2023, month=2, day=4),
                date(year=2023, month=6, day=5),
            ),
        ),
    ],
)
def test_date_range_pattern_validation(payload, expected_range):
    result = analytics_service.dates_range_by_pattern(payload)
    assert result == expected_range


@pytest.mark.parametrize(
    "payload",
    [
        "2023-2-4-2023-6",
    ],
)
def test_date_range_pattern_validation_invalid(payload):
    with pytest.raises(UserError):
        analytics_service.dates_range_by_pattern(payload)
