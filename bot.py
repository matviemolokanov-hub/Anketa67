import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
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
    waiting_for_crops = State()           # Вопрос 1: Дорогие семена/плоды
    waiting_for_inventory = State()       # Вопрос 2: Размер инвентаря
    waiting_for_roblox = State()          # Вопрос 3: Ник в Roblox
    waiting_for_discord = State()         # Вопрос 4: Наличие Discord
    waiting_for_proof = State()           # Пруф (фото)

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
        [InlineKeyboardButton(text="⏳ Резерв", callback_data=f"reserve_{user_id}")],
        [InlineKeyboardButton(text="🚫 Забанить", callback_data=f"ban_{user_id}")]
    ])

def get_photo_done_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Отправить все фото", callback_data="photos_done")]
    ])

# --- Хендлеры ---

@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    if message.from_user.id in banned_users:
        await message.answer("⛔️ Вы заблокированы.")
        return
        
    # Очищаем данные пользователя при новом старте
    await state.clear()
    
    start_text = (
        "📋 <b>Вступление в [PISKA] Cool Piski</b>\n\n"
        "Текущий ивент — <b>Cash Crop</b>.\n"
        "Главное в ивенте: сделать самую большую продажу инвентаря за раз.\n\n"
        "Что важно для отбора:\n\n"
        "1️⃣ 🌱 <b>Дорогие семена / плоды</b>\n"
        "В первую очередь смотрим, что у тебя уже есть из дорогого:\n"
        "• Moon Bloom\n"
        "• Venom Spitter\n"
        "• Dragon's Breath\n"
        "• Venus Fly Trap\n"
        "• Ghost Pepper\n"
        "• Sunflower\n"
        "• Mushroom\n\n"
        "Указывай общее количество: что уже посажено + что лежит в инвентаре.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "❓ <b>Вопрос 1:</b> Напишите, что у вас есть из дорогих культур и в каком количестве:"
    )
    
    await message.answer(start_text)
    await state.set_state(Form.waiting_for_crops)

@dp.message(Form.waiting_for_crops)
async def process_crops(message: Message, state: FSMContext):
    await state.update_data(crops=message.text)
    
    await message.answer(
        "2️⃣ 🎒 <b>Размер инвентаря</b>\n\n"
        "Варианты: 100 / 150 / 200 / больше.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "❓ <b>Вопрос 2:</b> Напишите, какой у вас размер инвентаря:"
    )
    await state.set_state(Form.waiting_for_inventory)

@dp.message(Form.waiting_for_inventory)
async def process_inventory(message: Message, state: FSMContext):
    await state.update_data(inventory=message.text)
    
    await message.answer(
        "3️⃣ 🕹️ <b>Ник в Roblox</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "❓ <b>Вопрос 3:</b> Напишите ваш ник в Roblox:"
    )
    await state.set_state(Form.waiting_for_roblox)

@dp.message(Form.waiting_for_roblox)
async def process_roblox(message: Message, state: FSMContext):
    await state.update_data(roblox=message.text)
    
    await message.answer(
        "4️⃣ 🎮 <b>Наличие Discord</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "❓ <b>Вопрос 4:</b> У вас есть Discord?",
        reply_markup=get_yes_no_keyboard()
    )
    await state.set_state(Form.waiting_for_discord)

@dp.callback_query(Form.waiting_for_discord, F.data.in_({"yes", "no"}))
async def process_discord(call: CallbackQuery, state: FSMContext):
    answer_text = "✅ Да" if call.data == "yes" else "❌ Нет"
    await state.update_data(discord=answer_text)
    
    # Инициализируем список для хранения фото
    await state.update_data(photos=[])
    await state.update_data(photo_count=0)
    
    proof_text = (
        "📸 <b>ПРУФ</b>\n\n"
        "Отправьте <b>одно или несколько</b> фото:\n"
        "• 🌱 сада\n"
        "• 🎒 инвентаря\n"
        "• 🌿 дорогих плодов / семян\n"
        "• 📊 Cash Crop результата\n\n"
        "📤 <b>Отправляйте фото по одному</b>\n"
        "После загрузки всех фото нажмите кнопку\n"
        "⬇️ <b>«Отправить все фото»</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "📤 <b>Пришлите первое фото:</b>"
    )
    await call.message.edit_text(proof_text, reply_markup=None)
    await state.set_state(Form.waiting_for_proof)
    await call.answer()

@dp.message(Form.waiting_for_proof, F.photo)
async def handle_proof_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    photo_count = data.get('photo_count', 0)
    
    # Сохраняем file_id фото
    file_id = message.photo[-1].file_id
    photos.append(file_id)
    photo_count += 1
    
    await state.update_data(photos=photos)
    await state.update_data(photo_count=photo_count)
    
    # Показываем кнопку "Отправить все фото"
    keyboard = get_photo_done_keyboard()
    
    await message.answer(
        f"✅ <b>Фото {photo_count} загружено!</b>\n\n"
        f"📸 Загружено фото: {photo_count}\n\n"
        "📤 <b>Отправьте ещё фото</b> (если нужно)\n"
        "или нажмите кнопку ниже:",
        reply_markup=keyboard
    )

