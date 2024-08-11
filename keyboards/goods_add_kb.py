from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, InputMediaPhoto

from database.sqlite_db import cur, base
from states.class_states import DelInfoAboutUs

from create_bot import dp, bot
from database import sqlite_db


ADMIN_ID = [2043495890, 167628351, 7079102289]

goods_info = InlineKeyboardMarkup(row_width=2)
good_add = InlineKeyboardButton('Добавить товар', callback_data='good_add')
good_del = InlineKeyboardButton('Удалить товар', callback_data='good_del')
good_show = InlineKeyboardButton('Показать все товары', callback_data='showall_goods')
good_back = InlineKeyboardButton('Назад ◀️', callback_data='abouts_us_back_kb1')
goods_info.add(good_add, good_del)
goods_info.add(good_show)
goods_info.add(good_back)


@dp.callback_query_handler(text='back_to_categories')
async def back_to_categories(call: types.CallbackQuery):
    from keyboards.client_kb import menu_list
    await call.answer('Вы нажали назад')

    back_to_categories_media_photo = InputMediaPhoto(open('img/goods.jpg', 'rb'), '<b>Ассортименты : </b>', parse_mode=ParseMode.HTML)
    await bot.edit_message_media(media=back_to_categories_media_photo, chat_id=call.message.chat.id,
                                 message_id=call.message.message_id,
                                 reply_markup=menu_list)


@dp.callback_query_handler(text='good_add')
async def add_kb(call: types.CallbackQuery):
    from handlers.goods import add_callback_kb

    message = call.message
    await add_callback_kb(message)
    await call.answer('Вы нажали добавить товар')


@dp.callback_query_handler(text='good_del')
async def del_kb(call: types.CallbackQuery):
    await call.answer('Вы нажали на удалить товар')
    await call.message.reply('<b>Теперь введите номер товара который, вы хотите удалить</b>', parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton('Удалить все значения', callback_data="del_all_goods"), InlineKeyboardButton('Назад ◀', callback_data='admin_menu_back')))
    await DelInfoAboutUs.item_num.set()


@dp.callback_query_handler(text='del_all_goods')
async def del_kb_all(call: types.CallbackQuery):
    await call.answer('Все значения удалены', show_alert=True)

    print("Выполнение: DELETE FROM goods")
    cur.execute('DELETE FROM goods')
    base.commit()


@dp.callback_query_handler(text='admin_menu_back')
async def admin_menu_list_back(call: types.CallbackQuery):
    await call.answer('Вы нажали назад')
    await bot.edit_message_text('Выберите один из вариантов :', call.message.chat.id, call.message.message_id, reply_markup=goods_info)


