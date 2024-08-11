import os
import sqlite3 as sq

from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton

import keyboards.client_kb
from create_bot import bot

base = sq.connect('base.db')
cur = base.cursor()


def sql_start():
    global base, cur
    # cur.execute('DROP TABLE IF EXISTS users')
    if base:
        print('Database opened')
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        username TEXT,
        account INTEGER DEFAULT 0
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS mails (
        photo TEXT,
        desc TEXT
    )""")
    cur.execute("""
               CREATE TABLE IF NOT EXISTS others (
                   text_id INTEGER PRIMARY KEY,
                   about_us_text VARCHAR(255)
               )
           """)
    cur.execute("""
                CREATE TABLE IF NOT EXISTS goods (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT ,
                    item_type VARCHAR, 
                    item_photo TEXT,
                    item_name VARCHAR,
                    item_desc VARCHAR(500),
                    item_price TEXT
                )
            """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_cart (
            user_id INTEGER,
            item_id INTEGER,
            item_price VARCHAR(6),
            PRIMARY KEY (user_id, item_id),
            FOREIGN KEY (item_id) REFERENCES goods(item_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admin_info (
            admin_id INTEGER PRIMARY KEY,
            admin_username TEXT
        )
    """)
    base.commit()


def sqlite_start(user_id, name, username):
    try:
        existing_user = cur.execute("SELECT * FROM users WHERE user_id=?", (user_id, )).fetchone()

        if existing_user:
            print(f'Данный пользователь с user_id={user_id} уже существует в базе данных')
        else:
            cur.execute("INSERT INTO users(user_id, name, username) VALUES(?, ?, ?)", (user_id, name, username))
            base.commit()
    except sq.IntegrityError as e:
        print(f"Ошибка IntegrityError при добавлении пользователя: {e}")


async def abus_sql(abustext):
    cur.execute('INSERT INTO others(about_us_text) VALUES (?)', (abustext,))
    base.commit()


async def del_abus_sql(condition=None):
    if condition:
        cur.execute('DELETE FROM others WHERE text_id=?', (condition,))
    else:
        cur.execute('DELETE FROM others')
    base.commit()


async def onas_sql(call):
    onas_infos = cur.execute('SELECT about_us_text FROM others').fetchall()
    for onas_info in onas_infos:
        start_info_onas = onas_info[0]
        await call.message.reply(f"{start_info_onas.replace('[]', ' ')}", parse_mode=ParseMode.HTML)


async def goods_sql_add(item_photo, item_type, item_name, item_desc, item_price):
    cur.execute("INSERT INTO goods(item_photo, item_type, item_name, item_desc, item_price) VALUES (?, ?, ?, ?, ?)", (item_photo, item_type, item_name, item_desc, item_price))
    base.commit()


async def goods_sql_del(queue_num=None):
    print(f"Received queue_num: {queue_num} (type: {type(queue_num)})")

    if queue_num:
        print(f"Executing: DELETE FROM goods WHERE item_id={queue_num}")
        cur.execute('DELETE FROM goods WHERE item_id=?', (queue_num,))
        cur.execute('UPDATE sqlite_sequence SET seq = 1 WHERE name = "goods"')
    else:
        print("Executing: DELETE FROM goods")
        cur.execute('DELETE FROM goods')

    cur.execute('DELETE FROM sqlite_sequence WHERE name = "goods"')
    cur.execute('''
                UPDATE goods
                SET item_id = (
                    SELECT COUNT(*)
                    FROM goods AS g2
                    WHERE g2.item_id <= goods.item_id
                )
            ''')
    base.commit()


async def cycle_sql_goods(message):
    goods_cycle = cur.execute("SELECT item_id, item_name FROM goods").fetchall()

    if goods_cycle:
        response_goods_info = "<b>Все данные :\n\n</b>"
        for good_cycle in goods_cycle:
            item_id, item_name = good_cycle
            response_goods_info += f"<b>{item_id}: <i>{item_name}</i></b>\n"
        await message.reply(response_goods_info, parse_mode=ParseMode.HTML)
    else:
        await message.reply("<b>Значения отсутствуют</b>", parse_mode=ParseMode.HTML)


async def add_cart_info(user_id, item_id):
    try:
        # Получаем цену товара из таблицы goods
        cur.execute('SELECT item_price FROM goods WHERE item_id = ?', (item_id,))
        item_price = cur.fetchone()

        if item_price is None:
            print(f"Товар с item_id = {item_id} не найден.")
            return

        item_price = item_price[0]

        # Проверяем наличие записи
        cur.execute('SELECT COUNT(*) FROM user_cart WHERE user_id = ? AND item_id = ?', (user_id, item_id))
        count = cur.fetchone()[0]

        if count == 0:
            # Если запись не существует, добавляем новую
            cur.execute('''
                    INSERT INTO user_cart (user_id, item_id, item_price) VALUES (?, ?, ?)
                ''', (user_id, item_id, item_price))
        else:
            # Если запись существует, обновляем цену товара
            cur.execute('''
                    UPDATE user_cart SET item_price = ? WHERE user_id = ? AND item_id = ?
                ''', (item_price, user_id, item_id))

        base.commit()
    except sq.Error as e:
        print(f"Ошибка при добавлении товара в корзину: {e}")


