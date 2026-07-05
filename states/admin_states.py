from aiogram.fsm.state import State, StatesGroup


class AddMovie(StatesGroup):
    category = State()          # kino / multfilm / serial tanlash
    choose_series = State()     # serial tanlanganda - mavjud serial yoki yangi
    new_series_title = State()  # yangi serial nomi
    name = State()              # kino/multfilm nomi YOKI serial qismi nomi (masalan "1-qism")
    video = State()
    format = State()
    language = State()
    subtitle = State()
    code = State()


class EditMovie(StatesGroup):
    choose_item = State()   # kod yuborish orqali kino/qism topish
    choose_field = State()
    new_value = State()
    new_video = State()


class DeleteMovie(StatesGroup):
    choose_item = State()


class SeriesManage(StatesGroup):
    rename_title = State()


class AddChannel(StatesGroup):
    waiting_forward_or_username = State()


class RemoveChannel(StatesGroup):
    choose_channel = State()


class AddAdmin(StatesGroup):
    waiting_id = State()


class RemoveAdmin(StatesGroup):
    choose_admin = State()


class Broadcast(StatesGroup):
    waiting_content = State()
    confirm = State()
