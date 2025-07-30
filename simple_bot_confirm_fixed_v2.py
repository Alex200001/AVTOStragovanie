
import logging
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

BOT_TOKEN = "8464667567:AAF4rkhK4QHpOhtqpLPpe5PDnEvRfa94t1w"
ADMIN_ID = 1195423197


logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

confirm_kb = InlineKeyboardMarkup().add(
    InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
    InlineKeyboardButton("🔁 Изменить", callback_data="edit")
)

service_kb = ReplyKeyboardMarkup(resize_keyboard=True)
service_kb.add(KeyboardButton("ОСАГО"), KeyboardButton("КАСКО"))

nav_kb = ReplyKeyboardMarkup(resize_keyboard=True)
nav_kb.add(KeyboardButton("❌ Сбросить"), KeyboardButton("🔙 Назад"))

user_data = {}
user_step = {}

steps = ["service", "name", "phone", "car", "year", "region"]
prompts = {
    "service": "Что вас интересует: ОСАГО или КАСКО?",
    "name": "Введите ваше имя:",
    "phone": "Введите ваш номер телефона:",
    "car": "Марка и модель авто:",
    "year": "Год выпуска авто:",
    "region": "Регион проживания:"
}

@dp.message_handler(commands=["start", "reset"])
async def start(msg: types.Message):
    uid = msg.from_user.id
    user_data[uid] = {}
    user_step[uid] = 0
    await msg.answer("Здравствуйте! " + prompts["service"], reply_markup=service_kb)

@dp.message_handler(lambda msg: msg.text == "❌ Сбросить")
async def reset(msg: types.Message):
    uid = msg.from_user.id
    user_data.pop(uid, None)
    user_step.pop(uid, None)
    await start(msg)

@dp.message_handler(lambda msg: msg.text == "🔙 Назад")
async def go_back(msg: types.Message):
    uid = msg.from_user.id
    if uid in user_step and user_step[uid] > 0:
        user_step[uid] -= 1
        step_key = steps[user_step[uid]]
        kb = service_kb if step_key == "service" else nav_kb
        await msg.answer(f"🔙 {prompts[step_key]}", reply_markup=kb)
    else:
        await msg.answer("Вы уже на первом шаге.", reply_markup=nav_kb)

@dp.message_handler()
async def handle_input(msg: types.Message):
    uid = msg.from_user.id
    if uid not in user_step:
        await start(msg)
        return

    step_index = user_step[uid]
    step_key = steps[step_index]
    text = msg.text.strip()

    if step_key == "service" and text not in ["ОСАГО", "КАСКО"]:
        await msg.answer("Пожалуйста, выберите ОСАГО или КАСКО из кнопок.")
        return

    if step_key == "phone" and not re.fullmatch(r'\+7\d{10}', text):
        await msg.answer("❗ Пожалуйста, введите номер в формате +7XXXXXXXXXX")
        return

    if step_key == "year" and not re.fullmatch(r'\d{4}', text):
        await msg.answer("❗ Пожалуйста, введите корректный год выпуска (4 цифры).")
        return

    user_data[uid][step_key] = text
    user_step[uid] += 1

    if user_step[uid] >= len(steps):
        data = user_data[uid]
        summary = (
            f"📄 Заявка:\n"
            f"🔹 Услуга: {data['service']}\n"
            f"👤 Имя: {data['name']}\n"
            f"📞 Телефон: {data['phone']}\n"
            f"🚘 Авто: {data['car']}\n"
            f"📆 Год: {data['year']}\n"
            f"🌍 Регион: {data['region']}"
        )
        user_data[uid] = {"summary": summary}
        await msg.answer(summary + "\n\n✅ Подтвердить или 🔁 Изменить?", reply_markup=confirm_kb)
    else:
        next_key = steps[user_step[uid]]
        kb = service_kb if next_key == "service" else nav_kb
        await msg.answer(f"(Шаг {user_step[uid]+1} из {len(steps)})\n{prompts[next_key]}", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data in ["confirm", "edit"])
async def process_confirmation(callback: types.CallbackQuery):
    uid = callback.from_user.id
    if callback.data == "confirm":
        summary = user_data.pop(uid, {}).get("summary", "")
        await bot.send_message(ADMIN_ID, summary)
        await callback.message.edit_text("📄 Анкета успешно отправлена!\n✅ Спасибо, мы с вами свяжемся.")
        await bot.send_message(uid, "Вы можете начать заново с /start", reply_markup=ReplyKeyboardRemove())
    else:
        await callback.message.edit_text("🔁 Вы можете изменить данные. Введите /start для новой анкеты.")
        user_data.pop(uid, None)
        user_step.pop(uid, None)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
