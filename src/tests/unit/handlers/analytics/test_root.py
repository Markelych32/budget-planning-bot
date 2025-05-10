import pytest

from src.application.states import State
from src.domain.analytics import AnalyticsRootOption, LevelOption
from src.domain.users import User
from src.handlers.analytics import analytics_action_selected_callback
from src.handlers.analytics.root import (
    basic_level_selected_callback,
    detailed_level_selected_callback,
    level_selected_callback,
)
from src.handlers.router import any_message
from src.infrastructure.errors import DeprecatedMessage
from src.keyboards.default import Menu


async def test_anonymous_trigger_analytics(
    bot_send_message_patch, create_message
):
    await any_message(create_message(Menu.ANALYTICS))

    assert bot_send_message_patch.call_count == 1


async def test_trigger_analytics(
    create_cost, bot_send_message_patch, create_message, create_user
):
    user: User = await create_user("john")
    state: State = State(user.id)
    await create_cost(user.id)

    await any_message(create_message(Menu.ANALYTICS))

    assert bot_send_message_patch.call_count == 1
    assert state.next_callback == analytics_action_selected_callback


async def test_analytics_action_selected_this_month_callback(
    bot_edit_callback_query_patch, create_user, create_callback_query_contract
):
    user: User = await create_user("john")
    state: State = State(user.id)
    contract = create_callback_query_contract(
        user=user, data=f"{AnalyticsRootOption.THIS_MONTH}"
    )

    await analytics_action_selected_callback(contract)

    assert state.next_callback == level_selected_callback
    assert bot_edit_callback_query_patch.call_count == 1


@pytest.mark.parametrize(
    "callback_data,expected_next_callback",
    [
        (LevelOption.SELECT_DETAILED_LEVEL, detailed_level_selected_callback),
        (LevelOption.SELECT_BASIC_LEVEL, basic_level_selected_callback),
    ],
)
async def test_level_selected_callback(
    callback_data,
    expected_next_callback,
    bot_edit_callback_query_patch,
    create_user,
    create_callback_query_contract,
):
    user: User = await create_user("john")
    state: State = State(user.id)
    contract = create_callback_query_contract(user=user, data=callback_data)

    await level_selected_callback(contract)

    assert state.next_callback == expected_next_callback
    assert bot_edit_callback_query_patch.call_count == 1


@pytest.mark.parametrize(
    "state_payload",
    [
        {"start_date": "something"},
        {"end_date": "something"},
    ],
)
async def test_detailed_level_selected_callback_fail(
    state_payload, create_user, create_callback_query_contract
):
    """Handler can not be used without start and end dates."""

    user: User = await create_user("john")
    state: State = State(user.id)
    state.populate_data(state_payload)
    contract = create_callback_query_contract(
        user=user, data=LevelOption.SELECT_DETAILED_LEVEL
    )

    with pytest.raises(DeprecatedMessage):
        await detailed_level_selected_callback(contract)
