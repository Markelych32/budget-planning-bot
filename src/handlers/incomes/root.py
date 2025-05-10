from src.application.messages import (
    CallbackMessages,
    CallbackQueryContract,
    MessageContract,
    Messages,
)
from src.domain.incomes import DeleteIncomeCallbackOperation, IncomeRootOption
from src.domain.incomes import services as incomes_services
from src.handlers.incomes.add import value_entered_callback
from src.handlers.incomes.delete import month_selected_callback
from src.infrastructure.errors import NotFound, UserError
from src.keyboards.default import default_keyboard
from src.keyboards.models import CallbackItem
from src.keyboards.patterns import callback_patterns_keyboard

__all__ = ("incomes_general_menu_callback", "income_action_selected_callback")


async def income_action_selected_callback(contract: CallbackQueryContract):
    state = contract.state

    match contract.q.data:
        case IncomeRootOption.ADD_INCOME:
            state.next_callback = value_entered_callback
            text = "⤵️ Введите значение и нажмите Enter"
            change_text = "Выбран раздел доходов"
            keyboard = default_keyboard()
        case IncomeRootOption.DELETE_INCOME:
            text = "📅 Выберите месяц"
            change_text = "Выбрана опция удаления дохода"

            keyboard_patterns: list[CallbackItem] = []
            try:
                async for month in incomes_services.get_last_months(
                    contract.user.configuration.number_of_dates
                ):
                    callback_data = "".join(
                        (DeleteIncomeCallbackOperation.SELECT_MONTH, month)
                    )
                    keyboard_patterns.append(
                        CallbackItem(name=month, callback_data=callback_data),
                    )
            except NotFound:
                raise UserError(message="😢 В этом месяце доходов нет")

            keyboard = callback_patterns_keyboard(keyboard_patterns)
            state.next_callback = month_selected_callback
        case _:
            raise ValueError("Некорректный ввод для раздела доходов")

    await CallbackMessages.edit(q=contract.q, text=change_text)
    message = await Messages.send(
        chat_id=contract.user.chat_id, text=text, keyboard=keyboard
    )

    state.messages_to_delete.add(message.id)


async def incomes_general_menu_callback(contract: MessageContract):
    state = contract.state
    state.clear_data()
    state.next_callback = income_action_selected_callback

    keyboard = callback_patterns_keyboard(
        [
            CallbackItem(
                name="🔥 Удалить", callback_data=IncomeRootOption.DELETE_INCOME
            ),
            CallbackItem(
                name="💹 Добавить", callback_data=IncomeRootOption.ADD_INCOME
            ),
        ]
    )

    message = await Messages.send(
        chat_id=contract.user.chat_id,
        text="🤔 Выберите следующую опцию",
        keyboard=keyboard,
    )

    state.messages_to_delete.add(contract.m.id)
    state.messages_to_delete.add(message.id)
