from src.application.states import State
from src.domain.incomes import IncomeRootOption
from src.domain.users import User
from src.handlers.incomes.add import value_entered_callback
from src.handlers.incomes.delete import month_selected_callback
from src.handlers.incomes.root import income_action_selected_callback
from src.handlers.router import any_message
from src.keyboards.default import Menu


async def test_anonymous_trigger_incomes(
    bot_send_message_patch, create_message
):
    await any_message(create_message(Menu.INCOMES))

    assert bot_send_message_patch.call_count == 1


async def test_trigger_incomes(
    create_cost, bot_send_message_patch, create_message, create_user
):
    user: User = await create_user("john")
    state: State = State(user.id)
    await create_cost(user.id)

    await any_message(create_message(Menu.INCOMES))

    assert bot_send_message_patch.call_count == 1
    assert state.next_callback == income_action_selected_callback


async def test_action_selected_add(
    bot_send_message_patch, create_user, create_callback_query_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)
    contract = create_callback_query_contract(
        user=user, data=f"{IncomeRootOption.ADD_INCOME}"
    )

    await income_action_selected_callback(contract)

    assert state.next_callback == value_entered_callback
    assert bot_send_message_patch.call_count == 1


async def test_action_selected_delete(
    bot_send_message_patch,
    create_user,
    create_callback_query_contract,
    create_income,
):
    user: User = await create_user("john")
    state: State = State(user.id)
    await create_income(user.id)

    contract = create_callback_query_contract(
        user=user, data=f"{IncomeRootOption.DELETE_INCOME}"
    )

    await income_action_selected_callback(contract)

    assert state.next_callback == month_selected_callback
    assert bot_send_message_patch.call_count == 1
