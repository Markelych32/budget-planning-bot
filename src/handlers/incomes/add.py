from datetime import datetime

from src.application.database import transaction
from src.application.messages import (
    CallbackMessages,
    CallbackQueryContract,
    MessageContract,
    Messages,
)
from src.domain.dates import DateFormat
from src.domain.dates import services as dates_services
from src.domain.incomes import (
    AddIncomeCallbackOperation,
    Income,
    IncomeUncommited,
)
from src.domain.incomes import services as incomes_services
from src.domain.money import CurrenciesCRUD, CurrencyInDB
from src.domain.money import services as money_services
from src.infrastructure.errors import UserError, ValidationError
from src.keyboards.constants import (
    INCOME_SOURCES_KEYBOARD_ELEMENTS,
    ConfirmationOption,
)
from src.keyboards.default import default_keyboard
from src.keyboards.models import CallbackItem
from src.keyboards.patterns import (
    callback_patterns_keyboard,
    patterns_keyboard,
)


@transaction
async def confirmation_selected_callback(contract: CallbackQueryContract):
    state = contract.state
    state.messages_to_delete.add(contract.q.id)

    match contract.q.data:
        case AddIncomeCallbackOperation.SELECT_YES:
            state.check_data("value", "currency", "name", "source", "date")
            schema = IncomeUncommited(
                name=state.data.name,  # type: ignore
                value=state.data.value,  # type: ignore
                source=state.data.source,  # type: ignore
                date=state.data.date,  # type: ignore
                currency_id=state.data.currency.id,  # type: ignore
                user_id=contract.user.id,
            )

            income: Income = await incomes_services.add(schema)
            text = "\n\n".join(("✅ Доход успешно сохранён", income.repr()))

        case AddIncomeCallbackOperation.SELECT_NO:
            text = "❌ Доход не был сохранён"
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
    state.check_data("value", "currency", "name", "source")

    date_raw: str = contract.q.data.replace(
        AddIncomeCallbackOperation.SELECT_DATE, ""
    )
    state.data.date = datetime.strptime(date_raw, DateFormat.FULL).date()

    repr_value = "".join(
        (
            money_services.repr_value(state.data.value),
            state.data.currency.sign,
        )
    )
    text = "\n\n".join(
        (
            "\n".join(
                (
                    f"Название 👉 {state.data.name}",
                    f"Значение 👉 {repr_value}",
                    f"Источник 👉 {state.data.source}",
                    f"Дата 👉 {state.data.date}",
                )
            ),
            "Вы хотите сохранить доход?",
        )
    )

    keyboard_patterns: list[CallbackItem] = [
        CallbackItem(
            name=ConfirmationOption.NO,
            callback_data=AddIncomeCallbackOperation.SELECT_NO,
        ),
        CallbackItem(
            name=ConfirmationOption.YES,
            callback_data=AddIncomeCallbackOperation.SELECT_YES,
        ),
    ]

    await CallbackMessages.edit(
        q=contract.q,
        text=text,
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )

    state.next_callback = confirmation_selected_callback
    state.messages_to_delete.add(contract.q.id)


async def source_selected_callback(contract: CallbackQueryContract):
    state = contract.state
    state.check_data("value", "currency", "name")

    source = contract.q.data.replace(
        AddIncomeCallbackOperation.SELECT_SOURCE, ""
    )
    state.data.source = source

    # Prepare dates for the keyboard
    keyboard_patterns: list[CallbackItem] = []

    for date in dates_services.get_last_dates(
        contract.user.configuration.number_of_dates
    ):
        keyboard_patterns.append(
            CallbackItem(
                name=date,
                callback_data="".join(
                    (AddIncomeCallbackOperation.SELECT_DATE, date)
                ),
            )
        )

    await CallbackMessages.edit(
        q=contract.q, text=f"Source selected: {source}"
    )
    message = await Messages.send(
        chat_id=contract.user.chat_id,
        text="📅 Выберите дату",
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )

    state.next_callback = date_selected_callback
    state.messages_to_delete.add(message.id)
    state.messages_to_delete.add(contract.q.id)


async def name_entered_callback(contract: MessageContract):
    state = contract.state
    state.check_data("value", "currency")
    state.data.name = contract.m.text

    # Prepare keyboard with income sources
    keyboard_patterns = [
        CallbackItem(
            name=callback_item.name,
            callback_data=(
                f"{AddIncomeCallbackOperation.SELECT_SOURCE}"
                f"{callback_item.callback_data}"
            ),
        )
        for callback_item in INCOME_SOURCES_KEYBOARD_ELEMENTS
    ]

    message = await Messages.send(
        chat_id=contract.user.chat_id,
        text="🤔 Выберите источник",
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )

    state.next_callback = source_selected_callback
    state.messages_to_delete.add(message.id)
    state.messages_to_delete.add(contract.m.id)


async def currency_selected_callback(contract: CallbackQueryContract):
    state = contract.state
    state.check_data("value")
    currency_id: int = int(
        contract.q.data.replace(AddIncomeCallbackOperation.SELECT_CURRENCY, "")
    )
    currency: CurrencyInDB = await CurrenciesCRUD().get(currency_id)
    state.data.currency = currency

    await CallbackMessages.edit(
        q=contract.q,
        text=f"Выбрана валюта: {currency.name}({currency.sign})",
    )
    message = await Messages.send(
        chat_id=contract.user.chat_id,
        text="⤵️ Введите название и нажмите Enter",
        keyboard=patterns_keyboard(
            contract.user.configuration.incomes_sources_items
        ),
    )

    state.next_callback = name_entered_callback
    state.messages_to_delete.add(message.id)
    state.messages_to_delete.add(contract.q.id)


async def value_entered_callback(contract: MessageContract):
    state = contract.state

    try:
        state.data.value = money_services.validate(contract.m.text)
    except ValidationError:
        state.clear_data()
        raise UserError("⚠️ Значение должно быть корректным числом")

    currencies: list[CurrencyInDB] = await CurrenciesCRUD().all()

    keyboard_patterns = [
        CallbackItem(
            name=f"{currency.name} {currency.sign}",
            callback_data=(
                f"{AddIncomeCallbackOperation.SELECT_CURRENCY}{currency.id}"
            ),
        )
        for currency in currencies
    ]

    repr_value = "".join(
        (money_services.repr_value(state.data.value))
    )
    text = "\n\n".join(
        (
            "\n".join((f"Значение 👉 {repr_value}",)),
            "💱 Выберите валюту",
        )
    )

    message = await Messages.send(
        text=text,
        chat_id=contract.user.chat_id,
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )

    state.messages_to_delete.add(message.id)
    state.messages_to_delete.add(contract.m.id)
    state.next_callback = currency_selected_callback
