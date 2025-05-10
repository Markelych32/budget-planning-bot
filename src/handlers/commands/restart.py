from src.application.messages import MessageContract, Messages
from src.keyboards.default import default_keyboard

__all__ = ("restart",)


async def restart(contract: MessageContract):
    contract.state.messages_to_delete.add(contract.m.id)
    contract.state.clear_data()

    await Messages.delete(
        contract.user.chat_id, *contract.state.messages_to_delete
    )
    await Messages.send(
        chat_id=contract.m.chat.id,
        text="♻️  Operation disabled",
        keyboard=default_keyboard(),
    )
