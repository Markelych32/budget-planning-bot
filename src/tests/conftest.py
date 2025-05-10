from datetime import date, datetime
from random import randint
from typing import Callable, Coroutine

import pytest
from alembic import command as alembic_command
from alembic import config as _alembic_config
from loguru import logger
from telebot import types

from src.application.database import transaction
from src.application.messages import CallbackQueryContract, MessageContract
from src.application.states import State
from src.domain.configurations import services as configurations_services
from src.domain.costs import CostInDB, CostsCRUD, CostUncommited
from src.domain.currency_exchange import (
    CurrencyExchangeCRUD,
    CurrencyExchangeInDB,
    CurrencyExchangeUncommited,
)
from src.domain.incomes import IncomeInDB, IncomesCRUD, IncomeUncommited
from src.domain.users import User, UserInDB, UsersCRUD, UserUncommited
from src.infrastructure.cache import Cache
from src.infrastructure.database import CTX_SESSION, IncomeSource

alembic_config = _alembic_config.Config(
    "alembic.ini",
)


def pytest_configure():
    # Disable logs
    logger.disable("src.infrastructure")
    logger.disable("src.handlers")
    logger.disable("src.domain")
    logger.disable("src.application")


# =====================================================================
# Database specific fixtures and mocks
# =====================================================================
@pytest.fixture(autouse=True)
def auto_prune_database():
    alembic_command.upgrade(alembic_config, "head")
    yield
    alembic_command.downgrade(alembic_config, "base")


@pytest.fixture(autouse=True)
async def _auto_close_session():
    yield
    session = CTX_SESSION.get()
    await session.close()


# =====================================================================
# Application specific fixtures and mocks
# =====================================================================
@pytest.fixture(autouse=True)
def _auto_clean_state():
    """Since State is used for storing the data between callback calls
    it should be cleaned for the each test."""

    yield
    State._instances.clear()


@pytest.fixture(autouse=True)
def _auto_clean_cache():
    """Since Cache is a regular dict it should be cleaned after each test."""

    yield
    Cache._DATA.clear()


@pytest.fixture(scope="session")
def default_users_raw() -> dict[str, UserUncommited]:
    """
    Since the user is allowed by the ACL from the environment variables,
    this dict represents valid users that could pass the @acl.
    """

    return {
        "john": UserUncommited(
            account_id=21, chat_id=1, username="john", full_name="John Doe"
        ),
        "marry": UserUncommited(
            account_id=22, chat_id=1, username="Marry", full_name="Marry Doe"
        ),
    }


@pytest.fixture
def create_user(default_users_raw) -> Callable[[str], Coroutine]:
    """Create the default user with the configuration."""

    @transaction
    async def inner(name: str) -> User:
        user_in_db: UserInDB = await UsersCRUD().create(
            default_users_raw[name]
        )
        await configurations_services.create_default(user_id=user_in_db.id)
        user: User = await UsersCRUD().get(user_in_db.id)

        return user

    return inner


@pytest.fixture
def create_cost() -> Callable[[int, int, int, str, int, date], Coroutine]:
    @transaction
    async def inner(
        user_id: int,
        category_id: int = 1,
        currency_id: int = 1,
        name: str = "Water",
        value: int | None = None,
        date_: date = date.today(),
    ) -> CostInDB:
        """Since categories and currencies are prepopulated at the very
        beginning, it is assumed that the first id is existed."""

        cost: CostInDB = await CostsCRUD().create(
            CostUncommited(
                name=name,
                value=value or randint(1000, 10000),
                date=date_,
                user_id=user_id,
                category_id=category_id,
                currency_id=currency_id,
            )
        )

        return cost

    return inner


@pytest.fixture
def create_income():
    @transaction
    async def inner(
        user_id: int,
        currency_id: int = 1,
        name: str = "Google",
        source: IncomeSource = IncomeSource.REVENUE,
        value: int | None = None,
        date_: date = date.today(),
    ) -> IncomeInDB:
        """Since currencies table is prepopulated at the very
        beginning, it is assumed that the first id is existed."""

        return await IncomesCRUD().create(
            IncomeUncommited(
                name=name,
                value=value or randint(1000, 10000),
                source=source,
                date=date_,
                user_id=user_id,
                currency_id=currency_id,
            )
        )

    return inner


@pytest.fixture
def create_currency_exchange():
    @transaction
    async def inner(
        user_id: int,
        source_value: int | None = None,
        destination_value: int | None = None,
        source_currency_id: int = 1,
        destination_currency_id: int = 2,
        date_: date = date.today(),
    ) -> CurrencyExchangeInDB:
        """Since currencies table is prepopulated at the very
        beginning, it is assumed that the first id is existed."""

        # NOTE: Currency exchange can not be used for the same currencies
        assert source_currency_id != destination_currency_id

        return await CurrencyExchangeCRUD().create(
            CurrencyExchangeUncommited(
                source_value=source_value or randint(1000, 10000),
                destination_value=destination_value or randint(1000, 10000),
                source_currency_id=source_currency_id,
                destination_currency_id=destination_currency_id,
                date=date_,
                user_id=user_id,
            )
        )

    return inner


@pytest.fixture
def create_message_contract(
    create_message,
) -> Callable[[User, str], MessageContract]:
    def inner(user: User, text: str = "") -> MessageContract:
        return MessageContract(
            m=create_message(account_id=user.account_id, text=text),
            state=State(user.id),
            user=user,
        )

    return inner


@pytest.fixture
def create_callback_query_contract(
    create_callback_query,
) -> Callable[[User, str], CallbackQueryContract]:
    def inner(user: User, data: str = "test") -> CallbackQueryContract:
        return CallbackQueryContract(
            q=create_callback_query(data=data, account_id=user.account_id),
            state=State(user.id),
            user=user,
        )

    return inner


# =====================================================================
# Telegram bot specific fixtures and mocks
# =====================================================================
@pytest.fixture(autouse=True)
def bot_send_message_patch(mocker):
    return mocker.patch("src.application.messages.services.bot.send_message")


@pytest.fixture(autouse=True)
def bot_edit_callback_query_patch(mocker):
    return mocker.patch(
        "src.application.messages.services.bot.edit_message_text"
    )


@pytest.fixture(autouse=True)
def bot_delete_message_patch(mocker):
    return mocker.patch("src.application.messages.services.Messages.delete")


@pytest.fixture
def create_message(default_users_raw: dict[str, UserUncommited]):
    def inner(
        text: str = "",
        account_id: int = default_users_raw["john"].account_id,
    ) -> types.Message:
        """
        By default it creates the message by user
        that corresponds to the ACL from settings.
        """

        message = types.Message(
            message_id=1,
            from_user=types.User(
                id=account_id,
                is_bot=False,
                username="test",
                first_name="test",
                last_name="test",
            ),
            chat=types.Chat(id=1, type="private"),
            date=int(datetime.now().timestamp()),
            content_type="text",
            options="",
            json_string="",
        )

        message.text = "test" if not text else text

        return message

    return inner


@pytest.fixture
def create_callback_query(default_users_raw, create_message):
    def inner(
        data: str,
        account_id: int = default_users_raw["john"].account_id,
        message: types.Message | None = None,
    ) -> types.CallbackQuery:
        """By default it creates the message by user
        that corresponds to the ACL from settings."""

        message = message or create_message(account_id=account_id)

        return types.CallbackQuery(
            id=1,
            data=data,
            from_user=types.User(
                id=account_id,
                is_bot=False,
                username="test",
                first_name="test",
                last_name="test",
            ),
            json_string="",
            chat_instance=types.Chat(id=1, type="private"),
            message=message,
        )

    return inner
