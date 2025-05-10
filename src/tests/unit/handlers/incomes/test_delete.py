from datetime import date

import pytest

from domain.money.models import CurrencyInDB
from domain.money.repository import CurrenciesCRUD
from src.application.states import State
from src.domain.dates import DateFormat
from src.domain.incomes import DeleteIncomeCallbackOperation, IncomeInDB
from src.handlers.incomes.delete import (
    confirmation_selected_callback,
    income_selected_callback,
    month_selected_callback,
)
from src.infrastructure.errors import DeprecatedMessage, UserError


async def test_month_selected_callback(
    bot_edit_callback_query_patch,
    create_user,
    create_callback_query_contract,
    create_income,
):
    user = await create_user("john")
    await create_income(user.id)
    state = State(user.id)
    month = date.today().strftime(DateFormat.MONTHLY)

    await month_selected_callback(
        create_callback_query_contract(
            user, data=f"{DeleteIncomeCallbackOperation.SELECT_MONTH}{month}"
        )
    )

    assert state.data.dict() == {"month": month}
    assert bot_edit_callback_query_patch.call_count == 1
    assert state.next_callback == income_selected_callback


async def test_month_selected_callback_fail(
    bot_edit_callback_query_patch, create_user, create_callback_query_contract
):
    """The month selection should fail if incomes
    do not exist in the database."""

    user = await create_user("john")
    state = State(user.id)
    month = date.today().strftime(DateFormat.MONTHLY)

    with pytest.raises(UserError):
        await month_selected_callback(
            create_callback_query_contract(user, data=month)
        )

    assert state.data.dict() == {}
    assert bot_edit_callback_query_patch.call_count == 0
    assert state.next_callback is None


async def test_income_selected_callback(
    bot_edit_callback_query_patch,
    create_user,
    create_callback_query_contract,
    create_income,
):
    user = await create_user("john")
    income: IncomeInDB = await create_income(user.id)
    state = State(user.id)
    month = date.today().strftime(DateFormat.MONTHLY)
    state.populate_data({"month": month})

    await income_selected_callback(
        create_callback_query_contract(
            user,
            data=f"{DeleteIncomeCallbackOperation.SELECT_INCOME}{income.id}",
        )
    )

    assert state.data.dict() == {"month": month, "income_id": income.id}
    assert bot_edit_callback_query_patch.call_count == 1
    assert state.next_callback == confirmation_selected_callback


async def test_income_selected_callback_fail(
    bot_edit_callback_query_patch, create_user, create_callback_query_contract
):
    """If State is not complete the income selection can not be used."""
    user = await create_user("john")
    state = State(user.id)

    with pytest.raises(DeprecatedMessage):
        await income_selected_callback(create_callback_query_contract(user))

    assert state.data.dict() == {}
    assert bot_edit_callback_query_patch.call_count == 0
    assert state.next_callback is None


async def test_confirmation_selected_callback_yes(
    bot_send_message_patch,
    create_user,
    create_callback_query_contract,
    create_income,
):
    """After user's confirmation the income should be deleted
    and the equity should be decreased."""

    user = await create_user("john")
    income: IncomeInDB = await create_income(user.id)
    state = State(user.id)
    state.populate_data({"income_id": income.id})

    await confirmation_selected_callback(
        create_callback_query_contract(
            user,
            data=(f"{DeleteIncomeCallbackOperation.SELECT_YES}"),
        )
    )

    currency: CurrencyInDB = await CurrenciesCRUD().get(income.currency_id)

    assert bot_send_message_patch.call_count == 1
    assert currency.equity == -income.value
    assert state.next_callback is None


async def test_confirmation_selected_callback_no(
    bot_send_message_patch,
    create_user,
    create_callback_query_contract,
    create_income,
):
    """After user's confirmation the income should be deleted
    and the equity should be decreased."""

    user = await create_user("john")
    income: IncomeInDB = await create_income(user.id)
    state = State(user.id)
    state.populate_data({"income_id": income.id})

    await confirmation_selected_callback(
        create_callback_query_contract(
            user,
            data=(f"{DeleteIncomeCallbackOperation.SELECT_NO}"),
        )
    )

    currency: CurrencyInDB = await CurrenciesCRUD().get(income.currency_id)

    assert bot_send_message_patch.call_count == 1
    assert currency.equity == 0
    assert state.next_callback is None
