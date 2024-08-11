import logging

from aiogram.types import ParseMode

from create_bot import bot, dp
from aiogram.dispatcher import FSMContext
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from database.sqlite_db import cur
from states.class_states import FSMAdmin

import keyboards

ADMIN_ID = [2043495890, 167628351, 7079102289]


async def mailing(message: types.Message):
    print("mailing function called")
    if message.from_user.id in ADMIN_ID:
        await FSMAdmin.photo.set()
        await message.reply('<b>Загрузите фото</b>', parse_mode=ParseMode.HTML, reply_markup=keyboards.client_kb.go_back_start_kb)
    else:
        print(f"User {message.from_user.id} is NOT in ADMIN_ID")


async def load_photo(message: types.Message, state: FSMContext):
    print("load_photo function called")
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id
    await FSMAdmin.next()
    await message.reply('<b>Теперь введите описание ...</b>', parse_mode=ParseMode.HTML)


async def load_desc(message: types.Message, state: FSMContext):
    print("load_desc function called")  # Отладочное сообщение
    async with state.proxy() as data:
        data['desc'] = message.html_text

    user_data = await state.get_data()
    mail_photo = user_data.get('photo', None)
    mail_desc = user_data.get('desc')

    print(f"user_data: {user_data}")  # Отладочное сообщение

    try:
        users_info_id = cur.execute("SELECT user_id FROM users").fetchall()
        for row in users_info_id:
            chat_id = row[0]
            try:
                await bot.send_photo(chat_id, mail_photo, caption=mail_desc)
            except Exception as e:
                logging.error(f"Ошибка при отправке сообщения пользователю {chat_id}: {e}")
        await bot.send_message(message.chat.id, '<b>Рассылка успешно <i>завершена ✅</i></b>', parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.error(f"Ошибка при выполнении запроса: {e}")

    await state.finish()


async def cancel_handler(message: types.Message, state: FSMContext):
    for admin in ADMIN_ID:
        if message.from_user.id == admin:
            current_state = await state.get_state()
            if current_state is None:
                return
            await state.finish()
            await message.reply('Процесс остановлен')


def register_handlers_admin(dp: Dispatcher):
    dp.register_message_handler(mailing, commands=['mail'], state=None)
    dp.register_message_handler(load_photo, content_types=['photo'], state=FSMAdmin.photo)
    dp.register_message_handler(load_desc, state=FSMAdmin.desc)
    dp.register_message_handler(cancel_handler, commands='cancel', state="*")
    dp.register_message_handler(cancel_handler, Text(equals='cancel', ignore_case=True), state="*")