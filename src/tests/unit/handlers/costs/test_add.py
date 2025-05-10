from datetime import datetime

import pytest

from src.application.states import State
from src.domain.categories import CategoriesCRUD, CategoryInDB
from src.domain.costs import AddCostCallbackOperation, CostsCRUD
from src.domain.dates import DateFormat
from src.domain.money import CurrenciesCRUD, CurrencyInDB
from src.domain.users import User
from src.handlers.add_cost import (
    category_selected_callback_query,
    confirmation_selected_callback_query,
    date_selected_callback_query,
    name_entered_callback,
    value_entered_callback,
)
from src.handlers.router import any_message
from src.infrastructure.errors import (
    DatabaseError,
    DeprecatedMessage,
    UserError,
)
from src.keyboards.default import Menu


async def test_anonymous_trigger_add_cost(
    mocker, bot_send_message_patch, create_message
):
    add_cost_service = mocker.patch("src.domain.costs.services.add")

    await any_message(create_message(Menu.ADD_COST))

    assert bot_send_message_patch.call_count == 1
    assert add_cost_service.call_count == 0


async def test_trigger_add_cost(
    bot_send_message_patch, create_message, create_user
):
    """Check the expected flow for triggering the /start command."""

    user: User = await create_user("john")
    state: State = State(user.id)

    await any_message(create_message(Menu.ADD_COST))

    assert bot_send_message_patch.call_count == 1
    assert state.next_callback == value_entered_callback


@pytest.mark.parametrize("input_data", ["12", "12.0", "12,00"])
async def test_value_entered_callback(
    input_data, bot_send_message_patch, create_user, create_message_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)
    contract = create_message_contract(user=user, text=input_data)

    await value_entered_callback(contract)

    assert bot_send_message_patch.call_count == 1
    assert state.next_callback == name_entered_callback
    assert state.data.dict() == {"value": 1200}


async def test_value_entered_callback_invalid(
    bot_send_message_patch, create_user, create_message_contract
):
    """The callback should fail if the input value is not a numeric."""
    user: User = await create_user("john")
    state: State = State(user.id)
    contract = create_message_contract(user=user, text="Not a number")

    with pytest.raises(UserError):
        await value_entered_callback(contract)

    assert bot_send_message_patch.call_count == 0
    assert state.next_callback is None
    assert state.data == {}


async def test_name_entered_callback(
    bot_send_message_patch, create_user, create_message_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)
    state.data.value = 1200
    contract = create_message_contract(user=user, text="Water")

    await name_entered_callback(contract)

    assert bot_send_message_patch.call_count == 1
    assert state.next_callback == category_selected_callback_query
    assert state.data.dict() == {"name": "Water", "value": 1200}


async def test_name_entered_callback_invalid_state(
    bot_send_message_patch,
    create_user,
    create_message_contract,
):
    """In order to proceed with name the value must exist in the state."""

    user: User = await create_user("john")
    state: State = State(user.id)
    contract = create_message_contract(user=user, text="Water")

    with pytest.raises(DeprecatedMessage):
        await name_entered_callback(contract)

    assert bot_send_message_patch.call_count == 0
    assert state.next_callback is None
    assert state.data.dict() == {}


async def test_category_selected_callback_query(
    bot_edit_callback_query_patch, create_user, create_callback_query_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)
    state.populate_data({"value": 1200, "name": "Water"})
    category: CategoryInDB = await CategoriesCRUD().get(id_=2)
    contract = create_callback_query_contract(
        user=user,
        data=f"{AddCostCallbackOperation.SELECT_CATEGORY}{category.id}",
    )

    await category_selected_callback_query(contract)

    assert bot_edit_callback_query_patch.call_count == 1
    assert state.next_callback == date_selected_callback_query
    assert state.data.dict() == {
        "value": 1200,
        "name": "Water",
        "category": category.dict(),
    }


