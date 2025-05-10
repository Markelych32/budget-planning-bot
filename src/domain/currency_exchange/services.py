from src.domain.currency_exchange.models import (
    CurrencyExchange,
    CurrencyExchangeUncommited,
)
from src.domain.currency_exchange.repository import CurrencyExchangeCRUD
from src.domain.money import CurrenciesCRUD


async def save(schema: CurrencyExchangeUncommited) -> CurrencyExchange:

    exchange_crud = CurrencyExchangeCRUD()
    currencies_crud = CurrenciesCRUD()

    currency_exchange_in_db = await exchange_crud.create(schema)
    currency_exchange = await exchange_crud.get(currency_exchange_in_db.id)

    await currencies_crud.decrease_equity(
        id_=currency_exchange.source_currency.id,
        value=currency_exchange.source_value,
    )
    await currencies_crud.increase_equity(
        id_=currency_exchange.destination_currency.id,
        value=currency_exchange.destination_value,
    )

    return currency_exchange
