import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

logging.basicConfig(level=logging.INFO)

# ===== ДАННЫЕ =====
BOT_TOKEN = "8772261504:AAGWKUwnsLR2bWXEZK9mL9PH9UA0NVz-keQ"
GROUP_ID = -1004442464434
# ==================

# Настройка бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

banned_users = set()

class Form(StatesGroup):
    waiting_for_carrots = State()
    waiting_for_device = State()
    waiting_for_discord = State()
    waiting_for_roblox = State()
    waiting_for_farm_amount = State() # Новый этап
    waiting_for_proof = State()

# --- Клавиатуры ---
def get_yes_no_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="yes"),
         InlineKeyboardButton(text="❌ Нет", callback_data="no")]
    ])

def get_moderation_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{user_id}"),
         InlineKeyboardButton(text="❌ Отказать", callback_data=f"reject_{user_id}")],
        [InlineKeyboardButton(text="🚫 Забанить", callback_data=f"ban_{user_id}")]
    ])

# --- Хендлеры ---

@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    if message.from_user.id in banned_users:
        await message.answer("⛔️ Вы заблокированы.")
        return
        
    start_text = (
        "👋 <b>Добро пожаловать в клан!</b>\n\n"
        "Чтобы подать заявку, ответьте на несколько вопросов:\n\n"
        "🥕 <b>Вопрос 1: Сколько сейчас моркови имеете?</b>"
    )
    
    await message.answer(start_text)
    await state.set_state(Form.waiting_for_carrots)

@dp.message(Form.waiting_for_carrots)
async def process_carrots(message: Message, state: FSMContext):
    await state.update_data(carrots=message.text)
    await message.answer("📱 <b>Вопрос 2: Напишите, на каком устройстве вы будете играть?</b>")
    await state.set_state(Form.waiting_for_device)

@dp.message(Form.waiting_for_device)
async def process_device(message: Message, state: FSMContext):
    await state.update_data(device=message.text)
    await message.answer("🎮 <b>Вопрос 3: Есть ли дискорд?</b>", reply_markup=get_yes_no_keyboard())
    await state.set_state(Form.waiting_for_discord)

@dp.callback_query(Form.waiting_for_discord, F.data.in_({"yes", "no"}))
async def process_discord(call: CallbackQuery, state: FSMContext):
    answer_text = "Да ✅" if call.data == "yes" else "Нет ❌"
    await state.update_data(discord=answer_text)
    await call.message.edit_text("🕹️ <b>Вопрос 4: Напишите ваш ник в Роблокс</b>")
    await state.set_state(Form.waiting_for_roblox)
    await call.answer()

@dp.message(Form.waiting_for_roblox)
async def process_roblox(message: Message, state: FSMContext):
    await state.update_data(roblox=message.text)
    await message.answer("📈 <b>Вопрос 5: Сколько в день вы фармите моркови?</b>")
    await state.set_state(Form.waiting_for_farm_amount)

@dp.message(Form.waiting_for_farm_amount)
async def process_farm(message: Message, state: FSMContext):
    await state.update_data(farm=message.text)
    
    proof_text = (
        "📸 <b>ФИНАЛЬНЫЙ ЭТАП: ПОДТВЕРЖДЕНИЕ</b>\n\n"
        "1. Зайдите в игру и сделайте скрин, чтобы доказать, сколько у вас моркови.\n\n"
        "👉 <b>Пришлите своё фото в ответ на это сообщение:</b>"
    )
    await message.answer(proof_text)
    await state.set_state(Form.waiting_for_proof)

@dp.message(Form.waiting_for_proof, F.photo)
async def handle_proof(message: Message, state: FSMContext):
    data = await state.get_data()
    file_id = message.photo[-1].file_id
    username = f"@{message.from_user.username}" if message.from_user.username else "Нет"
    
    caption = (f"📋 <b>НОВАЯ АНКЕТА!</b>\n\n"
               f"👤 <b>Имя:</b> {message.from_user.full_name}\n"
               f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
               f"🔗 <b>Юзер:</b> {username}\n"
               f"🥕 <b>Морковь (сейчас):</b> {data.get('carrots')}\n"
               f"📈 <b>Морковь (фарм в день):</b> {data.get('farm')}\n"
               f"📱 <b>Устройство:</b> {data.get('device')}\n"
               f"🎮 <b>Discord:</b> {data.get('discord')}\n"
               f"🕹️ <b>Roblox:</b> {data.get('roblox')}\n\n"
               f"📸 <i>Доказательство от пользователя:</i>")
    
    try:
        await bot.send_photo(GROUP_ID, photo=file_id, caption=caption, reply_markup=get_moderation_keyboard(message.from_user.id))
        await message.answer(
            "✅ <b>Анкета успешно отправлена!</b>\nОжидай решения администрации.\n\n"
            "🔗 <b>Наши паблики:</b>\n"
            "Telegram: <a href='https://t.me/piskaguild'>https://t.me/piskaguild</a>\n"
            "Discord: <a href='https://discord.gg/WM7eEPDkc'>https://discord.gg/WM7eEPDkc</a>"
        )
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        await message.answer("❌ Ошибка отправки анкеты.")
    await state.clear()

@dp.message(Form.waiting_for_proof)
async def wrong_proof(message: Message):
    await message.answer("❌ Пожалуйста, пришлите именно фото!")

# --- Модерация ---
@dp.callback_query(F.data.startswith("accept_"))
async def accept(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await call.message.edit_caption(caption=call.message.caption + "\n\n✅ <b>Принято!</b>", reply_markup=None)
    try: 
        await bot.send_message(uid, "✅ <b>Вы были приняты в клан!</b>\nДля вступления, напишите в @k6ppy")
    except: pass
    await call.answer()

@dp.callback_query(F.data.startswith("reject_"))
async def reject(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await call.message.edit_caption(caption=call.message.caption + "\n\n❌ <b>Отказано!</b>", reply_markup=None)
    try: await bot.send_message(uid, "❌ <b>Вы не приняты</b>")
    except: pass
    await call.answer()

@dp.callback_query(F.data.startswith("ban_"))
async def ban_user(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    banned_users.add(uid)
    await call.message.edit_caption(caption=call.message.caption + "\n\n🚫 <b>Пользователь забанен!</b>", reply_markup=None)
    try: await bot.send_message(uid, "🚫 <b>Вы забанены в боте.</b>")
    except: pass
    await call.answer("Пользователь заблокирован!")

async def main():
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