@pytest.mark.parametrize(
    "state_payload",
    [
        {"name": "Water"},
        {"value": 1200},
    ],
)
async def test_category_selected_callback_query_invalid_state(
    state_payload,
    bot_edit_callback_query_patch,
    create_user,
    create_callback_query_contract,
):
    user: User = await create_user("john")
    state: State = State(user.id)
    state.populate_data(state_payload)
    category: CategoryInDB = await CategoriesCRUD().get(id_=2)
    contract = create_callback_query_contract(
        user=user,
        data=f"{AddCostCallbackOperation.SELECT_CATEGORY}{category.id}",
    )

    with pytest.raises(DeprecatedMessage):
        await category_selected_callback_query(contract)

    assert bot_edit_callback_query_patch.call_count == 0
    assert state.next_callback is None
    assert state.data.dict() == state_payload


async def test_date_selected_callback_query(
    bot_edit_callback_query_patch, create_user, create_callback_query_contract
):
    today = datetime.today().date()
    user: User = await create_user("john")
    category: CategoryInDB = await CategoriesCRUD().get(id_=2)
    state: State = State(user.id)
    state.populate_data(
        payload={
            "value": 1200,
            "name": "Water",
            "category": category,
            "date": today,
        }
    )
    contract = create_callback_query_contract(
        user=user,
        data=f"{AddCostCallbackOperation.SELECT_DATE}{today.strftime(DateFormat.FULL)}",
    )

    await date_selected_callback_query(contract)

    assert bot_edit_callback_query_patch.call_count == 1
    assert state.next_callback == confirmation_selected_callback_query
    assert state.data.dict() == {
        "value": 1200,
        "name": "Water",
        "category": category.dict(),
        "date": today,
    }


@pytest.mark.parametrize(
    "state_payload",
    [
        {
            "value": 1200,
            "name": "Water",
        },
        {"value": 1200},
        {"name": "Water"},
    ],
)
async def test_date_selected_callback_query_invalid_state(
    state_payload: dict,
    bot_edit_callback_query_patch,
    create_user,
    create_callback_query_contract,
):
    today = datetime.today().date()
    user: User = await create_user("john")
    state: State = State(user.id)
    state.populate_data(payload=state_payload)
    contract = create_callback_query_contract(
        user=user,
        data=f"{AddCostCallbackOperation.SELECT_DATE}{today.strftime(DateFormat.FULL)}",
    )

    with pytest.raises(DeprecatedMessage):
        await date_selected_callback_query(contract)

    assert bot_edit_callback_query_patch.call_count == 0
    assert state.next_callback is None
    assert state.data.dict() == state_payload


async def test_confirmation_selected_callback_query(
    bot_send_message_patch, create_user, create_callback_query_contract
):
    today = datetime.today().date()
    user: User = await create_user("john")
    category: CategoryInDB = await CategoriesCRUD().get(id_=2)
    state: State = State(user.id)
    payload = {
        "value": 1200,
        "name": "Water",
        "category": category,
        "date": today,
    }

    state.populate_data(payload)
    contract = create_callback_query_contract(
        user=user, data=f"{AddCostCallbackOperation.SELECT_YES}"
    )

    await confirmation_selected_callback_query(contract)

    costs_amount: int = await CostsCRUD().count()
    currency: CurrencyInDB = await CurrenciesCRUD().get(id_=1)

    assert bot_send_message_patch.call_count == 1
    assert costs_amount == 1
    assert currency.equity == -payload["value"]


async def test_confirmation_selected_callback_query_transaction_fail(
    mocker,
    bot_delete_message_patch,
    bot_edit_callback_query_patch,
    create_user,
    create_callback_query_contract,
):
    """The cost should be rolled back if the equity can not be changed."""

    today = datetime.today().date()
    user: User = await create_user("john")
    category: CategoryInDB = await CategoriesCRUD().get(id_=2)
    state: State = State(user.id)
    state.populate_data(
        payload={
            "value": 1200,
            "name": "Water",
            "category": category,
            "date": today,
        }
    )
    contract = create_callback_query_contract(
        user=user, data=f"{AddCostCallbackOperation.SELECT_YES}"
    )
    mocker.patch(
        "src.domain.costs.services.CurrenciesCRUD.decrease_equity",
        side_effect=DatabaseError,
    )

    with pytest.raises(DatabaseError):
        await confirmation_selected_callback_query(contract)

    costs_amount: int = await CostsCRUD().count()

    assert bot_edit_callback_query_patch.call_count == 0
    assert bot_delete_message_patch.call_count == 1
    assert costs_amount == 0
