import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
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

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

banned_users = set()

class Form(StatesGroup):
    waiting_for_crops = State()
    waiting_for_inventory = State()
    waiting_for_roblox = State()
    waiting_for_discord = State()
    waiting_for_proof = State()

def get_yes_no_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="yes"),
         InlineKeyboardButton(text="❌ Нет", callback_data="no")]
    ])

def get_moderation_keyboard(user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{user_id}"),
         InlineKeyboardButton(text="❌ Отказать", callback_data=f"reject_{user_id}")],
        [InlineKeyboardButton(text="⏳ Резерв", callback_data=f"reserve_{user_id}")],
        [InlineKeyboardButton(text="🚫 Забанить", callback_data=f"ban_{user_id}")]
    ])

@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    if message.from_user.id in banned_users:
        return await message.answer("⛔️ Вы заблокированы.")
        
    start_text = (
        "📋 <b>Вступление в [PISKA] Cool Piski</b>\n\n"
        "Текущий ивент — <b>Cash Crop.</b>\n"
        "<i>Главное в ивенте: сделать самую большую продажу инвентаря за раз.</i>\n\n"
        "<b>Что важно для отбора:</b>\n"
        "1) 🌱 Дорогие crops / seeds / плоды\n"
        "2) 🎒 Размер инвентаря\n"
        "3) Ник в роблоксе\n"
        "4) Есть ли дискорд?\n"
        "5) 📸 Пруф (Скрин сада / инвентаря / Cash Crop)\n\n"
        "👇 <b>Вопрос 1: Напишите, какие дорогие плоды/семена у вас есть и в каком количестве?</b>"
    )
    await message.answer(start_text)
    await state.set_state(Form.waiting_for_crops)

@dp.message(Form.waiting_for_crops)
async def process_crops(message: Message, state: FSMContext):
    await state.update_data(crops=message.text)
    await message.answer("🎒 <b>Вопрос 2: Напишите, какой у вас размер инвентаря (100/150/200/больше)?</b>")
    await state.set_state(Form.waiting_for_inventory)

@dp.message(Form.waiting_for_inventory)
async def process_inventory(message: Message, state: FSMContext):
    await state.update_data(inventory=message.text)
    await message.answer("🕹️ <b>Вопрос 3: Напишите ваш ник в Роблокс</b>")
    await state.set_state(Form.waiting_for_roblox)

@dp.message(Form.waiting_for_roblox)
async def process_roblox(message: Message, state: FSMContext):
    await state.update_data(roblox=message.text)
    await message.answer("🎮 <b>Вопрос 4: Есть ли дискорд?</b>", reply_markup=get_yes_no_keyboard())
    await state.set_state(Form.waiting_for_discord)

@dp.callback_query(Form.waiting_for_discord, F.data.in_({"yes", "no"}))
async def process_discord(call: CallbackQuery, state: FSMContext):
    answer = "Да ✅" if call.data == "yes" else "Нет ❌"
    await state.update_data(discord=answer)
    
    proof_text = (
        "📸 <b>ФИНАЛЬНЫЙ ЭТАП: ПРУФЫ</b>\n\n"
        "Сделайте скрин сада / инвентаря / дорогих плодов / Cash Crop результата.\n\n"
        "👉 <b>Пришлите фото в ответ на это сообщение:</b>"
    )
    await call.message.edit_text(proof_text)
    await state.set_state(Form.waiting_for_proof)
    await call.answer()

@dp.message(Form.waiting_for_proof, F.photo)
async def handle_proof(message: Message, state: FSMContext):
    data = await state.get_data()
    file_id = message.photo[-1].file_id
    username = f"@{message.from_user.username}" if message.from_user.username else "Нет"
    
    caption = (f"📋 <b>НОВАЯ АНКЕТА!</b>\n\n"
               f"👤 <b>Имя:</b> {message.from_user.full_name}\n"
               f"🔗 <b>Юзер:</b> {username}\n"
               f"🌱 <b>Crops/Seeds:</b> {data.get('crops')}\n"
               f"🎒 <b>Инвентарь:</b> {data.get('inventory')}\n"
               f"🕹️ <b>Roblox:</b> {data.get('roblox')}\n"
               f"🎮 <b>Discord:</b> {data.get('discord')}\n\n"
               f"📸 <i>Пруфы:</i>")
    
    try:
        await bot.send_photo(GROUP_ID, photo=file_id, caption=caption, reply_markup=get_moderation_keyboard(message.from_user.id))
        await message.answer("✅ <b>Анкета отправлена на рассмотрение!</b>")
    except Exception as e:
        await message.answer("❌ Ошибка отправки.")
    await state.clear()

# --- Модерация ---
@dp.callback_query(F.data.startswith("accept_"))
async def accept(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await call.message.edit_caption(caption=call.message.caption + "\n\n✅ <b>Принято!</b>", reply_markup=None)
    try: await bot.send_message(uid, "✅ <b>Вы были приняты в клан!</b>\nДля вступления, напишите одному из админов:\n@k6ppy\n@Forchlele")
    except: pass
    await call.answer()

@dp.callback_query(F.data.startswith("reject_"))
async def reject(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await call.message.edit_caption(caption=call.message.caption + "\n\n❌ <b>Отказано!</b>", reply_markup=None)
    try: await bot.send_message(uid, "❌ <b>Вы не приняты</b>")
    except: pass
    await call.answer()

@dp.callback_query(F.data.startswith("reserve_"))
async def reserve_user(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await call.message.edit_caption(caption=call.message.caption + "\n\n⏳ <b>Статус: В резерве</b>", reply_markup=None)
    reserve_msg = ("⭐️ <b>Твоя анкета пока в резерве...</b>\n\nСейчас мест ограничено, мы сохранили твою заявку. Мы напишем, если место появится!")
    try: await bot.send_message(uid, reserve_msg)
    except: pass
    await call.answer("Пользователь в резерве")

@dp.callback_query(F.data.startswith("ban_"))
async def ban_user(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await call.message.edit_caption(caption=call.message.caption + "\n\n🚫 <b>Пользователь забанен!</b>", reply_markup=None)
    try: await bot.send_message(uid, "🚫 <b>Вы забанены в боте.</b>")
    except: pass
    await call.answer("Пользователь заблокирован!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
