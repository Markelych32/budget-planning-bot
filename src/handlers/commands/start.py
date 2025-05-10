from src.application.database import transaction
from src.application.messages import CommandContract, Messages
from src.domain.users import UserUncommited
from src.domain.users import services as users_services
from src.infrastructure.errors import DatabaseError
from src.keyboards.default import default_keyboard

__all__ = ("start",)


@transaction
async def start(contract: CommandContract):
    try:
        await users_services.create_user(
            UserUncommited(
                chat_id=contract.m.chat.id,
                account_id=contract.m.from_user.id,
                username=contract.m.from_user.username,
                full_name=contract.m.from_user.full_name,
            )
        )
        text = "\n".join(
            (
                "Привет 😎\nТеперь вы с нами!\n",
                '<a href="https://github.com/parfeniukink/family_budget_bot/releases">Репозиторий проекта</a>',  # noqa: E501
            )
        )
    except DatabaseError:
        text = "🤨 В чём проблема?\nЗачем вы ввели команду /start заново?"

    await Messages.send(
        chat_id=contract.m.chat.id, text=text, keyboard=default_keyboard()
    )
