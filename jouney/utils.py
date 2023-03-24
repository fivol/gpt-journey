from aiogram import types


def gen_keyboard(keyboard):
    return types.ReplyKeyboardMarkup(
        [[types.KeyboardButton(btn) for btn in row] for row in keyboard],
        resize_keyboard=True
    )


def text(txt):
    return lambda m: m.text == txt
