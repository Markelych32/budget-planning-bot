from typing import AsyncGenerator

from src.application.database import transaction
from src.application.messages import (
    CallbackMessages,
    CallbackQueryContract,
    MessageContract,
    Messages,
)
from src.domain.analytics import (
    AnalyticsRootOption,
    BasicOption,
    DetailAnalyticsCallbackOperation,
    DetailedOption,
    LevelOption,
)
from src.domain.analytics import services as analytics_services
from src.domain.categories import services as categories_services
from src.domain.dates import DateFormat
from src.domain.dates import services as dates_services
from src.infrastructure.errors import UserError
from src.keyboards.constants import (
    ANALYTICS_BASIC_OPTIONS_KEYBOARD_ELEMENTS,
    ANALYTICS_DETAILED_OPTIONS_KEYBOARD_ELEMENTS,
)
from src.keyboards.default import default_keyboard
from src.keyboards.models import CallbackItem
from src.keyboards.patterns import callback_patterns_keyboard

__all__ = (
    "analytics_general_menu_callback",
    "analytics_action_selected_callback",
)


@transaction
async def basic_level_selected_callback(contract: CallbackQueryContract):
    state = contract.state
    state.check_data("start_date", "end_date")

    match contract.q.data:
        case BasicOption.ALL:
            frames = analytics_services.get_basic_analytics_in_range(
                start=state.data.start_date,  # type: ignore
                end=state.data.end_date,  # type: ignore
            )
        case BasicOption.ONLY_MY:
            frames = analytics_services.get_basic_analytics_in_range(
                start=state.data.start_date,  # type: ignore
                end=state.data.end_date,  # type: ignore
                by_user=contract.user,
            )
        case _:
            raise Exception

    title_text = (
        "📊 Диапазон времени для аналитики:\n"
        "**************************\n"
        f"{state.data.start_date.strftime(DateFormat.FULL)} - "  # type: ignore
        f"{state.data.end_date.strftime(DateFormat.FULL)}"  # type: ignore
    )
    await Messages.send(
        chat_id=contract.user.chat_id,
        text=title_text,
        keyboard=default_keyboard(),
    )

    async for frame in frames:
        await Messages.send(
            chat_id=contract.user.chat_id,
            text=frame,
            keyboard=default_keyboard(),
        )

    await Messages.delete(contract.user.chat_id, *state.messages_to_delete)


async def category_selected_callback(contract: CallbackQueryContract):
    state = contract.state
    category_id = int(
        contract.q.data.replace(
            DetailAnalyticsCallbackOperation.SELECT_CATEGORY, ""
        )
    )

    frames: AsyncGenerator = analytics_services.get_detailed_costs_in_range(
        start=state.data.start_date,  # type: ignore
        end=state.data.end_date,  # type: ignore
        date_format=DateFormat.DAILY,
        category_id=category_id,
    )

    no_frames = True

    async for frame in frames:
        no_frames = False

        await Messages.send(
            chat_id=contract.user.chat_id,
            text=frame,
            keyboard=default_keyboard(),
        )

    if no_frames:
        await Messages.delete(contract.user.chat_id, *state.messages_to_delete)
        raise UserError("¯\\_(ツ)_/¯ Пусто")
    else:
        await Messages.delete(contract.user.chat_id, *state.messages_to_delete)


@transaction
async def detailed_level_selected_callback(contract: CallbackQueryContract):
    state = contract.state
    state.check_data("start_date", "end_date")

    match contract.q.data:
        case DetailedOption.ONLY_MY:
            frames: AsyncGenerator = (
                analytics_services.get_detailed_analytics_in_range(
                    start=state.data.start_date,  # type: ignore
                    end=state.data.end_date,  # type: ignore
                    date_format=DateFormat.DAILY,
                    by_user=contract.user,
                )
            )
        case DetailedOption.ALL:
            frames = analytics_services.get_detailed_analytics_in_range(
                start=state.data.start_date,  # type: ignore
                end=state.data.end_date,  # type: ignore
                date_format=DateFormat.DAILY,
            )
        case DetailedOption.ONLY_INCOMES:
            frames = analytics_services.get_detailed_incomes_in_range(
                start=state.data.start_date,  # type: ignore
                end=state.data.end_date,  # type: ignore
                date_format=DateFormat.DAILY,
            )
        case DetailedOption.ONLY_CURRENCY_EXCHANGES:
            frames = (
                analytics_services.get_detailed_currency_exchanges_in_range(
                    start=state.data.start_date,  # type: ignore
                    end=state.data.end_date,  # type: ignore
                    date_format=DateFormat.DAILY,
                )
            )
        case DetailedOption.BY_CATEGORY:
            # NOTE: Since next step is needed -
            #       frames should not be represented
            state.next_callback = category_selected_callback

            # Prepare categories names with callback data
            keyboard_patterns: list[CallbackItem] = []
            filtered_categories = await categories_services.get_all()
            for category in filtered_categories:
                _callback_data = "".join(
                    (
                        DetailAnalyticsCallbackOperation.SELECT_CATEGORY,
                        str(category.id),
                    )
                )
                keyboard_patterns.append(
                    CallbackItem(
                        name=category.name, callback_data=_callback_data
                    )
                )
            return await CallbackMessages.edit(
                q=contract.q,
                text="🤔 Выберите категорию",
                keyboard=callback_patterns_keyboard(keyboard_patterns),
            )
        case _:
            raise ValueError("Некорректный ввод для раздела аналитики")

    no_frames = True

    async for frame in frames:
        no_frames = False
        await Messages.send(
            chat_id=contract.user.chat_id,
            text=frame,
            keyboard=default_keyboard(),
        )

    if no_frames:
        state.messages_to_delete.add(contract.q.id)
        raise UserError("¯\\_(ツ)_/¯ Пусто")

    state.messages_to_delete.add(contract.q.id)
    await Messages.delete(contract.user.chat_id, *state.messages_to_delete)


