from datetime import datetime

from src.application.database import transaction
from src.application.messages import (
    CallbackMessages,
    CallbackQueryContract,
    MessageContract,
    Messages,
)
from src.domain.categories import CategoriesCRUD, CategoryInDB
from src.domain.categories import services as categories_services
from src.domain.costs import AddCostCallbackOperation, Cost, CostUncommited
from src.domain.costs import services as costs_services
from src.domain.dates import DateFormat
from src.domain.dates import services as dates_services
from src.domain.money import services as money_services
from src.infrastructure.errors import UserError, ValidationError
from src.keyboards.constants import ConfirmationOption
from src.keyboards.default import default_keyboard, restart_keyboard
from src.keyboards.models import CallbackItem
from src.keyboards.patterns import (
    callback_patterns_keyboard,
    patterns_keyboard,
)


@transaction
async def confirmation_selected_callback_query(
    contract: CallbackQueryContract,
):
    state = contract.state
    state.messages_to_delete.add(contract.q.id)

    match contract.q.data:
        case AddCostCallbackOperation.SELECT_YES:
            state.check_data("value", "name", "date", "category")
            schema = CostUncommited(
                name=state.data.name,
                value=state.data.value,
                date=state.data.date,
                category_id=state.data.category.id,
                currency_id=contract.user.configuration.default_currency.id,
                user_id=contract.user.id,
            )

            cost: Cost = await costs_services.add(schema)
            text = "\n\n".join(("✅ Расход успешно сохранён", cost.repr()))

        case AddCostCallbackOperation.SELECT_NO:
            text = "❌ Расход не был сохранён"
        case _:
            raise ValidationError("Что-то пошло не так.\Пожалуйста, попробуйте ещё раз 🏋️")

    await Messages.send(
        contract.user.chat_id, text=text, keyboard=default_keyboard()
    )

    await Messages.delete(contract.user.chat_id, *state.messages_to_delete)
    state.clear_data()


async def date_selected_callback_query(
    contract: CallbackQueryContract,
):
    state = contract.state
    state.check_data("value", "name", "category")
    date_raw = contract.q.data.replace(
        AddCostCallbackOperation.SELECT_DATE, ""
    )
    state.data.date = datetime.strptime(date_raw, DateFormat.FULL).date()
    state.next_callback = confirmation_selected_callback_query

    repr_value = "".join(
        (
            money_services.repr_value(state.data.value),
            contract.user.configuration.default_currency.sign,
        )
    )
    text = "\n\n".join(
        (
            "\n".join(
                (
                    f"Название 👉 {state.data.name}",
                    f"Значение 👉 {repr_value}",
                    f"Категория 👉 {state.data.category.name}",
                    f"Дата 👉 {state.data.date}",
                )
            ),
            "Вы хотите сохранить расходы?",
        )
    )

    keyboard_patterns: list[CallbackItem] = [
        CallbackItem(
            name=ConfirmationOption.NO,
            callback_data=AddCostCallbackOperation.SELECT_NO,
        ),
        CallbackItem(
            name=ConfirmationOption.YES,
            callback_data=AddCostCallbackOperation.SELECT_YES,
        ),
    ]

    await CallbackMessages.edit(
        q=contract.q,
        text=text,
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )


async def category_selected_callback_query(
    contract: CallbackQueryContract,
):
    state = contract.state
    state.messages_to_delete.add(contract.q.id)
    state.check_data("value", "name")
    category_id: int = int(
        contract.q.data.replace(AddCostCallbackOperation.SELECT_CATEGORY, "")
    )

    category: CategoryInDB = await CategoriesCRUD().get(id_=category_id)
    state.data.category = category
    state.next_callback = date_selected_callback_query

    repr_value = "".join(
        (
            money_services.repr_value(state.data.value),  # type: ignore
            contract.user.configuration.default_currency.sign,
        )
    )
    text = "\n\n".join(
        (
            "\n".join(
                (
                    f"Название 👉 {state.data.name}",  # type: ignore
                    f"Значение 👉 {repr_value}",
                    f"Категория 👉 {state.data.category.name}",  # type: ignore
                )
            ),
            "📅 Выберите дату",
        )
    )

    keyboard_patterns: list[CallbackItem] = []

    for date in dates_services.get_last_dates(
        contract.user.configuration.number_of_dates
    ):
        keyboard_patterns.append(
            CallbackItem(
                name=date,
                callback_data="".join(
                    (AddCostCallbackOperation.SELECT_DATE, date)
                ),
            )
        )

    await CallbackMessages.edit(
        q=contract.q,
        text=text,
        keyboard=callback_patterns_keyboard(keyboard_patterns, width=1),
    )


async def name_entered_callback(contract: MessageContract):
    state = contract.state
    state.check_data("value")
    state.data.name = contract.m.text
    state.messages_to_delete.add(contract.m.id)
    state.next_callback = category_selected_callback_query

    keyboard_patterns: list[CallbackItem] = []
    for category in await categories_services.filter_by_ids(
        contract.user.configuration.ignore_categories_items
    ):
        _callback_data = "".join(
            (AddCostCallbackOperation.SELECT_CATEGORY, str(category.id))
        )
        keyboard_patterns.append(
            CallbackItem(name=category.name, callback_data=_callback_data)
        )

    repr_value = "".join(
        (
            money_services.repr_value(state.data.value),  # type: ignore
            contract.user.configuration.default_currency.sign,
        )
    )
    text = "\n\n".join(
        (
            "\n".join(
                (
                    f"Название 👉 {state.data.name}",  # type: ignore
                    f"Значение 👉 {repr_value}",
                )
            ),
            "🤔 Выберите категорию",
        )
    )

    message = await Messages.send(
        text=text,
        chat_id=contract.user.chat_id,
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )
    state.messages_to_delete.add(contract.m.id)
    state.messages_to_delete.add(message.id)


async def value_entered_callback(contract: MessageContract):
    state = contract.state
    try:
        state.data.value = money_services.validate(contract.m.text)
    except ValidationError:
        raise UserError("⚠️ Значение должно быть корректным значением")

    state.next_callback = name_entered_callback

    message = await Messages.send(
        text="⤵️ Введите название и нажмите Enter",
        chat_id=contract.user.chat_id,
        keyboard=patterns_keyboard(
            contract.user.configuration.costs_sources_items
        ),
    )
    state.messages_to_delete.add(message.id)
    state.messages_to_delete.add(contract.m.id)


async def add_cost_callback(contract: MessageContract):
    state = contract.state
    state.clear_data()
    state.next_callback = value_entered_callback
    text = "⤵️ Введите значение и нажмите Enter"

    message = await Messages.send(
        chat_id=contract.user.chat_id,
        text=text,
        keyboard=restart_keyboard(),
    )
    state.messages_to_delete.add(contract.m.id)
    state.messages_to_delete.add(message.id)
