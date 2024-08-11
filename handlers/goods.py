from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode

from create_bot import bot, dp
from aiogram import types

from keyboards.admin_kb import type_of_element_periphery, type_of_element_components, type_of_element_decor, \
    type_of_element_goods
from states.class_states import ItemInfo

from database import sqlite_db

from keyboards import client_kb, goods_add_kb
from keyboards import admin_kb


@dp.message_handler(state=None)
async def add_callback_kb(message: types.Message):
    await ItemInfo.item_photo.set()
    await message.reply('<b>Отправьте фото товара</b>', parse_mode=ParseMode.HTML, reply_markup=client_kb.go_back_start_kb)


@dp.message_handler(content_types=['photo'], state=ItemInfo.item_photo)
async def item_photo_state(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['item_photo'] = message.photo[0].file_id
    await ItemInfo.next()
    await message.reply('<b>Теперь введите название товара</b>', parse_mode=ParseMode.HTML)


@dp.message_handler(state=ItemInfo.item_name)
async def item_name_state(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['item_name'] = message.text
        print(f"Item name set: {data['item_name']}")
    await message.reply('<b>Теперь введите тип товара</b>', parse_mode=ParseMode.HTML, reply_markup=admin_kb.type_of_element_goods)
    await ItemInfo.next()


@dp.callback_query_handler(lambda c: c.data.startswith(('part_', 'type_')), state=ItemInfo.item_type)
async def process_item_type(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split('_')
    if data[0] == 'part':
        part_type = data[1]
        if part_type == 'periphery':
            await call.message.edit_text('<b>Выберите тип периферии:</b>', parse_mode=ParseMode.HTML, reply_markup=type_of_element_periphery)
        elif part_type == 'components':
            await call.message.edit_text('<b>Выберите тип компонента:</b>', parse_mode=ParseMode.HTML, reply_markup=type_of_element_components)
        elif part_type == 'decor':
            await call.message.edit_text('<b>Выберите тип декора:</b>', parse_mode=ParseMode.HTML, reply_markup=type_of_element_decor)
        else:
            await call.message.reply('Неверный выбор. Пожалуйста, попробуйте снова.')
        async with state.proxy() as data:
            data['item_type'] = part_type
            print(f"Item type set: {data['item_type']}")
    elif data[0] == 'type':
        item_type = data[1]
        if item_type == 'back':
            await bot.send_message(call.message.chat.id, '<b>Ассортименты</b>', reply_markup=type_of_element_goods)
        async with state.proxy() as data:
            data['item_type'] = item_type
            print(f"Item type set: {data['item_type']}")
        await call.message.reply('<b>Теперь введите описание товара</b>', parse_mode=ParseMode.HTML)
        await ItemInfo.next()
    else:
        await call.message.reply('Неверный выбор. Пожалуйста, попробуйте снова.')


@dp.message_handler(state=ItemInfo.item_desc)
async def item_desc_state(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['item_desc'] = message.text
    await ItemInfo.next()
    await message.reply('<b>Теперь введите цену товара</b>', parse_mode=ParseMode.HTML)


@dp.message_handler(state=ItemInfo.item_price)
async def item_price_state(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['item_price'] = message.text

    await message.reply('<b>Данные <i>успешно сохранены ✅</i>\n\nХотите еще что-нибудь <i>добавить</i> или <i>удалить</i>?</b>', parse_mode=ParseMode.HTML, reply_markup=goods_add_kb.goods_info)

    item_infos = await state.get_data()
    item_photo_add = item_infos.get('item_photo')
    item_name_add = item_infos.get('item_name')
    item_type_add = item_infos.get('item_type')
    item_desc_add = item_infos.get('item_desc')
    item_price_add = item_infos.get('item_price')

    await sqlite_db.goods_sql_add(item_photo_add, item_type_add, item_name_add, item_desc_add, item_price_add)
    await state.finish()

