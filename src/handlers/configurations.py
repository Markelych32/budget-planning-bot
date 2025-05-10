from src.application.database import transaction
from src.application.messages import (
    CallbackMessages,
    CallbackQueryContract,
    MessageContract,
    Messages,
)
from src.domain.categories import CategoriesCRUD, CategoryInDB
from src.domain.configurations import (
    ConfigurationRootOption,
    ConfigurationsCRUD,
    ConfigurationUpdateOption,
)
from src.domain.configurations import services as configurations_services
from src.domain.money import CurrenciesCRUD, CurrencyInDB
from src.infrastructure.errors import UserError
from src.keyboards.default import default_keyboard
from src.keyboards.models import CallbackItem
from src.keyboards.patterns import callback_patterns_keyboard


@transaction
async def number_of_dates_selected_callback(contract: MessageContract):
    try:
        if not contract.m.text:
            raise ValueError
        number_of_dates = int(contract.m.text)
    except ValueError:
        raise UserError("⚠️ Значение должно быть корректным числом")

    await ConfigurationsCRUD().update_number_of_dates(
        configuration_id=contract.user.configuration.id,
        payload=number_of_dates,
    )

    await Messages.send(
        chat_id=contract.user.chat_id,
        text="✅ Настройки обновлены",
        keyboard=default_keyboard(),
    )

    contract.state.messages_to_delete.add(contract.m.id)
    await Messages.delete(
        contract.user.chat_id, *contract.state.messages_to_delete
    )


@transaction
async def costs_sources_selected_callback(contract: MessageContract):
    if not contract.m.text:
        raise UserError("⚠️ Должен быть источник")

    payload = configurations_services.clean_sources_input(contract.m.text)

    await ConfigurationsCRUD().update_costs_sources(
        configuration_id=contract.user.configuration.id, payload=payload
    )

    await Messages.send(
        chat_id=contract.user.chat_id,
        text="✅ Настройки обновлены",
        keyboard=default_keyboard(),
    )

    contract.state.messages_to_delete.add(contract.m.id)
    await Messages.delete(
        contract.user.chat_id, *contract.state.messages_to_delete
    )


@transaction
async def incomes_sources_selected_callback(contract: MessageContract):
    if not contract.m.text:
        raise UserError("⚠️ Должен быть источник")

    payload = configurations_services.clean_sources_input(contract.m.text)

    await ConfigurationsCRUD().update_incomes_sources(
        configuration_id=contract.user.configuration.id, payload=payload
    )

    await Messages.send(
        chat_id=contract.user.chat_id,
        text="✅ Настройки обновлены",
        keyboard=default_keyboard(),
    )

    contract.state.messages_to_delete.add(contract.m.id)
    await Messages.delete(
        contract.user.chat_id, *contract.state.messages_to_delete
    )


@transaction
async def ignore_categories_entered_callback(contract: MessageContract):
    if not contract.m.text:
        raise UserError("⚠️ Должны быть идентификаторы категорий")

    payload = await configurations_services.clean_ignore_categories(
        contract.m.text
    )

    await ConfigurationsCRUD().update_ignore_categories(
        configuration_id=contract.user.configuration.id, payload=payload
    )

    await Messages.send(
        chat_id=contract.user.chat_id,
        text="✅ Настройки обновлены",
        keyboard=default_keyboard(),
    )

    contract.state.messages_to_delete.add(contract.m.id)
    await Messages.delete(
        contract.user.chat_id, *contract.state.messages_to_delete
    )


@transaction
async def default_currency_selected_callback(contract: CallbackQueryContract):
    currency_id: int = int(
        contract.q.data.replace(ConfigurationUpdateOption.SELECT_CURRENCY, "")
    )
    currency: CurrencyInDB = await CurrenciesCRUD().get(currency_id)
    await ConfigurationsCRUD().update_default_currency(
        contract.user.configuration.id, currency.id
    )

    await Messages.send(
        chat_id=contract.user.chat_id,
        text="✅ Настройки обновлены",
        keyboard=default_keyboard(),
    )

    await Messages.delete(
        contract.user.chat_id, *contract.state.messages_to_delete
    )


