from typing import AsyncGenerator

from loguru import logger

from src.application.database import transaction
from src.application.messages import (
    CallbackMessages,
    CallbackQueryContract,
    MessageContract,
    Messages,
)
from src.domain.categories import CategoriesCRUD, CategoryInDB
from src.domain.categories import services as categories_services
from src.domain.costs import Cost, CostsCRUD, DeleteCostCallbackOperation
from src.domain.costs import services as costs_services
from src.domain.dates import DateFormat
from src.domain.money import services as money_services
from src.infrastructure.errors import NotFound, UserError
from src.keyboards.constants import ConfirmationOption
from src.keyboards.default import default_keyboard
from src.keyboards.models import CallbackItem
from src.keyboards.patterns import callback_patterns_keyboard


@transaction
async def confirmation_selected_callback(contract: CallbackQueryContract):
    contract.state.check_data("cost_id")
    cost: Cost = await CostsCRUD().get(
        id_=contract.state.data.cost_id,  # type: ignore
    )

    match contract.q.data:
        case DeleteCostCallbackOperation.SELECT_YES:
            await costs_services.delete(cost)
            text = "🔥 Расход успешно удалён"
        case DeleteCostCallbackOperation.SELECT_NO:
            text = "💁 Расход не был удалён"
        case _:
            logger.error(
                "Delete cost confirmation contract payload unrecognized."
            )
            raise Exception

    await Messages.send(
        chat_id=contract.user.chat_id,
        text=text,
        keyboard=default_keyboard(),
    )
    await Messages.delete(
        contract.user.chat_id, *contract.state.messages_to_delete
    )
    contract.state.clear_data()


async def cost_selected_callback(contract: CallbackQueryContract):
    contract.state.data.cost_id = int(
        contract.q.data.replace(DeleteCostCallbackOperation.SELECT_COST, "")
    )
    contract.state.next_callback = confirmation_selected_callback

    keyboard_patterns: list[CallbackItem] = [
        CallbackItem(
            name=ConfirmationOption.NO,
            callback_data=DeleteCostCallbackOperation.SELECT_NO,
        ),
        CallbackItem(
            name=ConfirmationOption.YES,
            callback_data=DeleteCostCallbackOperation.SELECT_YES,
        ),
    ]

    await CallbackMessages.edit(
        q=contract.q,
        text="Вы действительно хотите удалить расход?",
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )


async def category_selected_callback(contract: CallbackQueryContract):
    contract.state.check_data("month")

    category_id: int = int(
        contract.q.data.replace(
            DeleteCostCallbackOperation.SELECT_CATEGORY, ""
        )
    )
    category: CategoryInDB = await CategoriesCRUD().get(category_id)

    contract.state.data.category = category
    contract.state.next_callback = cost_selected_callback

    keyboard_patterns = []
    costs: AsyncGenerator[Cost, None] = CostsCRUD().filter_for_delete(
        month=contract.state.data.month,  # type: ignore
        category_id=category_id,
    )
    async for cost in costs:
        cost_repr = (
            f"({cost.date.strftime(DateFormat.DAILY)}) {cost.name}: "
            f"{money_services.repr_value(cost.value)}{cost.currency.sign}"
        )
        keyboard_patterns.append(
            CallbackItem(
                name=cost_repr,
                callback_data="".join(
                    (DeleteCostCallbackOperation.SELECT_COST, str(cost.id))
                ),
            )
        )

    if not keyboard_patterns:
        await Messages.delete(
            contract.user.chat_id, *contract.state.messages_to_delete
        )
        raise UserError("💪 Расходов нет")

    await CallbackMessages.edit(
        contract.q,
        text="🤔 Выберите расход",
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )


async def month_selected_callback(contract: CallbackQueryContract):
    contract.state.next_callback = category_selected_callback
    contract.state.data.month = contract.q.data.replace(
        DeleteCostCallbackOperation.SELECT_MONTH, ""
    )

    keyboard_patterns: list[CallbackItem] = []
    for category in await categories_services.get_all():
        _callback_data = "".join(
            (DeleteCostCallbackOperation.SELECT_CATEGORY, str(category.id))
        )
        keyboard_patterns.append(
            CallbackItem(name=category.name, callback_data=_callback_data)
        )

    await CallbackMessages.edit(
        q=contract.q,
        text="🤔 Выберите категорию",
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )


async def delete_cost_callback(contract: MessageContract):
    keyboard_patterns: list[CallbackItem] = []

    try:
        async for month in costs_services.get_last_months(
            contract.user.configuration.number_of_dates
        ):
            keyboard_patterns.append(
                CallbackItem(
                    name=month,
                    callback_data="".join(
                        (DeleteCostCallbackOperation.SELECT_MONTH, month)
                    ),
                ),
            )
    except NotFound:
        raise UserError(
            message=(
                "✨ В течение прошлого месяца не было расходов.\n"
                "Вы можете увеличить диапазон в настройках"
            )
        )

    state = contract.state
    state.next_callback = month_selected_callback
    text = "📅 Выберите месяц"

    message = await Messages.send(
        chat_id=contract.user.chat_id,
        text=text,
        keyboard=callback_patterns_keyboard(keyboard_patterns, width=1),
    )

    state.messages_to_delete.add(contract.m.id)
    state.messages_to_delete.add(message.id)
