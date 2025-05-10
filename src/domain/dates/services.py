import calendar
from datetime import date, timedelta
from functools import partial
from typing import Generator

from src.domain.dates.constants import DateFormat


def month_dates_range(year: int, month: int) -> tuple[date, date]:
    _month = partial(date, year=year, month=month)
    _, last_day = calendar.monthrange(year, month)

    first_date = _month(day=1)
    last_date = _month(day=last_day)

    return first_date, last_date


def this_month_edge_dates() -> tuple[date, date]:

    today = date.today()
    return month_dates_range(year=today.year, month=today.month)


def previous_month_edge_dates() -> tuple[date, date]:

    prev_month_day = date.today().replace(day=1) - timedelta(days=1)
    return month_dates_range(
        year=prev_month_day.year, month=prev_month_day.month
    )


def represent_dates_range(
    first_date: date, last_date: date, date_format: DateFormat
) -> Generator[str, None, None]:

    if first_date == last_date:
        yield last_date.strftime(date_format)
        return

    while last_date > first_date:
        yield last_date.strftime(date_format)
        last_date -= timedelta(days=last_date.day)


def get_last_dates(amount: int) -> Generator[str, None, None]:

    for i in range(amount):
        yield (date.today() - timedelta(days=i)).strftime(DateFormat.FULL)