@dp.message_handler(state=DelInfoAboutUs.item_num)
async def del_info_about_us(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['item_num'] = message.text

    state_del_num = await state.get_data()
    state_del_int = state_del_num.get('item_num')
    print(f"Значение ключа равно : {state_del_int}")
    await sqlite_db.goods_sql_del(state_del_int)

    await message.reply('<b>Данные успешно удалены\n\nХотите еще что-нибудь добавить/удалить ?</b>',
                        parse_mode=ParseMode.HTML,
                        reply_markup=goods_info)
    await state.finish()


@dp.callback_query_handler(text='showall_goods')
async def show_all_goods_data(call: types.CallbackQuery):
    await call.answer('Вы нажали на показать все значения')
    await sqlite_db.cycle_sql_goods(message=call.message)


menu_type_func_user = InlineKeyboardMarkup(row_width=1)
menu_type_func_back = InlineKeyboardButton('Назад ◀️', callback_data='menu_list_back')
menu_type_func_user.add(menu_type_func_back)

menu_type_func_admin = InlineKeyboardMarkup(row_width=1)
menu_type_func_del = InlineKeyboardButton('Удалить 🔽', callback_data='menu_type_func_del')
menu_type_func_back = InlineKeyboardButton('Назад ◀️', callback_data='menu_list_back')
menu_type_func_admin.add(menu_type_func_del, menu_type_func_back)


@dp.callback_query_handler(lambda c: c.data.startswith('view_cart_'))
async def add_to_cart(callback_query: types.CallbackQuery):
    from database.sqlite_db import add_cart_info

    await callback_query.answer("Товар добавлен в корзину!", show_alert=True)

    product_id = int(callback_query.data.split('_')[2])
    user_id = callback_query.from_user.id

    # Добавление товара в корзину пользователя
    await add_cart_info(user_id, product_id)


def get_pagination_keyboard(current_page, total_pages, menu_type_get, product_id):
    keyboard = InlineKeyboardMarkup()

    prev_button = None
    next_button = None
    cart_button = InlineKeyboardButton('Добавить в корзину 🛒', callback_data=f'view_cart_{product_id}')

    if current_page > 1:
        prev_button = InlineKeyboardButton('◀️ Назад', callback_data=f'page_{menu_type_get}_{current_page - 1}')
    if current_page < total_pages:
        next_button = InlineKeyboardButton('Вперёд ▶️', callback_data=f'page_{menu_type_get}_{current_page + 1}')

    if total_pages > 1:
        if prev_button and next_button:
            keyboard.add(prev_button, next_button)
        elif prev_button:
            keyboard.add(prev_button)
        elif next_button:
            keyboard.add(next_button)
    else:
        if prev_button:
            keyboard.add(prev_button)
        if next_button:
            keyboard.add(next_button)

    back_button = InlineKeyboardButton('Комлектующие ⚙', callback_data='back_to_categories')
    keyboard.add(back_button)
    keyboard.add(cart_button)

    return keyboard


@dp.callback_query_handler(lambda c: c.data.startswith('menutype_'))
async def process_menu_type(call: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(
        callback_query_id=call.id,
        text=f'Вы выбрали категорию: {call.data.split("_")[1]}',
        show_alert=False
    )

    menu_type_get = call.data.split('_')[1]
    print(f"Отладка : {menu_type_get}")

    cur.execute('SELECT COUNT(*) FROM goods WHERE item_type=?', (menu_type_get,))
    total_items = cur.fetchone()[0]
    items_per_page = 1
    total_pages = (total_items + items_per_page - 1) // items_per_page

    current_page = 1

    await state.update_data(total_pages=total_pages, items_per_page=items_per_page, menu_type_get=menu_type_get,
                            current_page=current_page)

    offset = (current_page - 1) * items_per_page
    cur.execute(
        'SELECT item_id, item_photo, item_name, item_desc, item_price FROM goods WHERE item_type=? LIMIT ? OFFSET ?',
        (menu_type_get, items_per_page, offset))
    get_whole_menu = cur.fetchall()

    if get_whole_menu:
        for get_whole_menus in get_whole_menu:
            try:
                item_id, item_photo, item_name, item_desc, item_price = get_whole_menus
                caption = f"<b><i>{item_name}</i></b>\n\n{item_desc}\n\n<b>Цена: {item_price}</b>"

                media_photo = InputMediaPhoto(item_photo, caption=caption, parse_mode=ParseMode.HTML)
                await bot.edit_message_media(media=media_photo, chat_id=call.message.chat.id,
                                             message_id=call.message.message_id,
                                             reply_markup=get_pagination_keyboard(current_page, total_pages,
                                                                                  menu_type_get, item_id))
            except Exception as e:
                print(f"Ошибка при отправке фото: {e}")
    else:
        await bot.send_message(call.message.chat.id, "Нет данных для отображения")


@dp.callback_query_handler(lambda c: c.data.startswith('page_'))
async def process_pagination(call: types.CallbackQuery, state: FSMContext):
    await call.answer('Вы нажали вперед')

    menu_type_get = call.data.split('_')[1]
    total_items = cur.execute('SELECT COUNT(*) FROM goods WHERE item_type=?', (menu_type_get,)).fetchone()[0]
    items_per_page = 1
    total_pages = (total_items + items_per_page - 1) // items_per_page

    current_page = int(call.data.split('_')[2])

    offset = (current_page - 1) * items_per_page
    cur.execute('SELECT item_id, item_photo, item_name, item_desc, item_price FROM goods WHERE item_type=? LIMIT ? OFFSET ?', (menu_type_get, items_per_page, offset))
    get_whole_menu = cur.fetchall()

    if get_whole_menu:
        for get_whole_menus in get_whole_menu:
            try:
                item_id, item_photo, item_name, item_desc, item_price = get_whole_menus

                if call.message.photo:
                    await bot.edit_message_media(
                        media=types.InputMediaPhoto(
                            media=item_photo,
                            caption=f"<b><i>{item_name}</i>\n\n{item_desc}\n\nЦена: {item_price}</b>",
                            parse_mode=ParseMode.HTML),
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        reply_markup=get_pagination_keyboard(current_page, total_pages, menu_type_get, item_id)
                    )
                else:
                    await call.message.edit_text(
                        text=f"<b><i>{item_name}</i>\n\n{item_desc}\n\nЦена: {item_price}</b>",
                        parse_mode=ParseMode.HTML,
                        reply_markup=get_pagination_keyboard(current_page, total_pages, menu_type_get, item_id)
                    )
            except Exception as e:
                print(f"Ошибка при обновлении фото: {e}")
    else:
        try:
            await call.message.edit_text("Нет данных для отображения")
        except Exception as e:
            print(f"Ошибка при редактировании текста сообщения: {e}")

    await state.update_data(current_page=current_page)
    await bot.answer_callback_query(call.id)