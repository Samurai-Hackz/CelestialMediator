from aiogram.dispatcher.filters import Text

from database.sqlite_db import admin_info_add, admin_info_del, admin_info_sel
from states.class_states import AdminInfo, AdminDel

from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ParseMode, InputMediaPhoto

from create_bot import dp, bot
from aiogram import types

from database import sqlite_db
from keyboards import goods_add_kb
from states.class_states import AbUs


cancel_all_states = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
cancel_all_states.add(InlineKeyboardButton('Остановить процесс', callback_data="cancel_state_admin"))


admin_info_panel = InlineKeyboardMarkup(row_width=1)
admin_info_panel_kb = [
    [InlineKeyboardButton('Добавить админа', callback_data='admin_add'),
     InlineKeyboardButton('Удалить админа', callback_data='admin_del')],
    [InlineKeyboardButton('Все админы', callback_data='admin_all')],
    [InlineKeyboardButton('Назад ️◀️️', callback_data='admin_back')]
]
for button_row in admin_info_panel_kb:
    admin_info_panel.row(*button_row)


abus_kb = InlineKeyboardMarkup(row_width=2)
admin_panel_kb = InlineKeyboardButton('Админ-панель', callback_data='admin_panel_kb')
admin_panel_kb1 = InlineKeyboardButton('Ассортименты', callback_data='start_kb1')
admin_panel_kb2 = InlineKeyboardButton('О нас ℹ️', callback_data='start_kb2')
admin_panel_kb3 = InlineKeyboardButton('Корзина 🛒', callback_data='start_kb3')
admin_panel_kb4 = InlineKeyboardButton('Оставить отзыв ✍', callback_data='start_kb4')
admin_panel_kb5 = InlineKeyboardButton(text='Баланс 💰', callback_data='start_kb5')
abus_kb.add(admin_panel_kb1)
abus_kb.add(admin_panel_kb2, admin_panel_kb3)
abus_kb.add(admin_panel_kb4, admin_panel_kb5)
abus_kb.add(admin_panel_kb)


@dp.callback_query_handler(lambda c: c.data == 'admin_panel_kb')
async def admin_panel_callback(call: types.CallbackQuery):
    await call.answer('Вы в админ-панели')
    with open('img/admin-panel.jpg', 'rb') as admin_panel_photo:
        media_admin_panel = InputMediaPhoto(admin_panel_photo, caption='<b>Основное меню хранителя:</b>', parse_mode=ParseMode.HTML)
        await bot.edit_message_media(media_admin_panel, call.message.chat.id, call.message.message_id,
                                     reply_markup=admin_panel_browser)


admin_panel_browser = InlineKeyboardMarkup(row_width=2)
admin_panel_browser_kb = [
    InlineKeyboardButton('Сделать рассылку ', callback_data='admin_panel_browser_kb1'),
    InlineKeyboardButton('Изменить "О НАС"', callback_data='admin_panel_browser_kb2'),
    InlineKeyboardButton('Товар удалить/добавить', callback_data='admin_panel_browser_kb3'),
    InlineKeyboardButton('Админ удалить/добавить', callback_data='admin_panel_browser_kb4'),
    InlineKeyboardButton('Назад ◀️', callback_data='abouts_us_back_kb1')
]
admin_panel_browser.add(*admin_panel_browser_kb)


@dp.callback_query_handler(lambda c: c.data.startswith('admin_panel_browser_'))
async def admin_panel_options(call: types.CallbackQuery):
    admin_options = call.data.split('_')[3]

    if admin_options == 'kb1':
        from handlers import admin

        await call.answer('Вы нажали на рассылку')
        message = call.message
        await admin.mailing(message)
    elif admin_options == 'kb2':
        await call.answer('Вы нажали, изменить "О НАС"')
        await call.message.reply('<b>Выберите один из вариантов :</b>', parse_mode=ParseMode.HTML,
                                 reply_markup=about_us)
    elif admin_options == 'kb3':
        await call.answer('Вы нажали на добавить или удалить товар')
        await call.message.reply('<b>Выберите один из вариантов :</b>', parse_mode=ParseMode.HTML,
                                 reply_markup=goods_add_kb.goods_info)
    elif admin_options == 'kb4':
        await call.answer('Вы нажали на добавить/удалить администратора')
        await call.message.reply('<b>Выберите один из вариантов :</b>', parse_mode=ParseMode.HTML,
                                 reply_markup=admin_info_panel)