@dp.callback_query(Form.waiting_for_proof, F.data == "photos_done")
async def send_all_photos(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])
    
    if not photos:
        await call.answer("❌ Вы не отправили ни одного фото!", show_alert=True)
        return
    
    # Отправляем все фото в группу модерации
    username = f"@{call.from_user.username}" if call.from_user.username else "❌ Нет"
    
    caption = (
        f"📋 <b>НОВАЯ АНКЕТА</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Имя:</b> {call.from_user.full_name}\n"
        f"🆔 <b>ID:</b> <code>{call.from_user.id}</code>\n"
        f"🔗 <b>Юзер:</b> {username}\n\n"
        f"1️⃣ 🌱 <b>Дорогие семена/плоды:</b>\n"
        f"<i>{data.get('crops')}</i>\n\n"
        f"2️⃣ 🎒 <b>Размер инвентаря:</b> {data.get('inventory')}\n\n"
        f"3️⃣ 🕹️ <b>Roblox ник:</b> {data.get('roblox')}\n\n"
        f"4️⃣ 🎮 <b>Discord:</b> {data.get('discord')}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📸 <i>Пруф от пользователя ({len(photos)} фото):</i>"
    )
    
    try:
        # Отправляем первое фото с подписью
        await bot.send_photo(
            GROUP_ID, 
            photo=photos[0], 
            caption=caption, 
            reply_markup=get_moderation_keyboard(call.from_user.id)
        )
        
        # Отправляем остальные фото как отдельные сообщения (без подписи)
        for photo_id in photos[1:]:
            await bot.send_photo(GROUP_ID, photo=photo_id)
        
        # Уведомляем пользователя
        await call.message.edit_text(
            "✅ <b>Все фото успешно отправлены!</b>\n"
            "Анкета передана на рассмотрение.\n"
            "Ожидай решения администрации.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔗 <b>Наши паблики:</b>\n"
            "Telegram: <a href='https://t.me/piskaguild'>https://t.me/piskaguild</a>\n"
            "Discord: <a href='https://discord.gg/WM7eEPDkc'>https://discord.gg/WM7eEPDkc</a>"
        )
        
        await call.answer("✅ Анкета отправлена!")
        await state.clear()
        
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        await call.message.answer("❌ Ошибка отправки анкеты. Попробуйте снова /start")
        await state.clear()
        await call.answer()

@dp.message(Form.waiting_for_proof)
async def wrong_proof(message: Message):
    await message.answer(
        "❌ Пожалуйста, пришлите именно <b>фото</b>!\n\n"
        "📸 Отправьте фото сада, инвентаря или плодов."
    )

# --- Модерация ---
@dp.callback_query(F.data.startswith("accept_"))
async def accept(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await call.message.edit_caption(caption=call.message.caption + "\n\n✅ <b>Принято!</b>", reply_markup=None)
    try: 
        await bot.send_message(uid, 
            "✅ <b>Поздравляем! Вы приняты в клан!</b>\n\n"
            "Для вступления, напишите одному из админов:\n"
            "👤 @k6ppy\n"
            "👤 @Forchlele"
        )
    except: pass
    await call.answer()

@dp.callback_query(F.data.startswith("reject_"))
async def reject(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await call.message.edit_caption(caption=call.message.caption + "\n\n❌ <b>Отказано!</b>", reply_markup=None)
    try: await bot.send_message(uid, "❌ <b>К сожалению, вы не прошли отбор.</b>")
    except: pass
    await call.answer()

@dp.callback_query(F.data.startswith("reserve_"))
async def reserve_user(call: CallbackQuery):
    uid = int(call.data.split("_")[1])
    await call.message.edit_caption(caption=call.message.caption + "\n\n⏳ <b>Статус: В резерве</b>", reply_markup=None)
    reserve_msg = (
        "⭐️ <b>Твоя анкета пока в резерве</b>\n\n"
        "Это не отказ. Сейчас мест в гильдии ограниченное количество, поэтому в основной состав сначала берём самых сильных и активных игроков.\n\n"
        "Твоя заявка сохранена. Если освободится место или ты покажешь хороший прогресс, мы сможем пересмотреть анкету.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "<b>Чтобы подняться выше в списке:</b>\n"
        "🌱 собери больше дорогих культур\n"
        "🎒 увеличь размер инвентаря\n"
        "📈 покажи хороший прогресс в ивенте\n"
        "⏰ будь активен и не пропадай\n\n"
        "<i>Если будет место — админ напишет тебе.</i>"
    )
    try: await bot.send_message(uid, reserve_msg)
    except: pass
    await call.answer("Пользователь в резерве")

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