async def basket_get(message, user_id):
    users_info_cart = cur.execute('''
        SELECT uc.item_id, g.item_name, uc.item_price 
        FROM user_cart uc
        JOIN goods g ON uc.item_id = g.item_id
        WHERE uc.user_id = ?
    ''', (user_id,)).fetchall()

    if not users_info_cart:
        await bot.send_message(message.chat.id, "<b>Ваша корзина <i>пуста ♻️</i></b>", parse_mode=ParseMode.HTML)
        return 0

    total_sum = 0

    cart_text = "<b>Ваш <i>общий счет</i> :</b>\n\n"
    for item in users_info_cart:
        item_id, item_name, item_price = item
        cleaned_price = item_price.replace(' ', '').replace('сум', '').replace('руб', '').replace(",", ".")
        try:
            price = float(cleaned_price)
        except ValueError:
            await bot.send_message(message.chat.id, f"Ошибка обработки цены для товара: {item_name}. Цена: {item_price:,.2f}")
            return 0

        cart_text += f"<i>• {item_name}: <b>{price:,.2f} сум</b></i>\n"
        total_sum += price

    cart_text += f"\n<b>Итого: <i>{total_sum:,.2f} сум</i></b>"

    await bot.send_message(message.chat.id, cart_text, parse_mode='HTML', reply_markup=keyboards.client_kb.reset_data_cart)

    return total_sum


async def process_payment(user_id, message):
    await message.delete()
    total_sum = await basket_get(message, user_id)

    if total_sum == 0:
        return

    result = [results[0] for results in cur.execute("SELECT account FROM users WHERE user_id=?", (user_id,)).fetchall()]

    if result:
        user_balance = result[0]
        if user_balance >= total_sum:
            new_balance = user_balance - total_sum
            cur.execute("UPDATE users SET account = ? WHERE user_id = ?", (new_balance, user_id))
            base.commit()
            await bot.send_message(message.chat.id,
                f"<b>Оплата прошла успешно! Сумма {total_sum:,.2f} сум была списана с вашего счета.</b>\n"
                f"<b>Ваш новый баланс: {new_balance:,.2f} сум</b>", parse_mode=ParseMode.HTML)
        else:
            await bot.send_message(message.chat.id,
                                f"<b>Недостаточно средств на счете. Ваш текущий баланс: {user_balance:,.2f} сум</b>",
                                parse_mode=ParseMode.HTML,
                                reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton('Удалить сообщение', callback_data='delete_balance_info')))
    else:
        await bot.send_message(message.chat.id, "Ошибка: Пользователь не найден в базе данных.", parse_mode=ParseMode.HTML)


async def res_data_from_cart(user_id, message):
    cur.execute('DELETE FROM user_cart WHERE user_id=?', (user_id, ))
    await message.delete()
    base.commit()


async def admin_info_add(admin_id, admin_username):
    cur.execute("INSERT INTO admin_info (admin_id, admin_username) VALUES (?, ?)", (admin_id, admin_username,))
    base.commit()


async def admin_info_del(admin_id):
    cur.execute("DELETE FROM admin_info WHERE admin_username = ?", (admin_id, ))
    base.commit()


async def admin_info_sel(message):
    admin_lists = cur.execute("SELECT admin_id, admin_username FROM admin_info").fetchall()
    admin_list_text = '<b>Список админов :</b>\n\n'
    for admin_list in admin_lists:
        admin_id, admin_username = admin_list
        admin_list_text += f'<b>Админ : <i>{admin_username}</i></b>\n'
    await message.reply(f'{admin_list_text}', parse_mode=ParseMode.HTML)

    if not admin_lists:
        await message.reply('<b>Админ лист пуст ♻️</b>', parse_mode=ParseMode.HTML)
        return


async def admin_info_select():
    admin_select = cur.execute('SELECT admin_id FROM admin_info').fetchall()
    if not admin_select:
        print('Нету админ данных')


async def show_ballance(user_id, message):
    balance_data = cur.execute("SELECT account FROM users WHERE user_id=?", (user_id, )).fetchone()
    print(balance_data)
    for balance in balance_data:
        if balance is None:
            await message.reply(f'<b>Ваш баланс составляет : 0 сум\n\nДля пополнения своего баланса нажмите на кнопку ниже</b>',
                                parse_mode=ParseMode.HTML,
                                reply_markup=keyboards.client_kb.update_balance)
        else:
            await message.reply(
                f'<b>Ваш баланс составляет : {balance_data}\n\nДля пополнения своего баланса нажмите на кнопку ниже</b>',
                parse_mode=ParseMode.HTML,
                reply_markup=keyboards.client_kb.update_balance)


async def bank_counter(amount_of_money, user_id, message):
    account_score = cur.execute("SELECT account FROM users WHERE user_id=?", (user_id, )).fetchone()[0]
    payment_info = message.successful_payment
    amount = payment_info.total_amount / 100

    if not account_score:
        cur.execute('INSERT INTO users (account) VALUES (?)', (amount_of_money, ))
    else:
        new_balance = account_score + amount
        cur.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    base.commit()
