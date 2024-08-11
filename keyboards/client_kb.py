from aiogram.dispatcher.filters import Text

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, ReplyKeyboardMarkup, KeyboardButton, \
    InputMediaPhoto, LabeledPrice
from aiogram.dispatcher import FSMContext
from create_bot import dp, types
from create_bot import bot
import os
from dotenv import load_dotenv

from database import sqlite_db
from states.class_states import DataInfo, AmountOfPayment

load_dotenv()
answer = dict()

ADMIN_ID = [2043495890, 167628351, 7079102289]

# Command after /start command

start_kb = InlineKeyboardMarkup(row_width=2)
start_kb1 = InlineKeyboardButton(text='Ассортименты', callback_data='start_kb1')
start_kb2 = InlineKeyboardButton(text='О нас ℹ️', callback_data='start_kb2')
start_kb3 = InlineKeyboardButton(text='Корзина 🛒', callback_data='start_kb3')
start_kb4 = InlineKeyboardButton(text='Оставить отзыв ✍', callback_data='start_kb4')
start_kb5 = InlineKeyboardButton(text='Баланс 💰', callback_data='start_kb5')

start_kb.add(start_kb1)
start_kb.add(start_kb2, start_kb3)
start_kb.add(start_kb4, start_kb5)


# Go back after /start command

go_back_start_kb = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
go_back_start_kb1 = KeyboardButton('Назад')
go_back_start_kb.add(go_back_start_kb1)

# FSMContext stopping command


