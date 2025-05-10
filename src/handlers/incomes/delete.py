from loguru import logger

from src.application.database import transaction
from src.application.messages import (
    CallbackMessages,
    CallbackQueryContract,
    Messages,
)
from src.domain.incomes import (
    DeleteIncomeCallbackOperation,
    Income,
    IncomesCRUD,
)
from src.domain.incomes import services as incomes_services
from src.domain.money import services as money_services
from src.infrastructure.errors import UserError
from src.keyboards.constants import ConfirmationOption
from src.keyboards.default import default_keyboard
from src.keyboards.models import CallbackItem
from src.keyboards.patterns import callback_patterns_keyboard


@transaction
async def confirmation_selected_callback(
    contract: CallbackQueryContract,
):
    state = contract.state
    state.check_data("income_id")
    income: Income = await IncomesCRUD().get(
        id_=contract.state.data.income_id,  # type: ignore
    )

    match contract.q.data:
        case DeleteIncomeCallbackOperation.SELECT_YES:
            await incomes_services.delete(income)
            text = "🔥 Доход удалён"
        case DeleteIncomeCallbackOperation.SELECT_NO:
            text = "💁 Доход не был удалён"
        case _:
            logger.error(
                "Delete income confirmation contract payload unrecognized."
            )
            state.clear_data()
            state.next_callback = None
            raise Exception

    await Messages.send(
        chat_id=contract.user.chat_id,
        text=text,
        keyboard=default_keyboard(),
    )
    await Messages.delete(
        contract.user.chat_id, *contract.state.messages_to_delete
    )
    state.clear_data()
    state.next_callback = None


async def income_selected_callback(contract: CallbackQueryContract):
    state = contract.state
    state.check_data("month")
    state.data.income_id = int(
        contract.q.data.replace(
            DeleteIncomeCallbackOperation.SELECT_INCOME, ""
        )
    )
    keyboard_patterns: list[CallbackItem] = [
        CallbackItem(
            name=ConfirmationOption.NO,
            callback_data=DeleteIncomeCallbackOperation.SELECT_NO,
        ),
        CallbackItem(
            name=ConfirmationOption.YES,
            callback_data=DeleteIncomeCallbackOperation.SELECT_YES,
        ),
    ]

    await CallbackMessages.edit(
        q=contract.q,
        text="Вы действительно хотите удалить доход?",
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )

    state.next_callback = confirmation_selected_callback


async def month_selected_callback(contract: CallbackQueryContract):
    state = contract.state
    month = contract.q.data.replace(
        DeleteIncomeCallbackOperation.SELECT_MONTH, ""
    )

    keyboard_patterns = []
    async for income in IncomesCRUD().filter_for_delete(month):
        _income_repr = (
            f"{income.name}: "
            f"{money_services.repr_value(income.value)}{income.currency.sign} "
            f"({income.date.strftime('%m-%d')})"
        )
        _callback_data = "".join(
            (DeleteIncomeCallbackOperation.SELECT_INCOME, str(income.id))
        )
        keyboard_patterns.append(
            CallbackItem(name=_income_repr, callback_data=_callback_data)
        )

    if not keyboard_patterns:
        await Messages.delete(
            contract.user.chat_id, *contract.state.messages_to_delete
        )
        state.clear_data()
        raise UserError("😢 Доходов нет")

    await CallbackMessages.edit(
        contract.q,
        text="🤔 Выберите доход",
        keyboard=callback_patterns_keyboard(keyboard_patterns),
    )

    state.data.month = month
    state.next_callback = income_selected_callback
