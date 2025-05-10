from datetime import date

import pytest
from telebot import types

from src.application.states import State
from src.domain.categories import CategoriesCRUD, CategoryInDB
from src.domain.costs import CostInDB, CostsCRUD, DeleteCostCallbackOperation
from src.domain.dates import DateFormat
from src.domain.money import CurrenciesCRUD, CurrencyInDB
from src.domain.users import User
from src.handlers.delete_cost import (
    category_selected_callback,
    confirmation_selected_callback,
    cost_selected_callback,
    delete_cost_callback,
    month_selected_callback,
)
from src.handlers.router import any_message
from src.infrastructure.errors import DeprecatedMessage, UserError
from src.keyboards.default import Menu


async def test_anonymous_trigger_delete_cost(
    bot_send_message_patch, create_message
):
    message: types.Message = create_message(Menu.DELETE_COST)

    await any_message(message)

    assert bot_send_message_patch.call_count == 1


async def test_trigger_delete_cost(
    create_cost, bot_send_message_patch, create_message, create_user
):
    message: types.Message = create_message(Menu.DELETE_COST)
    user: User = await create_user("john")
    state: State = State(user.id)
    await create_cost(user.id)

    await any_message(message)

    assert bot_send_message_patch.call_count == 1
    assert state.next_callback == month_selected_callback


async def test_delete_cost_callback(
    bot_send_message_patch, create_user, create_cost, create_message_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)
    contract = create_message_contract(user=user)
    await create_cost(user_id=user.id)

    await delete_cost_callback(contract)

    assert bot_send_message_patch.call_count == 1
    assert state.next_callback == month_selected_callback


async def test_delete_cost_callback_fail(
    bot_send_message_patch, create_user, create_message_contract
):
    """If there are no costs, incomes or exchange rates
    the callback should fail"""

    user: User = await create_user("john")
    state: State = State(user.id)
    contract = create_message_contract(user=user)

    with pytest.raises(UserError):
        await delete_cost_callback(contract)

    assert bot_send_message_patch.call_count == 0
    assert state.next_callback is None
    assert state.data.dict() == {}


async def test_month_selected_callback(
    bot_edit_callback_query_patch, create_user, create_callback_query_contract
):
    user = await create_user("john")
    state = State(user.id)
    current_month: str = date.today().strftime(DateFormat.MONTHLY)
    contract = create_callback_query_contract(
        user=user,
        data=f"{DeleteCostCallbackOperation.SELECT_MONTH}{current_month}",
    )

    await month_selected_callback(contract)

    assert state.next_callback == category_selected_callback
    assert bot_edit_callback_query_patch.call_count == 1
    assert state.data.dict() == {"month": current_month}


async def test_category_selected_callback(
    bot_edit_callback_query_patch, create_user, create_callback_query_contract
):
    user = await create_user("john")
    state = State(user.id)
    current_month = date.today().strftime(DateFormat.MONTHLY)
    state.populate_data({"month": current_month})
    category: CategoryInDB = await CategoriesCRUD().get(id_=1)
    contract = create_callback_query_contract(
        user=user,
        data=f"{DeleteCostCallbackOperation.SELECT_CATEGORY}{category.id}",
    )

    with pytest.raises(UserError):
        await category_selected_callback(contract)

    assert state.next_callback == cost_selected_callback
    assert bot_edit_callback_query_patch.call_count == 0
    assert state.data.dict() == {
        "month": current_month,
        "category": category.dict(),
    }


async def test_category_selected_callback_fail(
    bot_edit_callback_query_patch, create_user, create_callback_query_contract
):
    """If the month is not set the category can not be selected."""

    user = await create_user("john")
    state = State(user.id)
    contract = create_callback_query_contract(
        user=user, data=f"{DeleteCostCallbackOperation.SELECT_CATEGORY}1"
    )

    with pytest.raises(DeprecatedMessage):
        await category_selected_callback(contract)

    assert state.next_callback is None
    assert bot_edit_callback_query_patch.call_count == 0
    assert state.data.dict() == {}


async def test_cost_selected_callback(
    bot_edit_callback_query_patch,
    create_user,
    create_cost,
    create_callback_query_contract,
):
    user = await create_user("john")
    state = State(user.id)
    cost: CostInDB = await create_cost(user.id)
    contract = create_callback_query_contract(
        user=user, data=f"{DeleteCostCallbackOperation.SELECT_COST}{cost.id}"
    )

    await cost_selected_callback(contract)

    assert state.next_callback is confirmation_selected_callback
    assert bot_edit_callback_query_patch.call_count == 1


async def test_confirmation_selected_callback_yes(
    bot_send_message_patch,
    create_user,
    create_cost,
    create_callback_query_contract,
):
    """If Yes is selected the cost should not exist in the database and
    the equity should be changed."""

    user = await create_user("john")
    state = State(user.id)
    state.populate_data({"cost_id": 1})
    cost = await create_cost(user_id=user.id)

    await confirmation_selected_callback(
        create_callback_query_contract(
            user, data=f"{DeleteCostCallbackOperation.SELECT_YES}"
        )
    )

    costs_amount = await CostsCRUD().count()
    currency: CurrencyInDB = await CurrenciesCRUD().get(id_=1)

    assert bot_send_message_patch.call_count == 1
    assert costs_amount == 0
    assert currency.equity == cost.value


async def test_confirmation_selected_callback_no(
    bot_send_message_patch,
    create_user,
    create_cost,
    create_callback_query_contract,
):
    """If No is selected the cost should exist in the database and
    the equity should not be changed."""

    user = await create_user("john")
    state = State(user.id)
    state.populate_data({"cost_id": 1})
    await create_cost(user_id=user.id)

    await confirmation_selected_callback(
        create_callback_query_contract(
            user, data=f"{DeleteCostCallbackOperation.SELECT_NO}"
        )
    )

    costs_amount = await CostsCRUD().count()
    currency: CurrencyInDB = await CurrenciesCRUD().get(id_=1)

    assert bot_send_message_patch.call_count == 1
    assert costs_amount == 1
    assert currency.equity == 0
