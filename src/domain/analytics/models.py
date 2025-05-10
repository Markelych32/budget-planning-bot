from itertools import groupby
from operator import attrgetter
from typing import AsyncGenerator, Generator

from src.domain.costs import NOT_REAL_COSTS_CATEGORIES, Cost
from src.domain.currency_exchange import CurrencyExchange
from src.domain.dates import DateFormat
from src.domain.incomes import NOT_REAL_REVENUE_SOURCES, Income
from src.domain.money import CurrenciesCRUD, CurrencyInDB
from src.domain.money import services as money_services
from src.infrastructure.database import IncomeSource
from src.infrastructure.models import InternalModel
from src.settings import TELEGRAM_MESSAGE_MAX_LEN

__all__ = ("AnalyticsResult",)


class AnalyticsResult(InternalModel):

    costs: list[Cost]
    incomes: list[Income]
    currency_exchanges: list[CurrencyExchange]

    def get_costs_to_revenue_ratio(self, currency: CurrencyInDB) -> float:

        costs = sum(c.value for c in self.costs if c.currency == currency)
        incomes = sum(i.value for i in self.incomes if i.currency == currency)
        curr_exchanges_destination = sum(
            curr_exchange.destination_value
            for curr_exchange in self.currency_exchanges
            if curr_exchange.destination_currency == currency
        )
        curr_exchanges_source = sum(
            curr_exchange.source_value
            for curr_exchange in self.currency_exchanges
            if curr_exchange.source_currency == currency
        )

        return costs / (
            incomes + curr_exchanges_destination - curr_exchanges_source
        )

    @property
    def costs_by_currency(self) -> dict[int, list[Cost]]:
        currency_attr_key = attrgetter("currency.id")
        costs_by_currency = groupby(
            sorted(self.costs, key=currency_attr_key), currency_attr_key
        )
        return {k: list(v) for k, v in costs_by_currency}

    @property
    def incomes_by_currency(self) -> dict[int, list[Income]]:
        currency_attr_key = attrgetter("currency.id")
        incomes_by_currency = groupby(
            sorted(self.incomes, key=currency_attr_key), currency_attr_key
        )
        return {k: list(v) for k, v in incomes_by_currency}

    def _get_basic_representation(
        self,
        currency: CurrencyInDB,
        costs: list[Cost] | None,
        incomes: list[Income] | None,
    ) -> str:
        message = (
            f"📊 Аналитика для {currency.sign} {currency.name} "
            f"{currency.sign}\n"
        )

        costs_total = 0
        real_costs_total = 0
        incomes_total = 0
        real_revenue_total = 0
        debts_total = 0
        gifts_total = 0
        exchanges_source_total = 0
        exchanges_destination_total = 0

        if costs:
            message += "\n<b>🔥 Расходы</b>\n"
            costs_total = sum((c.value for c in costs))
            real_costs_total = sum(
                (
                    c.value
                    for c in costs
                    if c.category.name not in NOT_REAL_COSTS_CATEGORIES
                )
            )

            grouping_key = attrgetter("category.name")
            for category_name, category_costs in groupby(
                sorted(costs, key=grouping_key), key=grouping_key
            ):
                category_costs_total = sum((c.value for c in category_costs))
                try:
                    ratio: float = (
                        category_costs_total / real_costs_total
                    ) * 100
                except ZeroDivisionError:
                    ratio = 0.0
                message += (
                    f"\n{category_name} 👉 "
                    f"{money_services.repr_value(category_costs_total)}"
                )
                if category_name not in NOT_REAL_COSTS_CATEGORIES:
                    message += f" <i>({ratio:.2f}%)</i>"

        debts_total = (
            sum((i.value for i in incomes if i.source == IncomeSource.DEBT))
            if incomes
            else 0
        )
        gifts_total = (
            sum((i.value for i in incomes if i.source == IncomeSource.GIFT))
            if incomes
            else 0
        )

        if debts_total or gifts_total:
            message += "\n\n<b>🚌 ДРУГИЕ ДОХОДЫ:</b>\n\n"

        message += "\n".join(
            (
                f"🪙 Долги 👉 {money_services.repr_value(debts_total)}"
                if debts_total
                else "",
                f"🎁 Подарки 👉 {money_services.repr_value(gifts_total)}"
                if gifts_total
                else "",
            )
        )

        exchanges_source_total = sum(
            ex.source_value
            for ex in self.currency_exchanges
            if ex.source_currency.id == currency.id
        )
        exchanges_destination_total = sum(
            ex.destination_value
            for ex in self.currency_exchanges
            if ex.destination_currency.id == currency.id
        )

        if exchanges_source_total or exchanges_destination_total:
            message += "\n\n<b>🚌 ОБМЕН ВАЛЮТ:</b>\n\n"

        message += "\n".join(
            (
                f"💱 Конвертировано в эту валюту 👉 {money_services.repr_value(exchanges_destination_total)}"  # noqa
                if exchanges_destination_total
                else "",
                f"💱 Конвертировано из этой валюты 👉 {money_services.repr_value(exchanges_source_total)}"  # noqa
                if exchanges_source_total
                else "",
            )
        )

        if costs or incomes or self.currency_exchanges:
            message += "\n\n<b>🚌 ОБЩИЕ ЗНАЧЕНИЯ:</b>\n\n"

        incomes_total = sum((i.value for i in incomes)) if incomes else 0
        real_revenue_total = (
            sum(
                (
                    i.value
                    for i in incomes
                    if i.source not in NOT_REAL_REVENUE_SOURCES
                )
            )
            if incomes
            else 0
        )

        message += "\n".join(
            (
                f"💹 Все доходы 👉 {money_services.repr_value(incomes_total)}"  # noqa
                if incomes_total
                else "",
                f"🔥 Все расходы 👉 {money_services.repr_value(costs_total)}"
                if costs_total
                else "",
                "" if costs_total and incomes_total else "",
                f"💹 Реальный доход 👉 {money_services.repr_value(real_revenue_total)}"  # noqa
                if real_revenue_total
                else "",
                f"🔥 Реальные затраты 👉 {money_services.repr_value(real_costs_total)}\n"  # noqa
                if real_costs_total
                else "",
            )
        )

        if costs or incomes or self.currency_exchanges:
            message += "\n\n<b>🚌 ОБЩЕЕ СООТНОШЕНИЕ:</b>\n\n"

        try:
            real_costs_to_real_revenue = (
                real_costs_total
                / (
                    real_revenue_total
                    + exchanges_destination_total
                    - exchanges_source_total
                )
            ) * 100
        except ZeroDivisionError:
            real_costs_to_real_revenue = 0

        try:
            all_costs_to_all_incomes = (
                costs_total
                / (
                    incomes_total
                    + exchanges_destination_total
                    - exchanges_source_total
                )
            ) * 100
        except ZeroDivisionError:
            all_costs_to_all_incomes = 0

        message += "\n".join(
            (
                "Соотношение реальных затрат и реальных доходов 👉 "
                f"<b>{real_costs_to_real_revenue:.2f}%</b>",
                "Отношение всех расходов ко всем доходам 👉 "
                f"{all_costs_to_all_incomes:.2f}%",
            )
        )

        return message

    async def get_basic_representation(self) -> AsyncGenerator[str, None]:

        currencies: list[CurrencyInDB] = await CurrenciesCRUD().all()

        for currency in currencies:
            yield self._get_basic_representation(
                currency,
                costs=self.costs_by_currency.get(currency.id),
                incomes=self.incomes_by_currency.get(currency.id),
            )

    def get_detailed_representation(
        self, date_format: DateFormat
    ) -> Generator[str, None, None]:
        grouping_key = attrgetter("category.name")
        costs_by_category = groupby(
            sorted(self.costs, key=grouping_key), key=grouping_key
        )

        costs_title = "<b>🔥 Расходы</b>\n"

        message = costs_title

        for category_name, costs in costs_by_category:
            message += f"\n\n<b>{category_name}</b>"

            for cost in costs:
                cost_repr = (
                    f"\n👉 <i>{cost.date.strftime(date_format)}</i>  "
                    f"{cost.name}  {money_services.repr_value(cost.value)}"
                    f"{cost.currency.sign}"
                )

                if len(message) + len(cost_repr) > TELEGRAM_MESSAGE_MAX_LEN:
                    yield message
                    message = ""

                message += cost_repr

        if message and message != costs_title:
            yield message

        grouping_key = attrgetter("source")
        incomes_by_source = groupby(
            sorted(self.incomes, key=grouping_key), key=grouping_key
        )

        incomes_title = "<b>💹 Доходы</b>\n"

        message = incomes_title

        for source, incomes in incomes_by_source:
            message += f"\n\n<b>{source.capitalize()}s</b>"

            for income in incomes:
                cost_repr = (
                    f"\n👉 <i>{income.date.strftime(date_format)}</i>  "
                    f"{income.name}  {money_services.repr_value(income.value)}"
                    f"{income.currency.sign}"
                )

                if len(message) + len(cost_repr) > TELEGRAM_MESSAGE_MAX_LEN:
                    yield message
                    message = ""

                message += cost_repr

        if message and message != incomes_title:
            yield message
            message = ""

        currency_exchanges_title = "<b>💱 Обмен валют</b>\n"

        message = currency_exchanges_title

        for currency_exchange in self.currency_exchanges:
            cost_repr = (
                f"\n👉 <i>{currency_exchange.date.strftime(date_format)}</i>  "
                f"{money_services.repr_value(currency_exchange.source_value)}"
                f"{currency_exchange.source_currency.sign}  🔀  "
                f"{money_services.repr_value(currency_exchange.destination_value)}"  # noqa
                f"{currency_exchange.destination_currency.sign} "
            )

            if len(message) + len(cost_repr) > TELEGRAM_MESSAGE_MAX_LEN:
                yield message
                message = ""

            message += cost_repr

        # Send last incomes frame befor moving forward
        if message and message != currency_exchanges_title:
            yield message