async def update_submenu_option_selected_callback(
    contract: CallbackQueryContract,
):
    state = contract.state
    state.messages_to_delete.add(contract.q.message.id)

    match contract.q.data:
        case ConfigurationUpdateOption.NUMBER_OF_DATES:
            await CallbackMessages.edit(
                q=contract.q,
                text="⤵️ Введите число и нажмите Enter",
                keyboard=None,
            )
            state.next_callback = number_of_dates_selected_callback
        case ConfigurationUpdateOption.COSTS_SOURCES:
            text = (
                "⤵️ Введите новые источники расходов и нажмите Enter\n"
                "<i>Например: Вкусно - и точка, Вода, Шоколадные конфеты</i>"
            )
            await CallbackMessages.edit(q=contract.q, text=text, keyboard=None)
            state.next_callback = costs_sources_selected_callback
        case ConfigurationUpdateOption.INCOMES_SOURCES:
            text = (
                "⤵️ Введите основные источники доходов и нажмите Enter\n"
                "<i>Например: Моя любимая работа, лотерея</i>"
            )
            await CallbackMessages.edit(q=contract.q, text=text, keyboard=None)
            state.next_callback = incomes_sources_selected_callback
        case ConfigurationUpdateOption.IGNORE_CATEGORIES:
            categories: list[CategoryInDB] = await CategoriesCRUD().all()
            categories_text = "\n".join(
                (
                    (f"{category.id} 👉 {category.name}")
                    for category in categories
                )
            )

            text = (
                "Вот список категорий с идентификаторами:\n"
                f"{categories_text}"
                "\n\n⤵️ Пожалуйста, введите идентификаторы категорий для <b>удаления</b> через запятую."
                "\n<i>Например: 1,2,3,5,19</i>"
            )
            await CallbackMessages.edit(q=contract.q, text=text, keyboard=None)
            state.next_callback = ignore_categories_entered_callback
        case ConfigurationUpdateOption.DEFAULT_CURRENCY:
            currencies: list[CurrencyInDB] = await CurrenciesCRUD().all()

            keyboard_patterns = [
                CallbackItem(
                    name=f"{currency.name} {currency.sign}",
                    callback_data=(
                        f"{ConfigurationUpdateOption.SELECT_CURRENCY}{currency.id}"
                    ),
                )
                for currency in currencies
            ]
            await CallbackMessages.edit(
                q=contract.q,
                text="🤔 Выберите валюту по умолчанию",
                keyboard=callback_patterns_keyboard(keyboard_patterns),
            )
            state.next_callback = default_currency_selected_callback
        case _:
            raise Exception


async def configuration_submenu_option_selected_callback(
    contract: CallbackQueryContract,
):
    state = contract.state

    match contract.q.data:
        case ConfigurationRootOption.GET_ALL:
            await CallbackMessages.edit(
                q=contract.q, text=contract.user.configuration.represent()
            )
            await Messages.delete(
                contract.user.chat_id, *state.messages_to_delete
            )
        case ConfigurationRootOption.UPDATE:
            state.next_callback = update_submenu_option_selected_callback
            state.messages_to_delete.add(contract.q.id)
            await CallbackMessages.edit(
                q=contract.q,
                text="🤔 Выберите какой параметр изменить",
                keyboard=callback_patterns_keyboard(
                    [
                        CallbackItem(
                            name=" 🎨 Основные источники расходов",
                            callback_data=ConfigurationUpdateOption.COSTS_SOURCES,
                        ),
                        CallbackItem(
                            name="🎨 Основные источники доходов",
                            callback_data=ConfigurationUpdateOption.INCOMES_SOURCES,
                        ),
                        CallbackItem(
                            name="👮‍♂️ Исключить категории",
                            callback_data=ConfigurationUpdateOption.IGNORE_CATEGORIES,
                        ),
                        CallbackItem(
                            name="🔢 Кол-во дней для выбора",
                            callback_data=ConfigurationUpdateOption.NUMBER_OF_DATES,
                        ),
                        CallbackItem(
                            name="💱 Валюта по умолчанию",
                            callback_data=ConfigurationUpdateOption.DEFAULT_CURRENCY,
                        ),
                    ],
                    width=1,
                ),
            )
        case _:
            raise Exception


async def configurations_general_callback(contract: MessageContract):
    contract.state.clear_data()

    await Messages.send(
        chat_id=contract.user.chat_id,
        text="🤔 Выберите следующую опцию",
        keyboard=callback_patterns_keyboard(
            [
                CallbackItem(
                    name="♻️ Изменить",
                    callback_data=ConfigurationRootOption.UPDATE,
                ),
                CallbackItem(
                    name="🔦 Показать",
                    callback_data=ConfigurationRootOption.GET_ALL,
                ),
            ]
        ),
    )

    contract.state.next_callback = (
        configuration_submenu_option_selected_callback
    )
    contract.state.messages_to_delete.add(contract.m.id)
