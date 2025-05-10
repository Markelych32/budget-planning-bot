from src.application.messages import CallbackQueryContract


async def option_selected_callback(contract: CallbackQueryContract):
    pass


async def level_selected_callback(contract: CallbackQueryContract):
    state = contract.state
    state.next_callback = option_selected_callback
