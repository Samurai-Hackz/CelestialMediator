from aiogram.dispatcher.filters.state import StatesGroup, State

# Admin file STATES


class AbUs(StatesGroup):
    abus_info = State()


class FSMAdmin(StatesGroup):
    photo = State()
    desc = State()

# Client kb STATES


class DataInfo(StatesGroup):
    text_answer = State()


class ItemInfo(StatesGroup):
    item_id = State()
    item_photo = State()
    item_name = State()
    item_type = State()
    item_desc = State()
    item_price = State()


class DelInfoAboutUs(StatesGroup):
    item_num = State()


class Form(StatesGroup):
    page = State()  # Состояние для отслеживания текущей страницы


class AdminInfo(StatesGroup):
    admin_id = State()
    admin_username = State()


class AdminDel(StatesGroup):
    admin_id = State()


class AmountOfPayment(StatesGroup):
    bill = State()
