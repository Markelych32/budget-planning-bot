from telebot import types

from src.keyboards.constants import Commands, Menu


def restart_keyboard() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(Commands.RESTART)

    return markup


def default_keyboard() -> types.ReplyKeyboardMarkup:

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(Menu.DELETE_COST, Menu.ADD_COST)
    markup.row(Menu.ANALYTICS, Menu.EQUITY)
    markup.row(Menu.INCOMES, Menu.EXCHANGE)
    markup.row(Menu.CONFIGURATIONS)

    return markup
