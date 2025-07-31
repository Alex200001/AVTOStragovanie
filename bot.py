
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import logging

BOT_TOKEN = "ВСТАВЬ_СЮДА_СВОЙ_ТОКЕН"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

user_data = {}

kb = ReplyKeyboardMarkup(resize_keyboard=True)
kb.add(KeyboardButton("Рассчитать ОСАГО"))

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer("Здравствуйте! Нажмите кнопку для расчёта ОСАГО:", reply_markup=kb)

@dp.message_handler(lambda m: m.text == "Рассчитать ОСАГО")
async def ask_region(msg: types.Message):
    user_data[msg.from_user.id] = {"step": "region"}
    await msg.answer("Введите ваш регион (например: Москва):")

@dp.message_handler(lambda m: user_data.get(m.from_user.id, {}).get("step") == "region")
async def handle_region(msg: types.Message):
    user_data[msg.from_user.id]["region"] = msg.text
    user_data[msg.from_user.id]["step"] = "power"
    await msg.answer("Введите мощность автомобиля в л.с.:")

@dp.message_handler(lambda m: user_data.get(m.from_user.id, {}).get("step") == "power")
async def handle_power(msg: types.Message):
    try:
        power = int(msg.text)
        user_data[msg.from_user.id]["power"] = power
        user_data[msg.from_user.id]["step"] = "age"
        await msg.answer("Введите возраст водителя:")
    except ValueError:
        await msg.answer("Пожалуйста, введите число (мощность в л.с.):")

@dp.message_handler(lambda m: user_data.get(m.from_user.id, {}).get("step") == "age")
async def handle_age(msg: types.Message):
    try:
        age = int(msg.text)
        user_data[msg.from_user.id]["age"] = age
        user_data[msg.from_user.id]["step"] = "kbm"
        await msg.answer("Введите КБМ (например: 1.0 если без аварий):")
    except ValueError:
        await msg.answer("Пожалуйста, введите возраст числом.")

@dp.message_handler(lambda m: user_data.get(m.from_user.id, {}).get("step") == "kbm")
async def handle_kbm(msg: types.Message):
    try:
        kbm = float(msg.text)
        user_data[msg.from_user.id]["kbm"] = kbm

        # Расчёт ОСАГО
        base_rate = 4118  # Базовый тариф
        power = user_data[msg.from_user.id]["power"]
        age = user_data[msg.from_user.id]["age"]
        region = user_data[msg.from_user.id]["region"].lower()
        kbm = user_data[msg.from_user.id]["kbm"]

        # Коэффициенты
        if power < 50:
            k_power = 0.6
        elif 50 <= power <= 70:
            k_power = 1.0
        elif 71 <= power <= 100:
            k_power = 1.1
        elif 101 <= power <= 120:
            k_power = 1.2
        elif 121 <= power <= 150:
            k_power = 1.4
        else:
            k_power = 1.6

        k_age = 1.0 if age >= 35 else 1.8

        if "москва" in region:
            k_region = 2.0
        elif "спб" in region or "петербург" in region:
            k_region = 1.8
        else:
            k_region = 1.0

        final_price = round(base_rate * k_power * k_age * kbm * k_region, 2)

        await msg.answer(f"Примерная стоимость ОСАГО: {final_price} ₽")
        user_data.pop(msg.from_user.id, None)

    except ValueError:
        await msg.answer("Пожалуйста, введите корректное значение КБМ.")

if __name__ == "__main__":
    executor.start_polling(dp)
