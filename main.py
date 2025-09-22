import asyncio
import sqlite3
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Bot konfiguratsiyasi
BOT_TOKEN = "7424263149:AAEyeMN4UrdaLR0iFKjQUthnOl5fQvajpKg"
ADMIN_CHAT_IDS = [5515940993, 1746298530]

# Ma'lumotlar bazasini yaratish
def init_database():
    conn = sqlite3.connect('applications.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            phone_number TEXT,
            category TEXT,
            answers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

init_database()

# FSM holatlari
class InterviewStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_category = State()
    answering_questions = State()

# Savollar bazasi
QUESTIONS = {
    "📞 Operator": [
        "Telefon orqali ishlagan tajribangiz qaysi kompaniyada bo'lgan va qancha vaqt davom etgan?",
        "Bir kunda o'rtacha nechta qo'ng'iroq qila olasiz?",
        "Telefon orqali mijoz bilan gaplashishda eng katta xatoni qanday deb bilasiz?",
        "Mijoz \"narx qimmat\" desa, qanday javob qaytarasiz?",
        "Agar mijoz sizni baland ovoz bilan tanqid qilsa, qanday yo'l tutasiz?",
        "O'zingizni 3 ta so'z bilan tasvirlab bering.",
        "\"Bilmiman\" degan javob qay darajada to'g'ri?"
    ],
    "📱 SMM Menejer": [
        "Kamida 1 yil qaysi brend yoki kompaniyaning SMMini yuritgansiz?",
        "Siz ishlab chiqargan kontent reja misol qilib ayta olasizmi?",
        "Qaysi platformalarda eng ko'p natija bergansiz (Instagram, Telegram, TikTok...)?",
        "Kontent samaradorligini qanday o'lchaysiz? (Eng muhim metrikalar)",
        "Agar reklama byudjeti kichik bo'lsa, qanday qilib katta reach olish mumkin?",
        "Siz uchun \"samarali post\" deganda nima tushuniladi?"
    ],
    "🎬 Montajchi": [
        "Montaj sohasida 1 yildan ortiq qaysi loyihalarda ishlagansiz?",
        "Qaysi dasturlarni mukammal bilasiz? (Premiere Pro, After Effects, CapCut...)",
        "Siz ishlagan videolarni ko'rsatishingiz mumkinmi?",
        "Bir daqiqalik videoni o'rtacha nechchi soatda tayyorlaysiz?",
        "Agar mijoz video variantini rad etsa, qanday reaksiya qilasiz?",
        "Sizningcha, yaxshi montajchi qanday bo'lishi kerak?"
    ],
    "📊 Buxgalter": [
        "Qaysi sohada (savdo, xizmat, ishlab chiqarish) 1 yildan ortiq tajribangiz bor?",
        "Qaysi buxgalteriya dasturlarini bilasiz? (1C, Excel, boshqa)",
        "Soliq hisobotini o'zingiz mustaqil topshirib ko'rganmisiz?",
        "Eng katta xatoingizni eslay olasizmi va uni qanday to'g'rilagansiz?",
        "Ishda siz uchun qaysi qadriyat muhimroq: tezlikmi yoki aniqlik?",
        "Stress vaziyatda xatoga yo'l qo'ymaslik uchun nima qilasiz?"
    ],
    "🎨 Dizayner": [
        "Qaysi sohada va qaysi kompaniyalarda 1 yildan ortiq dizayner bo'lib ishlagansiz?",
        "Portfolioingizni ko'rsatishingiz mumkinmi? Qaysi ishlaringiz bilan faxrlanasiz?",
        "Biror mahsulot uchun baner tayyorlayotganda avval nimalarga e'tibor berasiz?",
        "\"Kompaniya brendingi\" deganda nimani tushunasiz?",
        "Siz uchun yaxshi dizaynerning eng muhim 3 sifati qaysilar?",
        "Ishingizda sizni ilhomlantiradigan narsa nima?",
        "Mijoz yoki rahbar doim fikrini o'zgartirsa, qanday ishlaysiz?"
    ],
    "👨‍💻 Dasturchi": [
        "Qaysi dasturlash tillarida (Python, JavaScript, Java, PHP, C#…) tajribangiz bor?",
        "API nima va uni ishlatgan loyihangizdan misol keltira olasizmi?",
        "Veb-sayt sekin ishlayapti, muammoni qanday aniqlaysiz?",
        "Sizningcha, yaxshi dasturchi qanday 3 sifatga ega bo'lishi kerak?",
        "\"Sizdan talab qilinadigan barcha ishlarni o'z vaqtida va to'liq bajarishga tayyormisiz?\""
    ]
}

# Bot va dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Asosiy tugmalar
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Operator"), KeyboardButton(text="📱 SMM Menejer")],
            [KeyboardButton(text="🎬 Montajchi"), KeyboardButton(text="📊 Buxgalter")],
            [KeyboardButton(text="🎨 Dizayner"), KeyboardButton(text="👨‍💻 Dasturchi")],
        ],
        resize_keyboard=True
    )

def get_phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Telefon raqamimni ulashish", request_contact=True)],
            [KeyboardButton(text="🔄 Qaytadan boshlash")]
        ],
        resize_keyboard=True
    )

