from aiogram import executor
from create_bot import dp
from handlers import client, admin
from database import sqlite_db

client.register_handlers_client(dp)
admin.register_handlers_admin(dp)

if __name__ == '__main__':
    print('Bot started')
    executor.start_polling(dp, skip_updates=True, on_startup=sqlite_db.sql_start())