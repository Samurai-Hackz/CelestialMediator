from aiogram import types, Dispatcher
from aiogram.types import ParseMode

from keyboards.admin_kb import abus_kb
from keyboards.client_kb import start_kb
from database.sqlite_db import sqlite_start
from create_bot import bot

from database.sqlite_db import cur

ADMIN_ID = [2043495890, 167628351, 7079102289]


async def start(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    username = message.from_user.username
    await message.delete()

    # Получаем список всех admin_id из базы данных
    admin_ids = [admin_sel[0] for admin_sel in cur.execute('SELECT admin_id FROM admin_info').fetchall()]

    if message.chat.type == "private":
        if user_id in admin_ids:
            # Пользователь является администратором
            await bot.send_photo(
                message.chat.id,
                open('img/admin-start.jpg', 'rb'),
                f'<b>Добрый день хранитель :</b>',
                reply_markup=abus_kb,
                parse_mode=ParseMode.HTML
            )
            print(user_id)
        else:
            # Пользователь не является администратором
            await bot.send_photo(
                message.chat.id,
                open('img/mainmenu.jpg', 'rb'),
                f'<b>Добрый день</b> <b><i>{name}</i></b>',
                reply_markup=start_kb,
                parse_mode=ParseMode.HTML
            )
        # Вызов функции для обработки нового пользователя
        sqlite_start(user_id, name, username)
    elif message.chat.type == "group":
        await bot.send_message(
            message.chat.id,
            '<b>Общение с ботом <i>только</i> через лс</b>',
            parse_mode=ParseMode.HTML
        )


def register_handlers_client(dp: Dispatcher):
    dp.register_message_handler(start, commands=['start'])