# Ma'lumotlarni bazaga saqlash
def save_application(user_data):
    conn = sqlite3.connect('applications.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO applications (user_id, username, first_name, phone_number, category, answers)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        user_data['user_id'],
        user_data['username'],
        user_data['first_name'],
        user_data['phone_number'],
        user_data['category'],
        json.dumps(user_data['answers'], ensure_ascii=False)
    ))
    
    conn.commit()
    application_id = cursor.lastrowid
    conn.close()
    
    return application_id

# Admin ga ariza yuborish
async def send_to_admin(application_id, user_data):
    message = f"📄 <b>Yangi ariza #{application_id}</b>\n\n"
    message += f"👤 <b>Foydalanuvchi:</b> {user_data['first_name']}\n"
    message += f"📱 <b>Username:</b> @{user_data['username']}\n"
    message += f"📞 <b>Telefon:</b> +{user_data['phone_number']}\n"
    message += f"💼 <b>Lavozim:</b> {user_data['category']}\n\n"
    message += "📋 <b>Javoblar:</b>\n\n"
    
    for i, (question, answer) in enumerate(user_data['answers'].items(), 1):
        message += f"{i}. <b>{question}</b>\n"
        message += f"   <b>Javob:</b> {answer}\n\n"
    
    try:
        for ADMIN_CHAT_ID in ADMIN_CHAT_IDS:
            await bot.send_message(ADMIN_CHAT_ID, message, parse_mode='HTML')
    except Exception as e:
        print(f"Admin ga xabar yuborishda xatolik: {e}")

# Start komandasi
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    welcome_text = """👋 **Assalomu alaykum!**\n\n"Ariza topshirish boti"ga xush kelibsiz!\n\nQuyidagi lavozimlardan birini tanlang:"""
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode='Markdown')

# Qaytadan boshlash
@dp.message(lambda message: message.text == "🔄 Qaytadan boshlash")
async def restart_handler(message: types.Message, state: FSMContext):
    await cmd_start(message, state)

# Kategoriya tanlash
@dp.message(lambda message: message.text in QUESTIONS.keys())
async def category_handler(message: types.Message, state: FSMContext):
    category = message.text
    
    await state.update_data(category=category)
    
    phone_text = """📞 **Telefon raqamingizni ulashing**\n\nArizani topshirish uchun telefon raqamingizni ulashing."""
    
    await message.answer(phone_text, reply_markup=get_phone_keyboard(), parse_mode='Markdown')
    await state.set_state(InterviewStates.waiting_for_phone)

# Telefon raqamini qabul qilish
@dp.message(InterviewStates.waiting_for_phone)
async def phone_handler(message: types.Message, state: FSMContext):
    if message.contact:
        phone_number = message.contact.phone_number
    else:
        # Agar kontakt emas, matn sifatida qabul qilish
        phone_number = message.text
    
    user_data = await state.get_data()
    user_data.update({
        'user_id': message.from_user.id,
        'username': message.from_user.username or "Noma'lum",
        'first_name': message.from_user.first_name or "Foydalanuvchi",
        'phone_number': phone_number,
        'answers': {},
        'current_question_index': 0
    })
    
    await state.set_data(user_data)
    
    # Savollarni boshlash
    category = user_data['category']
    questions = QUESTIONS[category]
    
    await message.answer(f"💼 **{category}** lavozimi uchun savollar boshlanmoqda...\n\nSavollar soni: {len(questions)} ta", parse_mode='Markdown', reply_markup=types.ReplyKeyboardRemove())
    await asyncio.sleep(1)
    
    # Birinchi savolni yuborish
    await ask_question(message, state)

# Keyingi savolni so'rash
async def ask_question(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    category = user_data['category']
    questions = QUESTIONS[category]
    current_index = user_data['current_question_index']
    
    if current_index < len(questions):
        question = questions[current_index]
        
        # Savolni chiroyli formatda yuborish
        question_text = f"❓ **{current_index + 1}-savol:** {question}\n\n"
        
        await message.answer(question_text, parse_mode='Markdown')
        await state.set_state(InterviewStates.answering_questions)
    else:
        # Barcha savollar tugadi
        await finish_interview(message, state)

# Javobni qabul qilish
@dp.message(InterviewStates.answering_questions)
async def answer_handler(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    category = user_data['category']
    questions = QUESTIONS[category]
    current_index = user_data['current_question_index']
    
    # Javobni saqlash
    current_question = questions[current_index]
    user_data['answers'][current_question] = message.text
    
    # Keyingi savolga o'tish
    user_data['current_question_index'] += 1
    await state.set_data(user_data)
    
    await ask_question(message, state)

# Intervyuni tugatish
async def finish_interview(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    
    # Ma'lumotlarni bazaga saqlash
    application_id = save_application(user_data)
    
    # Admin ga yuborish
    await send_to_admin(application_id, user_data)
    
    # Foydalanuvchiga tasdiqlash
    success_text = """✅ **Arizangiz muvaffaqiyatli topshirildi!**\n\nSizning arizangiz qabul qilindi va administratorga yuborildi.\n\nTez orada siz bilan bog'lanamiz!"""
    
    await message.answer(success_text, reply_markup=get_main_keyboard(), parse_mode='Markdown')
    await state.clear()

# Boshqa xabarlarga javob
@dp.message()
async def other_messages(message: types.Message):
    if message.text not in QUESTIONS.keys():
        await message.answer("Iltimos, quyidagi lavozimlardan birini tanlang:", reply_markup=get_main_keyboard())

# Botni ishga tushirish
async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())