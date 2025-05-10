from datetime import date

import pytest

from src.application.states import State
from src.domain.incomes import AddIncomeCallbackOperation
from src.domain.money import CurrenciesCRUD, CurrencyInDB
from src.domain.users import User
from src.handlers.incomes.add import (
    confirmation_selected_callback,
    currency_selected_callback,
    date_selected_callback,
    name_entered_callback,
    source_selected_callback,
    value_entered_callback,
)
from src.infrastructure.database import IncomeSource
from src.infrastructure.errors import DeprecatedMessage, UserError


async def test_value_entered_callback(
    bot_send_message_patch, create_user, create_message_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)

    contract = create_message_contract(user=user, text="12.50")

    await value_entered_callback(contract)

    assert state.data.dict() == {"value": 1250}
    assert state.next_callback == currency_selected_callback
    assert bot_send_message_patch.call_count == 1


async def test_value_entered_callback_fail(
    bot_send_message_patch, create_user, create_message_contract
):
    """Fail if not a valid number was entered."""

    user: User = await create_user("john")
    state: State = State(user.id)
    contract = create_message_contract(user=user, text="invalid number")

    with pytest.raises(UserError):
        await value_entered_callback(contract)

    assert state.data.dict() == {}
    assert state.next_callback is None
    assert bot_send_message_patch.call_count == 0


async def test_currency_selected_callback(
    bot_send_message_patch, create_user, create_callback_query_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)
    state.populate_data({"value": 1200})
    currency: CurrencyInDB = await CurrenciesCRUD().first()
    contract = create_callback_query_contract(
        user=user,
        data=f"{AddIncomeCallbackOperation.SELECT_CURRENCY}{currency.id}",
    )

    await currency_selected_callback(contract)

    assert state.data.dict() == {"value": 1200, "currency": currency}
    assert state.next_callback == name_entered_callback
    assert bot_send_message_patch.call_count == 1


async def test_currency_selected_callback_fail(
    bot_send_message_patch, create_user, create_callback_query_contract
):
    """Fail if value does not exist in the State."""

    user: User = await create_user("john")
    state: State = State(user.id)
    contract = create_callback_query_contract(user=user)

    with pytest.raises(DeprecatedMessage):
        await currency_selected_callback(contract)

    assert state.data.dict() == {}
    assert state.next_callback is None
    assert bot_send_message_patch.call_count == 0


async def test_name_entered_callback(
    bot_send_message_patch, create_user, create_message_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)
    currency = await CurrenciesCRUD().first()
    state.populate_data({"value": 1200, "currency": currency})

    await name_entered_callback(
        create_message_contract(user=user, text="Google")
    )

    assert state.data.dict() == {
        "value": 1200,
        "currency": currency.dict(),
        "name": "Google",
    }
    assert state.next_callback == source_selected_callback
    assert bot_send_message_patch.call_count == 1


@pytest.mark.parametrize("state_payload", [{}, {"value": 1200}])
async def test_name_entered_callback_fail(
    state_payload, bot_send_message_patch, create_user, create_message_contract
):
    """Name can not be entered without full state."""

    user: User = await create_user("john")
    state: State = State(user.id)
    state.populate_data(state_payload)

    with pytest.raises(DeprecatedMessage):
        await name_entered_callback(
            create_message_contract(user=user, text="Google")
        )

    assert state.data.dict() == state_payload
    assert state.next_callback is None
    assert bot_send_message_patch.call_count == 0


async def test_source_selected_callback(
    bot_send_message_patch,
    bot_edit_callback_query_patch,
    create_user,
    create_callback_query_contract,
):
    user: User = await create_user("john")
    state: State = State(user.id)
    currency = await CurrenciesCRUD().first()
    state.populate_data(
        {"value": 1200, "currency": currency, "name": "Google"}
    )

    await source_selected_callback(
        create_callback_query_contract(
            user=user,
            data=(
                f"{AddIncomeCallbackOperation.SELECT_SOURCE}"
                f"{IncomeSource.REVENUE}"
            ),
        )
    )

    assert state.data.dict() == {
        "value": 1200,
        "currency": currency.dict(),
        "name": "Google",
        "source": IncomeSource.REVENUE,
    }
    assert state.next_callback == date_selected_callback
    assert bot_send_message_patch.call_count == 1
    assert bot_edit_callback_query_patch.call_count == 1


@pytest.mark.parametrize(
    "state_payload", [{}, {"value": 1200, "name": "Google"}]
)
async def test_test_source_selected_callback_fail(
    state_payload,
    bot_send_message_patch,
    bot_edit_callback_query_patch,
    create_user,
    create_callback_query_contract,
):
    user: User = await create_user("john")
    state: State = State(user.id)
    state.populate_data(state_payload)

    with pytest.raises(DeprecatedMessage):
        await source_selected_callback(
            create_callback_query_contract(user=user)
        )

    assert state.data.dict() == state_payload
    assert state.next_callback is None
    assert bot_send_message_patch.call_count == 0
    assert bot_edit_callback_query_patch.call_count == 0


async def test_confirmation_selected_callback_yes(
    bot_send_message_patch,
    create_user,
    create_callback_query_contract,
):
    user: User = await create_user("john")
    state: State = State(user.id)
    currency = await CurrenciesCRUD().first()
    value = 1200
    state.populate_data(
        {
            "value": value,
            "currency": currency,
            "name": "Google",
            "source": IncomeSource.REVENUE,
            "date": date.today(),
        }
    )

    await confirmation_selected_callback(
        create_callback_query_contract(
            user=user,
            data=(f"{AddIncomeCallbackOperation.SELECT_YES}"),
        )
    )

    currency = await CurrenciesCRUD().get(id_=currency.id)

    assert bot_send_message_patch.call_count == 1
    assert currency.equity == value


async def test_confirmation_selected_callback_no(
    bot_send_message_patch,
    create_user,
    create_callback_query_contract,
):
    """If not confirmed - the income should not be saved."""

    user: User = await create_user("john")
    state: State = State(user.id)
    currency = await CurrenciesCRUD().first()
    state.populate_data(
        {
            "value": 1200,
            "currency": currency,
            "name": "Google",
            "source": IncomeSource.REVENUE,
            "date": date.today(),
        }
    )

    await confirmation_selected_callback(
        create_callback_query_contract(
            user=user,
            data=(f"{AddIncomeCallbackOperation.SELECT_NO}"),
        )
    )

    currency = await CurrenciesCRUD().get(id_=currency.id)

    assert bot_send_message_patch.call_count == 1
    assert currency.equity == 0