async def level_selected_callback(contract: CallbackQueryContract):
    state = contract.state

    match contract.q.data:
        case LevelOption.SELECT_BASIC_LEVEL:
            state.next_callback = basic_level_selected_callback
            keyboard = callback_patterns_keyboard(
                ANALYTICS_BASIC_OPTIONS_KEYBOARD_ELEMENTS
            )
        case LevelOption.SELECT_DETAILED_LEVEL:
            state.next_callback = detailed_level_selected_callback
            keyboard = callback_patterns_keyboard(
                ANALYTICS_DETAILED_OPTIONS_KEYBOARD_ELEMENTS
            )
        case _:
            raise ValueError("Некорректный ввод для раздела аналитики")

    await CallbackMessages.edit(
        q=contract.q, text="🤔 Выберите следующую опцию", keyboard=keyboard
    )

    state.messages_to_delete.add(contract.q.id)


async def pattern_entered_callback(contract: MessageContract):
    state = contract.state
    start_date, end_date = analytics_services.dates_range_by_pattern(
        contract.m.text
    )
    state.data.start_date = start_date
    state.data.end_date = end_date

    dates_delta: int = (end_date - start_date).days

    if dates_delta <= 31:
        state.next_callback = level_selected_callback

        message = await Messages.send(
            chat_id=contract.user.chat_id,
            text="🤔 Выберите уровень аналитики",
            keyboard=callback_patterns_keyboard(
                [
                    CallbackItem(
                        name="Подробный",
                        callback_data=LevelOption.SELECT_DETAILED_LEVEL,
                    ),
                    CallbackItem(
                        name="Обычный",
                        callback_data=LevelOption.SELECT_BASIC_LEVEL,
                    ),
                ]
            ),
        )

    else:
        state.next_callback = basic_level_selected_callback
        message = await Messages.send(
            chat_id=contract.user.chat_id,
            text="🤔 Выберите уровень аналитики",
            keyboard=callback_patterns_keyboard(
                ANALYTICS_BASIC_OPTIONS_KEYBOARD_ELEMENTS
            ),
        )

    state.messages_to_delete.add(contract.m.id)
    state.messages_to_delete.add(message.id)


async def analytics_action_selected_callback(contract: CallbackQueryContract):
    state = contract.state

    match contract.q.data:
        case AnalyticsRootOption.THIS_MONTH:
            start_date, end_date = dates_services.this_month_edge_dates()
            state.data.start_date = start_date
            state.data.end_date = end_date

            state.next_callback = level_selected_callback

            await CallbackMessages.edit(
                q=contract.q,
                text="🤔 Выберите уровень аналитики",
                keyboard=callback_patterns_keyboard(
                    [
                        CallbackItem(
                            name="Подробный",
                            callback_data=LevelOption.SELECT_DETAILED_LEVEL,
                        ),
                        CallbackItem(
                            name="Обычный",
                            callback_data=LevelOption.SELECT_BASIC_LEVEL,
                        ),
                    ]
                ),
            )
        case AnalyticsRootOption.PREVIOUS_MONTH:
            start_date, end_date = dates_services.previous_month_edge_dates()
            state.data.start_date = start_date
            state.data.end_date = end_date

            state.next_callback = level_selected_callback

            await CallbackMessages.edit(
                q=contract.q,
                text="🤔 Выберите уровень аналитики",
                keyboard=callback_patterns_keyboard(
                    [
                        CallbackItem(
                            name="Подробный",
                            callback_data=LevelOption.SELECT_DETAILED_LEVEL,
                        ),
                        CallbackItem(
                            name="Обычный",
                            callback_data=LevelOption.SELECT_BASIC_LEVEL,
                        ),
                    ]
                ),
            )
        case AnalyticsRootOption.BY_PATTERN:
            await CallbackMessages.edit(
                q=contract.q,
                text="⤵️ Введите шаблон или диапазон и нажмите Enter",
                keyboard=None,
            )

            state.next_callback = pattern_entered_callback
        case _:
            raise ValueError("Некорректный ввод для раздела аналитики")

    state.messages_to_delete.add(contract.q.id)


async def analytics_general_menu_callback(contract: MessageContract):
    state = contract.state
    state.clear_data()
    state.next_callback = analytics_action_selected_callback

    keyboard = callback_patterns_keyboard(
        [
            CallbackItem(
                name="📅 Предыдущий месяц",
                callback_data=AnalyticsRootOption.PREVIOUS_MONTH,
            ),
            CallbackItem(
                name="📅 Текущий месяц",
                callback_data=AnalyticsRootOption.THIS_MONTH,
            ),
            CallbackItem(
                name="🗓️ Выбрать диапазон",
                callback_data=AnalyticsRootOption.BY_PATTERN,
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
