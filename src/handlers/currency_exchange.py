from datetime import datetime

from src.application.database import transaction
from src.application.messages import (
    CallbackMessages,
    CallbackQueryContract,
    MessageContract,
    Messages,
)
from src.domain.currency_exchange import (
    CurrencyExchange,
    CurrencyExchangeUncommited,
)
from src.domain.currency_exchange import services as currency_exchange_services
from src.domain.currency_exchange.constants import (
    CurrencyExchangeCallbackOperation,
)
from src.domain.dates import DateFormat
from src.domain.dates import services as dates_services
from src.domain.money import CurrenciesCRUD, CurrencyInDB
from src.domain.money import services as money_services
from src.infrastructure.errors import ValidationError
from src.keyboards.constants import ConfirmationOption
from src.keyboards.default import default_keyboard
from src.keyboards.models import CallbackItem
from src.keyboards.patterns import callback_patterns_keyboard


@transaction
async def confirmation_entered_callback(contract: CallbackQueryContract):
    state = contract.state

    match contract.q.data:
        case CurrencyExchangeCallbackOperation.SELECT_YES:
            state.check_data(
                "source_currency",
                "source_value",
                "destination_currency",
                "destination_value",
                "date",
            )

            schema = CurrencyExchangeUncommited(
                source_value=state.data.source_value,  # type: ignore
                source_currency_id=(
                    state.data.source_currency.id  # type: ignore
                ),
                destination_value=(
                    state.data.destination_value  # type: ignore
                ),
                destination_currency_id=(
                    state.data.destination_currency.id  # type: ignore
                ),
                date=state.data.date,  # type: ignore
                user_id=contract.user.id,
            )
            currency_exchange: CurrencyExchange = (
                await currency_exchange_services.save(schema)
            )
            text = "\n\n".join(
                ("✅ Обмен валют успешно сохранён", currency_exchange.repr())
            )

        case CurrencyExchangeCallbackOperation.SELECT_NO:
            text = "❌ Обмен валют не был сохранён"
            state.clear_data()
        case _:
            raise ValidationError("Что-то пошло не так.\nПопробуйте ещё раз 🏋️")

    await Messages.send(
        contract.user.chat_id, text=text, keyboard=default_keyboard()
    )

    await Messages.delete(contract.user.chat_id, *state.messages_to_delete)
    state.clear_data()


async def date_selected_callback(contract: CallbackQueryContract):
    state = contract.state
    state.check_data(
        "source_currency",
        "source_value",
        "destination_currency",
        "destination_value",
    )
    raw_date = contract.q.data.replace(
        CurrencyExchangeCallbackOperation.SELECT_DATE, ""
    )
    state.data.date = datetime.strptime(raw_date, DateFormat.FULL).date()

    source_value = "".join(
        (
            money_services.repr_value(state.data.source_value),  # type: ignore
            state.data.source_currency.sign,  # type: ignore
        )
    )
    destination_value = "".join(
        (
            money_services.repr_value(
                state.data.destination_value  # type: ignore
            ),
            state.data.destination_currency.sign,  # type: ignore
        )
    )
    text = "\n\n".join(
        (
            "\n".join(
                (
                    f"Исходный счёт 👉 {source_value}",
                    f"Целевой счёт 👉 {destination_value}",  # type: ignore
                    f"Дата 👉 {state.data.date}",  # type: ignore
                )
            ),
            "Вы хотите сохранить обмен валют?",
        )
    )

    keyboard_patterns: list[CallbackItem] = [
        CallbackItem(
            name=ConfirmationOption.NO,
            callback_data=CurrencyExchangeCallbackOperation.SELECT_NO,
        ),
        CallbackItem(
            name=ConfirmationOption.YES,
            callback_data=CurrencyExchangeCallbackOperation.SELECT_YES,
        ),
    ]

    await CallbackMessages.edit(
        q=contract.q,
        text=text,
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )

    state.next_callback = confirmation_entered_callback


async def destination_value_entered_callback(contract: MessageContract):
    state = contract.state
    state.check_data("source_currency", "source_value", "destination_currency")
    state.data.destination_value = money_services.validate(contract.m.text)

    keyboard_patterns: list[CallbackItem] = []

    for date in dates_services.get_last_dates(
        contract.user.configuration.number_of_dates
    ):
        keyboard_patterns.append(
            CallbackItem(
                name=date,
                callback_data="".join(
                    (CurrencyExchangeCallbackOperation.SELECT_DATE, date)
                ),
            )
        )

    message = await Messages.send(
        chat_id=contract.user.chat_id,
        text="📅 Выберите дату",
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )

    state.next_callback = date_selected_callback
    state.messages_to_delete.add(message.id)
    state.messages_to_delete.add(contract.m.id)


async def destination_currency_entered_callback(
    contract: CallbackQueryContract,
):
    state = contract.state
    state.check_data("source_currency", "source_value")
    currency_id = int(
        contract.q.data.replace(
            CurrencyExchangeCallbackOperation.SELECT_DST_CURRENCY, ""
        )
    )
    currency: CurrencyInDB = await CurrenciesCRUD().get(currency_id)

    await CallbackMessages.edit(
        q=contract.q, text="⤵️ Введите сумму, которую вы получили, и нажмите Enter."
    )

    state.next_callback = destination_value_entered_callback
    state.data.destination_currency = currency


async def source_value_entered_callback(contract: MessageContract):
    state = contract.state
    state.check_data("source_currency")
    state.data.source_value = money_services.validate(contract.m.text)
    currencies: list[CurrencyInDB] = await CurrenciesCRUD().exclude(
        state.data.source_currency.id
    )

    keyboard_patterns = [
        CallbackItem(
            name=f"{currency.name} {currency.sign}",
            callback_data=(
                f"{CurrencyExchangeCallbackOperation.SELECT_DST_CURRENCY}"
                f"{currency.id}"
            ),
        )
        for currency in currencies
    ]

    message = await Messages.send(
        chat_id=contract.user.chat_id,
        text="🤔 Выберите целевую валюту",
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )

    state.next_callback = destination_currency_entered_callback
    state.messages_to_delete.add(contract.m.id)
    state.messages_to_delete.add(message.id)


async def source_currency_entered_callback(contract: CallbackQueryContract):
    state = contract.state
    currency_id = int(
        contract.q.data.replace(
            CurrencyExchangeCallbackOperation.SELECT_SRC_CURRENCY, ""
        )
    )
    currency: CurrencyInDB = await CurrenciesCRUD().get(currency_id)

    await CallbackMessages.edit(
        q=contract.q, text="⤵️ Введите сумму, которую вы потратили, и нажмите Enter"
    )

    state.next_callback = source_value_entered_callback
    state.data.source_currency = currency


async def currency_exchange_callback(contract: MessageContract):
    state = contract.state
    state.clear_data()
    state.next_callback = source_currency_entered_callback
    currencies: list[CurrencyInDB] = await CurrenciesCRUD().all()

    keyboard_patterns = [
        CallbackItem(
            name=f"{currency.name} {currency.sign}",
            callback_data=(
                f"{CurrencyExchangeCallbackOperation.SELECT_SRC_CURRENCY}"
                f"{currency.id}"
            ),
        )
        for currency in currencies
    ]

    message = await Messages.send(
        chat_id=contract.user.chat_id,
        text="🤔 Выберите исходную валюту",
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )
    state.messages_to_delete.add(contract.m.id)
    state.messages_to_delete.add(message.id)
