from datetime import date

from src.application.states import State
from src.domain.currency_exchange import (
    CurrencyExchangeCallbackOperation,
    CurrencyExchangeCRUD,
)
from src.domain.dates import DateFormat
from src.domain.money import CurrenciesCRUD, CurrencyInDB
from src.domain.users import User
from src.handlers.currency_exchange import (
    confirmation_entered_callback,
    currency_exchange_callback,
    date_selected_callback,
    destination_currency_entered_callback,
    destination_value_entered_callback,
    source_currency_entered_callback,
    source_value_entered_callback,
)


async def test_currency_exchange_callback(
    bot_send_message_patch, create_user, create_message_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)

    await currency_exchange_callback(create_message_contract(user=user))

    assert state.next_callback == source_currency_entered_callback
    assert bot_send_message_patch.call_count == 1


async def test_source_currency_entered_callback(
    bot_edit_callback_query_patch, create_user, create_callback_query_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)
    source_currency: CurrencyInDB = await CurrenciesCRUD().first()

    await source_currency_entered_callback(
        create_callback_query_contract(
            user=user,
            data=(
                f"{CurrencyExchangeCallbackOperation.SELECT_SRC_CURRENCY}"
                f"{source_currency.id}"
            ),
        )
    )

    assert state.next_callback == source_value_entered_callback
    assert state.data.dict() == {"source_currency": source_currency}
    assert bot_edit_callback_query_patch.call_count == 1


async def test_source_value_entered_callback(
    bot_send_message_patch, create_user, create_message_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)
    source_currency: CurrencyInDB = await CurrenciesCRUD().first()
    state.populate_data({"source_currency": source_currency})

    await source_value_entered_callback(
        create_message_contract(user=user, text="12.25")
    )

    assert bot_send_message_patch.call_count == 1
    assert state.next_callback == destination_currency_entered_callback
    assert state.data.dict() == {
        "source_currency": source_currency,
        "source_value": 1225,
    }


async def test_destination_currency_entered_callback(
    bot_edit_callback_query_patch, create_user, create_callback_query_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)
    source_currency: CurrencyInDB = await CurrenciesCRUD().first()
    destination_currency: CurrencyInDB = await CurrenciesCRUD().last()
    state.populate_data(
        {"source_currency": source_currency, "source_value": 1225}
    )

    await destination_currency_entered_callback(
        create_callback_query_contract(
            user=user,
            data=(
                f"{CurrencyExchangeCallbackOperation.SELECT_DST_CURRENCY}"
                f"{destination_currency.id}"
            ),
        )
    )

    assert bot_edit_callback_query_patch.call_count == 1
    assert state.next_callback == destination_value_entered_callback
    assert state.data.dict() == {
        "source_currency": source_currency,
        "source_value": 1225,
        "destination_currency": destination_currency,
    }


async def test_destination_value_entered_callback(
    bot_send_message_patch, create_user, create_message_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)
    source_currency: CurrencyInDB = await CurrenciesCRUD().first()
    destination_currency: CurrencyInDB = await CurrenciesCRUD().last()
    state.populate_data(
        {
            "source_currency": source_currency,
            "source_value": 1225,
            "destination_currency": destination_currency,
        }
    )

    await destination_value_entered_callback(
        create_message_contract(user=user, text="20.00")
    )

    assert bot_send_message_patch.call_count == 1
    assert state.next_callback == date_selected_callback
    assert state.data.dict() == {
        "source_currency": source_currency,
        "source_value": 1225,
        "destination_currency": destination_currency,
        "destination_value": 2000,
    }


async def test_date_selected_callback(
    bot_edit_callback_query_patch, create_user, create_callback_query_contract
):
    user: User = await create_user("john")
    today = date.today()
    state: State = State(user.id)
    source_currency: CurrencyInDB = await CurrenciesCRUD().first()
    destination_currency: CurrencyInDB = await CurrenciesCRUD().last()
    state.populate_data(
        {
            "source_currency": source_currency,
            "source_value": 1225,
            "destination_currency": destination_currency,
            "destination_value": 2000,
        }
    )

    await date_selected_callback(
        create_callback_query_contract(
            user=user,
            data=(
                f"{CurrencyExchangeCallbackOperation.SELECT_DATE}"
                f"{today.strftime(DateFormat.FULL)}"
            ),
        )
    )

    assert bot_edit_callback_query_patch.call_count == 1
    assert state.next_callback == confirmation_entered_callback
    assert state.data.dict() == {
        "source_currency": source_currency,
        "source_value": 1225,
        "destination_currency": destination_currency,
        "destination_value": 2000,
        "date": today,
    }


async def test_confirmation_entered_callback_yes(
    bot_send_message_patch, create_user, create_callback_query_contract
):
    user: User = await create_user("john")
    today = date.today()
    state: State = State(user.id)
    source_currency: CurrencyInDB = await CurrenciesCRUD().first()
    destination_currency: CurrencyInDB = await CurrenciesCRUD().last()
    state.populate_data(
        {
            "source_currency": source_currency,
            "source_value": 1225,
            "destination_currency": destination_currency,
            "destination_value": 2000,
            "date": today,
        }
    )

    await confirmation_entered_callback(
        create_callback_query_contract(
            user=user,
            data=CurrencyExchangeCallbackOperation.SELECT_YES,
        )
    )

    currency_exchange_amount = await CurrencyExchangeCRUD().count()
    # Get currencies again to refresh the equity
    source_currency = await CurrenciesCRUD().first()
    destination_currency = await CurrenciesCRUD().last()

    assert bot_send_message_patch.call_count == 1
    assert state.next_callback is None
    assert state.data.dict() == {}
    assert currency_exchange_amount == 1
    assert source_currency.equity == -1225
    assert destination_currency.equity == 2000


async def test_confirmation_entered_callback_no(
    bot_send_message_patch, create_user, create_callback_query_contract
):
    """The currency exchange should no be saved if not confirmed."""

    user: User = await create_user("john")
    today = date.today()
    state: State = State(user.id)
    source_currency: CurrencyInDB = await CurrenciesCRUD().first()
    destination_currency: CurrencyInDB = await CurrenciesCRUD().last()
    state.populate_data(
        {
            "source_currency": source_currency,
            "source_value": 1225,
            "destination_currency": destination_currency,
            "destination_value": 2000,
            "date": today,
        }
    )

    await confirmation_entered_callback(
        create_callback_query_contract(
            user=user,
            data=CurrencyExchangeCallbackOperation.SELECT_NO,
        )
    )

    currency_exchange_amount = await CurrencyExchangeCRUD().count()
    # Get currencies again to refresh the equity
    source_currency = await CurrenciesCRUD().first()
    destination_currency = await CurrenciesCRUD().last()

    assert bot_send_message_patch.call_count == 1
    assert state.next_callback is None
    assert state.data.dict() == {}
    assert currency_exchange_amount == 0
    assert source_currency.equity == 0
    assert destination_currency.equity == 0