@dp.message_handler(text='Назад', state="*")
@dp.message_handler(Text(equals='Назад', ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    from handlers.client import start

    await bot.send_message(message.chat.id, '<b>Процесс остановлен. Спасибо за <i>содействия</i></b>', parse_mode=ParseMode.HTML)
    current_state = await state.get_state()
    if current_state is None:
        return
    await start(message)
    await state.finish()

# section "Ассортименты" in /start : start_kb1


@dp.callback_query_handler(lambda goods: goods.data == 'start_kb1')
async def about_us1(call: types.CallbackQuery):
    await call.answer('Вы нажали на кнопку')
    media = InputMediaPhoto(open('img/goods.jpg', 'rb'), caption='<b>Ассортименты :</b>', parse_mode=ParseMode.HTML)
    await bot.edit_message_media(media, call.message.chat.id, call.message.message_id, reply_markup=all_menu)

# section About us - callback : start_kb2


@dp.callback_query_handler(lambda abus: abus.data == 'start_kb2')
async def about_us2(call: types.CallbackQuery):
    await call.answer('Вы нажали на кнопку')
    await sqlite_db.onas_sql(call)


@dp.callback_query_handler(lambda abus: abus.data == 'start_kb2')
async def about_us(call: types.CallbackQuery):
    await call.answer('Вы нажали на кнопку')
    await sqlite_db.onas_sql(call)


@dp.callback_query_handler(lambda c: c.data == 'start_kb3')
async def start_kb3(call: types.CallbackQuery):
    from database import sqlite_db

    await call.answer('Вы нажали на корзину')
    await sqlite_db.basket_get(message=call.message, user_id=call.from_user.id)


# FSMContext for /start keyboard : start_kb4

@dp.callback_query_handler(lambda c: c.data == "start_kb4")
async def start_kb4(call: types.CallbackQuery):
    await call.answer('Напишите отзыв')
    await bot.send_message(call.message.chat.id, '<b>Напишите отзыв ниже 👇</b>', reply_markup=go_back_start_kb, parse_mode=ParseMode.HTML)
    await DataInfo.text_answer.set()


@dp.message_handler(content_types=types.ContentType.TEXT, state=DataInfo.text_answer)
async def receive_feedback(message: types.Message, state: FSMContext):
    feedback_text = message.text
    await message.delete()
    await bot.send_message(message.chat.id, f'<b>Спасибо за отзыв <a href="{message.from_user.id}">{message.from_user.first_name}</a></b>', parse_mode=ParseMode.HTML)

    await bot.send_message(os.getenv('CHAT_ID'), f"<b>Получен отзыв ✅</b>\n\n<b>Связь с пользователем: <a href='tg://user?id={message.from_user.id}'>ТЫКНИ</a></b>\n<b>Отзыв: <i>{feedback_text}</i></b>", parse_mode=ParseMode.HTML)
    await state.finish()


update_balance = InlineKeyboardMarkup()
update_balance.add(InlineKeyboardButton('Пополнить баланс 💲', callback_data='update_balance'))


@dp.callback_query_handler(lambda c: c.data == 'start_kb5')
async def start_kb5(call: types.CallbackQuery):
    from database.sqlite_db import show_ballance

    await call.answer('Вы нажали на баланс')
    await show_ballance(user_id=call.from_user.id, message=call.message)


@dp.callback_query_handler(lambda c: c.data == 'update_balance')
async def get_balance(call: types.CallbackQuery):
    await call.answer('Вы нажали на пополнить баланс')
    await call.message.reply('<b>Пожалуйста введите сумму пополнения ...</b>', parse_mode=ParseMode.HTML)
    await AmountOfPayment.bill.set()


@dp.message_handler(state=AmountOfPayment.bill)
async def amount_of_payment(message: types.Message, state: FSMContext):
    if float(message.text) > 5000:
        async with state.proxy() as data:
            data['bill'] = message.text
    else:
        await message.reply('<b>Оплата принимается минимум с 5.000 сум</b>', parse_mode=ParseMode.HTML)

    bill_amount = await state.get_data()
    bill_amount_get = bill_amount.get('bill')

    try:
        bill_amount_value = int(bill_amount_get)
        if bill_amount_value <= 0:
            raise ValueError("Сумма должна быть больше нуля.")

        total_amount_in_tiyin = bill_amount_value * 100

        prices = [LabeledPrice(label='Пополнение счета', amount=total_amount_in_tiyin)]

        await bot.send_invoice(
            chat_id=message.chat.id,
            title='Пополнение счета через Click',
            description='Общая сумма для пополнения :\n',
            payload='unique_payload',
            provider_token=os.getenv("PAYMENT_TOKEN"),
            start_parameter='test-payment',
            currency='UZS',
            prices=prices
        )
    except ValueError as e:
        print(f"Ошибка: {str(e)}. Введите корректную сумму.")
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")

    await state.finish()


@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def success_payment(message: types.Message):
    from database.sqlite_db import bank_counter

    payment_info = message.successful_payment
    await message.reply(f'<b>Оплата в размере <i>{payment_info}</i> была успешно проведена, спасибо за доверие 😊</b>', parse_mode=ParseMode.HTML)
    await bank_counter(payment_info, user_id=message.from_user.id, message=message)


all_menu = InlineKeyboardMarkup(row_width=2)
all_menu_kb1 = InlineKeyboardButton('Периферия', callback_data='menu_others')
all_menu_kb2 = InlineKeyboardButton('Комплектующие', callback_data='menu_components')
all_menu_kb3 = InlineKeyboardButton('Дэкор', callback_data='menu_decor')
all_menu_kb4 = InlineKeyboardButton('Назад ️◀️', callback_data='menu_back')
all_menu.add(all_menu_kb1, all_menu_kb2)
all_menu.add(all_menu_kb3)
all_menu.add(all_menu_kb4)

other_menu = InlineKeyboardMarkup(row_width=2)
other_menu_kb1 = InlineKeyboardButton('Мониторы', callback_data='menutype_scr')
other_menu_kb2 = InlineKeyboardButton('Клавиатуры', callback_data='menutype_kb')
other_menu_kb3 = InlineKeyboardButton('Мышки', callback_data='menutype_ms')
other_menu_kb4 = InlineKeyboardButton('Коврики', callback_data='menutype_crpt')
other_menu_kb5 = InlineKeyboardButton('Наушники', callback_data='menutype_hdp')
other_menu_kb6 = InlineKeyboardButton('Корпуса', callback_data='menutype_corpus')
other_menu_kb7 = InlineKeyboardButton('Назад ️◀️', callback_data='other_menu_back')
other_menu.add(other_menu_kb1, other_menu_kb2, other_menu_kb3, other_menu_kb4, other_menu_kb5, other_menu_kb6)
other_menu.add(other_menu_kb7)


@dp.callback_query_handler(lambda c: c.data.startswith('menu_'))
async def menu_components(call: types.CallbackQuery):
    from handlers import client

    menu_components_get = call.data.split('_')[1]

    if menu_components_get == 'back':
        await call.answer('Вы нажали назад')

        await client.start(call.message)
    elif menu_components_get == 'others':
        media_photo_others = InputMediaPhoto(open('img/goods.jpg', 'rb'), caption='<b>Периферия :</b>',
                                      parse_mode=ParseMode.HTML)
        await bot.edit_message_media(media_photo_others, call.message.chat.id, call.message.message_id, reply_markup=other_menu)
    elif menu_components_get == 'components':
        media_photo_components = InputMediaPhoto(open('img/goods.jpg', 'rb'), caption='<b>Комплектующие :</b>',
                                             parse_mode=ParseMode.HTML)
        await bot.edit_message_media(media_photo_components, call.message.chat.id, call.message.message_id,
                                     reply_markup=menu_list)


@dp.callback_query_handler(lambda c: c.data.startswith('other_menu_'))
async def menu_others_components(call: types.CallbackQuery):
    menu_others_component = call.data.split('_')[2]

    if menu_others_component == 'back':
        media_photo = InputMediaPhoto(open('img/goods.jpg', 'rb'), caption='<b>Ассортименты :</b>', parse_mode=ParseMode.HTML)
        await bot.edit_message_media(media_photo, call.message.chat.id, call.message.message_id, reply_markup=all_menu)


menu_list = InlineKeyboardMarkup(row_width=2)
menu_list_1 = InlineKeyboardButton('Мат.Платы', callback_data='menutype_mb')
menu_list_2 = InlineKeyboardButton('Процессоры', callback_data='menutype_cpu')
menu_list_3 = InlineKeyboardButton('Блоки питания', callback_data='menutype_psu')
menu_list_4 = InlineKeyboardButton('ОЗУ', callback_data='menutype_ram')
menu_list_5 = InlineKeyboardButton('Видеокарты', callback_data='menutype_gpu')
menu_list_6 = InlineKeyboardButton('SSD-накопители', callback_data='menutype_ssd')
menu_list_7 = InlineKeyboardButton('Блоки питания', callback_data='menutype_hdd')
menu_list_8 = InlineKeyboardButton('Кулер', callback_data='menutype_cooler')
menu_list_back = InlineKeyboardButton('Назад ◀️', callback_data='other_menu_back')
menu_list.add(menu_list_1, menu_list_2, menu_list_3, menu_list_4, menu_list_5, menu_list_6, menu_list_7, menu_list_8)
menu_list.add(menu_list_back)


@dp.callback_query_handler(text='menu_type_func_del')
async def menu_type_del(call: types.CallbackQuery):
    await bot.answer_callback_query(
        callback_query_id=call.id,
        text='Вы выбрали удалить пост',
        show_alert=False
    )


@dp.callback_query_handler(text='menu_list_back')
async def go_back(call: types.CallbackQuery):
    from handlers.client import start

    await call.answer('Вы нажали назад')
    await start(call.message)


@dp.callback_query_handler(text='start_kb1')
async def start_kb1(call: types.CallbackQuery):
    await call.message.delete()
    await bot.send_message(call.from_user.id, "<b>Меню</b>", reply_markup=menu_list, parse_mode=ParseMode.HTML)


reset_data_cart = InlineKeyboardMarkup()
reset_data_cart.add(InlineKeyboardButton('Удалить данные 🗑', callback_data='cart_data_reset'),
                    InlineKeyboardButton('Оплатить корзину 💲', callback_data='cart_data_pay'))


@dp.callback_query_handler(lambda c: c.data.startswith('cart_data_'))
async def res_cart(call: types.CallbackQuery):
    from database.sqlite_db import process_payment
    cart_information = call.data.split('_')[2]

    if cart_information == 'reset':
        await call.answer('Вы нажали на удалить данные из корзины')
        await bot.send_message(call.message.chat.id, '<b>Данные из корзины были успешно <i>удалены ✅</i></b>', parse_mode=ParseMode.HTML)
        await sqlite_db.res_data_from_cart(user_id=call.from_user.id, message=call.message)
    elif cart_information == 'pay':
        await call.answer('Вы нажали на оплатить товар из корзины')
        await process_payment(user_id=call.from_user.id, message=call.message)


@dp.callback_query_handler(lambda c: c.data == 'delete_balance_info')
async def del_balance(call: types.CallbackQuery):
    try:
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id-1)
    except Exception as e:
        await call.message.reply(f"Ошибка при удалении сообщения: {e}")