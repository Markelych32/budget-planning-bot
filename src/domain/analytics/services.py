"""
This module includes services that focused on generating reports for the user.
It means that it aggregates costs, incomes and currency exchanges
in order to build the response.
"""

import calendar
import re
from datetime import date, datetime
from typing import AsyncGenerator

from src.domain.analytics.constants import DatesRangeRegex
from src.domain.analytics.models import AnalyticsResult
from src.domain.costs import Cost, CostsCRUD
from src.domain.currency_exchange import CurrencyExchange, CurrencyExchangeCRUD
from src.domain.dates import DateFormat
from src.domain.incomes import Income, IncomesCRUD
from src.domain.users import User
from src.infrastructure.errors import UserError

dates_pattern_error = UserError(
    "⚠️ Некорректный шаблон даты.\n\n"
    "Вот несколько примеров корректного ввода:\n"
    "2022: конкретный год\n"
    "2022-2023: диапазон лет\n"
    "04-2022: месяц конкретного года\n"
    "04-2022 - 03-2023: диапазон месяцев\n"
    "01-04-2022 - 03-04-2022: диапазон точных дат"
)


def _get_matched_regex_by_payload(payload: str) -> DatesRangeRegex:
    for regex in DatesRangeRegex:
        if re.fullmatch(regex, payload):
            return regex

    raise dates_pattern_error


def dates_range_by_pattern(payload: str | None) -> tuple[date, date]:
    """This function gets the payload and return the range of dates.
    Here is the rule of detecting dates patterns:
    """

    if not payload:
        raise dates_pattern_error

    filtered_payload = payload.replace(" ", "")

    match _get_matched_regex_by_payload(filtered_payload):
        case DatesRangeRegex.YEAR:
            start_date = date(year=int(filtered_payload), month=1, day=1)
            end_date = date(year=int(filtered_payload), month=12, day=31)
            return start_date, end_date
        case DatesRangeRegex.YEARS:
            first_year, last_year = filtered_payload.split("-")
            start_date = date(year=int(first_year), month=1, day=1)
            end_date = date(year=int(last_year), month=12, day=31)
            return start_date, end_date
        case DatesRangeRegex.MONTH:
            start_date = datetime.strptime(filtered_payload, "%Y-%m").date()
            _, last_day = calendar.monthrange(
                start_date.year, start_date.month
            )
            end_date = date(
                year=start_date.year, month=start_date.month, day=last_day
            )
            return start_date, end_date
        case DatesRangeRegex.MONTHS:
            _format = "%Y-%m"
            parts = filtered_payload.split("-")
            start_date = datetime.strptime("-".join(parts[:2]), _format).date()
            _end_date = datetime.strptime("-".join(parts[2:]), _format).date()
            _, last_day = calendar.monthrange(_end_date.year, _end_date.month)
            end_date = date(
                year=_end_date.year, month=_end_date.month, day=last_day
            )
            return start_date, end_date
        case DatesRangeRegex.DAYS:
            _format = "%Y-%m-%d"
            parts = filtered_payload.split("-")
            start_date = datetime.strptime("-".join(parts[:3]), _format).date()
            end_date = datetime.strptime("-".join(parts[3:]), _format).date()
            return start_date, end_date

    raise dates_pattern_error


async def get_detailed_costs_in_range(
    start: date,
    end: date,
    date_format: DateFormat = DateFormat.FULL,
    by_user: User | None = None,
    category_id: int | None = None,
) -> AsyncGenerator[str, None]:
    costs: list[Cost] = await CostsCRUD().in_dates_range(
        start, end, by_user, category_id
    )
    analytics_result = AnalyticsResult(
        costs=costs, incomes=[], currency_exchanges=[]
    )

    for frame in analytics_result.get_detailed_representation(date_format):
        yield frame


async def get_detailed_incomes_in_range(
    start: date, end: date, date_format: DateFormat = DateFormat.FULL
) -> AsyncGenerator[str, None]:
    incomes: list[Income] = await IncomesCRUD().in_dates_range(start, end)
    analytics_result = AnalyticsResult(
        incomes=incomes, costs=[], currency_exchanges=[]
    )

    for frame in analytics_result.get_detailed_representation(date_format):
        yield frame


async def get_detailed_currency_exchanges_in_range(
    start: date, end: date, date_format: DateFormat = DateFormat.FULL
) -> AsyncGenerator[str, None]:
    currency_exchanges: list[
        CurrencyExchange
    ] = await CurrencyExchangeCRUD().in_dates_range(start, end)
    analytics_result = AnalyticsResult(
        currency_exchanges=currency_exchanges, costs=[], incomes=[]
    )

    for frame in analytics_result.get_detailed_representation(date_format):
        yield frame


async def get_detailed_analytics_in_range(
    start: date,
    end: date,
    date_format: DateFormat = DateFormat.FULL,
    by_user: User | None = None,
) -> AsyncGenerator[str, None]:
    """Get user's analytics result in specified range by frames."""

    costs: list[Cost] = await CostsCRUD().in_dates_range(start, end, by_user)
    incomes: list[Income] = await IncomesCRUD().in_dates_range(
        start, end, by_user
    )
    currency_exchanges: list[
        CurrencyExchange
    ] = await CurrencyExchangeCRUD().in_dates_range(start, end, by_user)

    analytics_result = AnalyticsResult(
        costs=costs, incomes=incomes, currency_exchanges=currency_exchanges
    )

    for frame in analytics_result.get_detailed_representation(date_format):
        yield frame


async def get_basic_analytics_in_range(
    start: date, end: date, by_user: User | None = None
) -> AsyncGenerator[str, None]:
    """Get user's analytics result in specified range by frames."""

    costs: list[Cost] = await CostsCRUD().in_dates_range(start, end, by_user)
    incomes: list[Income] = await IncomesCRUD().in_dates_range(
        start, end, by_user
    )
    currency_exchanges: list[
        CurrencyExchange
    ] = await CurrencyExchangeCRUD().in_dates_range(start, end, by_user)

    analytics_result = AnalyticsResult(
        costs=costs, incomes=incomes, currency_exchanges=currency_exchanges
    )

    async for frame in analytics_result.get_basic_representation():
        yield frame
