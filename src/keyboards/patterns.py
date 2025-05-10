from telebot import types

from src.infrastructure.utils import list_by_chunks
from src.keyboards.models import CallbackItem


def patterns_keyboard(
    patterns: list[str], width: int = 2
) -> types.ReplyKeyboardMarkup:

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    sources = [item for el in patterns if (item := el.strip())]

    for elements in list_by_chunks(sources, size=width):
        markup.row(*elements)

    return markup


def callback_patterns_keyboard(
    patterns: list[CallbackItem], width: int = 2
) -> types.InlineKeyboardMarkup:

    keyboard = [
        [
            types.InlineKeyboardButton(
                text=item.name,
                callback_data=item.callback_data,
            )
            for item in chunk
        ]
        for chunk in list_by_chunks(patterns, size=width)
    ]

    return types.InlineKeyboardMarkup(keyboard)
