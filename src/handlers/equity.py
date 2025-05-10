from src.application.database import transaction
from src.application.messages import MessageContract, Messages
from src.domain.money import CurrenciesCRUD, CurrencyInDB
from src.domain.money import services as money_services
from src.keyboards.default import default_keyboard


@transaction
async def equity_callback(contract: MessageContract):

    currencies: list[CurrencyInDB] = await CurrenciesCRUD().all()

    text = "\n\n".join(
        (
            "🏦 Капитализация",
            "\n".join(
                (
                    f"👉 {money_services.repr_value(currency.equity)} "
                    f"{currency.sign}"
                    for currency in currencies
                ),
            ),
        )
    )

    await Messages.send(
        chat_id=contract.user.chat_id, text=text, keyboard=default_keyboard()
    )
    await Messages.delete(contract.user.chat_id, contract.m.id)