@dp.callback_query_handler(lambda c: c.data.startswith('admin_'))
async def admin_info_tasks(call: types.CallbackQuery):
    admin_task = call.data.split('_')[1]

    if admin_task == 'add':
        await call.answer('Вы нажали на добавить админа')
        await AdminInfo.admin_id.set()
        await call.message.reply('<b>Пожалуйста отправьте ID админа</b>', parse_mode=ParseMode.HTML, reply_markup=cancel_all_states)
    elif admin_task == 'del':
        await call.answer('Вы нажали на удалить админа')
        await call.answer('Вы нажали на удалить админа')
        await call.message.reply('<b>Введите <b>USERNAME</b> админа</b>', parse_mode=ParseMode.HTML)

        await AdminDel.admin_id.set()
    elif admin_task == 'all':
        await call.answer('Вы нажали на показ всех админов')
        await admin_info_sel(call.message)


@dp.message_handler(state=AdminDel.admin_id)
async def admin_del_info(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['admin_id'] = message.text

    admin_del = await state.get_data()
    admin_id_del = admin_del.get('admin_id')

    if not admin_id_del.startswith('@'):
        admin_id_del = '@' + admin_id_del

    await admin_info_del(admin_id=admin_id_del)
    await message.reply(f'<b><i>{admin_id_del}</i> успешно удален из списка админов ✅</b>', parse_mode=ParseMode.HTML)
    await state.finish()


@dp.message_handler(text='Остановить процесс', state="*")
@dp.message_handler(Text(equals='Остановить процесс', ignore_case=True), state="*")
async def cancel_admin_state(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, '<b>Процесс остановлен. Спасибо за <i>содействия</i></b>',
                           parse_mode=ParseMode.HTML)
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()


@dp.message_handler(state=AdminInfo.admin_id)
async def admin_id_set(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['admin_id'] = message.text
    await message.reply('<b>Теперь введите <i>USERNAME</i> админа</b>', parse_mode=ParseMode.HTML)
    await AdminInfo.next()


@dp.message_handler(state=AdminInfo.admin_username)
async def admin_user_set(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['admin_username'] = message.text

    admin_info = await state.get_data()
    admin_id = admin_info.get('admin_id', None)
    admin_username = admin_info.get('admin_username')

    if not admin_username.startswith('@'):
        admin_username = '@' + admin_username

    await admin_info_add(admin_id, admin_username)
    await message.reply('<b>Данные админа <i>были внесены в БД</i></b>', parse_mode=ParseMode.HTML)
    await state.finish()


about_us = InlineKeyboardMarkup(row_width=2)
about_us_kb1 = InlineKeyboardButton('Добавить', callback_data='about_us_kb1')
about_us_kb2 = InlineKeyboardButton('Удалить', callback_data='about_us_kb2')
about_us.add(about_us_kb1, about_us_kb2)

abouts_us_back = InlineKeyboardMarkup(row_width=2)
abouts_us_back.add(InlineKeyboardButton('Вернуться назад 🏠', callback_data='abouts_us_back_kb1'))


@dp.callback_query_handler(text='abouts_us_back_kb1')
async def abouts_us_back_call(call: types.CallbackQuery):
    from handlers.client import start

    message = call.message
    await start(message)


@dp.callback_query_handler(text='about_us_kb1')
async def about_us_kb1_callback(call: types.CallbackQuery):
    await call.answer('Вы нажали на добавить')
    await bot.send_message(call.message.chat.id,
                           '<b>Пожалуйста введите описание которое вы хотите добавить в бота</b>',
                           parse_mode=ParseMode.HTML)
    await AbUs.abus_info.set()


@dp.message_handler(state=AbUs.abus_info)
async def abus_gotten(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['abus_info'] = message.html_text

    abus_info_get = await state.get_data()
    abus_infos = abus_info_get.get('abus_info')

    await bot.send_message(message.chat.id, '<b>Текст успешно сохранен</b>', parse_mode=ParseMode.HTML, reply_markup=abouts_us_back)

    await state.finish()
    await sqlite_db.abus_sql(abus_infos)


@dp.callback_query_handler(text='about_us_kb2')
async def about_us_del(call: types.CallbackQuery):
    print("Callback 'about_us_kb2' triggered")
    await call.answer('Вы нажали удалить о себе')
    await bot.send_message(call.message.chat.id, '<b>Все данные из <i>БД</i> были <i>успешно стёрты</i></b>', parse_mode=ParseMode.HTML, reply_markup=abouts_us_back)
    await sqlite_db.del_abus_sql()


@dp.callback_query_handler(lambda c: c.data.startswith('part_'))
async def part_process_callback(call: types.CallbackQuery):
    part_type = call.data.split('_')[1]

    if part_type == 'periphery':
        await call.message.edit_text('<b>Выберите тип периферии:</b>', parse_mode=ParseMode.HTML, reply_markup=type_of_element_periphery)
    elif part_type == 'components':
        await call.message.edit_text('<b>Выберите тип компонента:</b>', parse_mode=ParseMode.HTML, reply_markup=type_of_element_components)
    elif part_type == 'decor':
        await call.message.edit_text('<b>Выберите тип декора:</b>', parse_mode=ParseMode.HTML, reply_markup=type_of_element_decor)
    else:
        await call.message.reply('Неверный выбор. Пожалуйста, попробуйте снова.')


# Клавиатуры
type_of_element_goods = InlineKeyboardMarkup(row_width=2)
type_of_element_goods_buttons = [
    InlineKeyboardButton('Периферия', callback_data='part_periphery'),
    InlineKeyboardButton('Комплектующие', callback_data='part_components'),
    InlineKeyboardButton('Дэкор', callback_data='part_decor')
]
type_of_element_goods.add(*type_of_element_goods_buttons)


type_of_element_components = InlineKeyboardMarkup(row_width=2)
type_of_element_components_buttons = [
    InlineKeyboardButton('Материнские платы', callback_data='type_mb'),
    InlineKeyboardButton('Процессоры', callback_data='type_cpu'),
    InlineKeyboardButton('Блоки питания', callback_data='type_psu'),
    InlineKeyboardButton('ОЗУ', callback_data='type_ram'),
    InlineKeyboardButton('Видеокарты', callback_data='type_gpu'),
    InlineKeyboardButton('SSD-накопители', callback_data='type_ssd'),
    InlineKeyboardButton('Жесткие диски', callback_data='type_hdd'),
    InlineKeyboardButton('Кулера', callback_data='type_cooler'),
    InlineKeyboardButton('Назад ️◀️', callback_data='type_back')
]
type_of_element_components.add(*type_of_element_components_buttons)


type_of_element_periphery = InlineKeyboardMarkup(row_width=2)
type_of_element_periphery_buttons = [
    InlineKeyboardButton('Мониторы', callback_data='type_scr'),
    InlineKeyboardButton('Клавиатуры', callback_data='type_kb'),
    InlineKeyboardButton('Мышки', callback_data='type_ms'),
    InlineKeyboardButton('Коврики', callback_data='type_crpt'),
    InlineKeyboardButton('Наушники', callback_data='type_hdp'),
    InlineKeyboardButton('Корпуса', callback_data='type_corpus'),
    InlineKeyboardButton('Назад ️◀️', callback_data='type_back')
]
type_of_element_periphery.add(*type_of_element_periphery_buttons)


type_of_element_decor = InlineKeyboardMarkup(row_width=2)
type_of_element_decor_buttons = [
    InlineKeyboardButton('Подсветки', callback_data='type_light'),
    InlineKeyboardButton('Лампы', callback_data='type_lamp'),
    InlineKeyboardButton('Плакат', callback_data='type_poster'),
    InlineKeyboardButton('Игрушки', callback_data='type_toys'),
    InlineKeyboardButton('Назад ️◀️', callback_data='type_back'),
]
type_of_element_decor.add(*type_of_element_decor_buttons)
