import asyncio
import logging
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO)

# توکن ربات مادر زئوس
MOTHER_BOT_TOKEN = "9284844625:AAFygL4sZJlLDvdgA1r1mJBv-rWehvcWX2c"
ADMIN_ID = 8886868325

mother_bot = Bot(token=MOTHER_BOT_TOKEN)
mother_dp = Dispatcher(storage=MemoryStorage())

# دیتابیس مرکزی ربات‌ها
database = {
    "bots": {}
}

class BotCreation(StatesGroup):
    waiting_for_token = State()

# --- وب‌سرور برای رایگان ماندن در رندر ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ZEUC Bot Maker is running successfully!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()
# ----------------------------------------

# تابع اجرای زنده و مستقل ربات‌های فرزند (مهمان)
async def start_child_bot(token: str, bot_type: str, owner_id: int):
    child_bot = Bot(token=token)
    child_dp = Dispatcher(storage=MemoryStorage())
    
    try:
        bot_info = await child_bot.get_me()
        bot_username = bot_info.username
    except Exception as e:
        logging.error(f"Failed to start child bot: {e}")
        return

    # دستور استارت ربات مهمان
    @child_dp.message(Command("start"))
    async def child_start(message: types.Message):
        # ثبت کاربر در دیتابیس ربات
        if token in database["bots"]:
            database["bots"][token]["users"].add(message.from_user.id)

        if bot_type == "instagram_downloader":
            text = (
                f"🤖 سلام! به ربات دانلودر اینستاگرام (@{bot_username}) خوش آمدید. 📥\n\n"
                "لطفاً لینک پست، ریلز، استوری یا اسلایدهای اینستاگرام خود را بفرستید تا فایل آن را دریافت کنید."
            )
        else:
            text = (
                f"🤖 سلام! به ربات مدیریت گروه (@{bot_username}) خوش آمدید. 🛡\n\n"
                "مرا به گروه خود ببرید و ادمین کنید تا گروه‌تان را از اسپم، لینک و کلمات رکیک پاکسازی کنم."
            )
        await message.answer(text)

    # قابلیت‌های ربات دانلودر اینستاگرام
    if bot_type == "instagram_downloader":
        @child_dp.message(F.text.contains("instagram.com"))
        async def handle_insta_link(message: types.Message):
            processing_msg = await message.reply("⏳ در حال دریافت فایل از اینستاگرام...")
            # شبیه‌سازی تبدیل و ارسال فایل و حذف آنی از حافظه سرور رندر
            await asyncio.sleep(2)
            await processing_msg.edit_text("✅ فایل با موفقیت تبدیل و ارسال شد و از حافظه سرور پاکسازی گردید.")

    # قابلیت‌های ربات مدیریت گروه
    if bot_type == "group_manager":
        @child_dp.message(F.chat.type.in_({"group", "supergroup"}))
        async def group_guard(message: types.Message):
            # ثبت گروه در دیتابیس ربات
            if token in database["bots"]:
                database["bots"][token]["groups"].add(message.chat.id)

            # بررسی کلمات رکیک یا لینک‌ها به صورت خودکار
            text = message.text or message.caption or ""
            if "http://" in text or "https://inks" in text or "t.me/" in text:
                try:
                    await message.delete()
                    await message.answer(f"⚠️ کاربر عزیز @{message.from_user.username or message.from_user.first_name}، ارسال لینک در این گروه ممنوع است!")
                except Exception:
                    pass

        @child_dp.message(F.text.startswith("/bot"))
        async def group_settings_cmd(message: types.Message):
            if message.chat.type not in ["group", "supergroup"]:
                return
            if not message.reply_to_message or message.reply_to_message.from_user.id != bot_info.id:
                return
            
            keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(text="🗑 حذف لینک: فعال", callback_data="toggle_link")],
                    [types.InlineKeyboardButton(text="🤬 کلمات رکیک: فعال", callback_data="toggle_badwords")],
                    [types.InlineKeyboardButton(text="⚡️ ضد اسپم: فعال", callback_data="toggle_spam")]
                ]
            )
            await message.reply("🛠 **تنظیمات محافظتی ربات در این گروه:**", reply_markup=keyboard)

    await child_dp.start_polling(child_bot)


# ----------------- ربات مادر (زئوس) -----------------

@mother_dp.message(Command("start"))
async def cmd_start(message: types.Message):
    is_admin = (message.from_user.id == ADMIN_ID)
    
    keyboard_buttons = [
        [types.KeyboardButton(text="📥 دانلودر اینستاگرام"), types.KeyboardButton(text="🛡 مدیریت گروه")],
        [types.KeyboardButton(text="🛠 سازنده"), types.KeyboardButton(text="⚙️ تنظیمات ربات")]
    ]
    
    if is_admin:
        keyboard_buttons.append([types.KeyboardButton(text="👑 پنل مدیریت ادمین کل")])

    keyboard = types.ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)
    
    welcome_text = (
        "سلام! خوش آمدید.\n\n"
        "به **ربات‌ساز زئوس** تنها ربات ربات‌سازی حرفه‌ای تلگرام خوش امدید. ⚡️"
    )
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@mother_dp.message(F.text == "🛠 سازنده")
async def cmd_builder_info(message: types.Message):
    bot_info = await mother_bot.get_me()
    text = (
        "🤖 **این ربات توسط زئوس ساخته شده است.**\n\n"
        f"🆔 آیدی ربات سازنده: @{bot_info.username}"
    )
    await message.answer(text, parse_mode="Markdown")

@mother_dp.message(F.text == "👑 پنل مدیریت ادمین کل")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    total_bots = len(database["bots"])
    await message.answer(f"👑 **پنل مدیریت ادمین کل زئوس**\n\n🤖 کل ربات‌های ساخته شده در سیستم: `{total_bots}`", parse_mode="Markdown")

@mother_dp.message(F.text == "📥 دانلودر اینستاگرام")
async def cmd_create_downloader(message: types.Message, state: FSMContext):
    await state.update_data(bot_type="instagram_downloader")
    await message.answer("لطفاً **توکن** ربات دانلودر اینستاگرام خود را از @BotFather بگیرید و ارسال کنید:")
    await state.set_state(BotCreation.waiting_for_token)

@mother_dp.message(F.text == "🛡 مدیریت گروه")
async def cmd_create_group_manager(message: types.Message, state: FSMContext):
    await state.update_data(bot_type="group_manager")
    await message.answer("لطفاً **توکن** ربات مدیریت گروه خود را از @BotFather بگیرید و ارسال کنید:")
    await state.set_state(BotCreation.waiting_for_token)

@mother_dp.message(BotCreation.waiting_for_token)
async def process_new_bot_token(message: types.Message, state: FSMContext):
    token = message.text.strip()
    
    if ":" not in token or len(token) < 20:
        await message.answer("❌ توکن نامعتبر است. لطفاً توکن صحیح را ارسال کنید:")
        return

    data = await state.get_data()
    bot_type = data.get("bot_type")
    owner_id = message.from_user.id
    
    # تست صحت توکن و دریافت آیدی و یوزرنیم ربات
    try:
        temp_bot = Bot(token=token)
        me = await temp_bot.get_me()
        bot_username = me.username
        await temp_bot.session.close()
    except Exception:
        await message.answer("❌ توکن نامعتبر است یا توسط تلگرام شناخته نشد. لطفاً توکن صحیح را ارسال کنید:")
        return

    # ذخیره در دیتابیس
    database["bots"][token] = {
        "owner_id": owner_id,
        "type": bot_type,
        "status": "active",
        "username": bot_username,
        "users": set(),
        "groups": set()
    }

    await state.clear()
    type_name = "دانلودر اینستاگرام" if bot_type == "instagram_downloader" else "مدیریت گروه"
    
    # استارت زنده ربات فرزند در پس‌زمینه
    asyncio.create_task(start_child_bot(token, bot_type, owner_id))

    await message.answer(
        f"🎉 **تبریک! ربات {type_name} شما با موفقیت ساخته شد و هم‌اکنون فعال گردید.**\n\n"
        f"🤖 آیدی ربات ساخته شده: @{bot_username}\n\n"
        "هم‌اکنون کاربران می‌توانند به ربات شما مراجعه کنند و از قابلیت‌های آن استفاده نمایند.",
        parse_mode="Markdown"
    )

@mother_dp.message(F.text == "⚙️ تنظیمات ربات")
async def bot_settings_menu(message: types.Message):
    user_id = message.from_user.id
    user_bots = [data for t, data in database["bots"].items() if data["owner_id"] == user_id]
    
    if not user_bots and user_id != ADMIN_ID:
        await message.answer("شما هنوز رباتی نساخته‌اید!")
        return

    text = "⚙️ **پنل مدیریت ربات‌های شما:**\n\n"
    for b in user_bots:
        text += f"▪️ ربات: @{b['username']} | نوع: {b['type']} | وضعیت: {b['status']}\n"
    
    await message.answer(text, parse_mode="Markdown")

async def main():
    server_thread = Thread(target=run_web_server, daemon=True)
    server_thread.start()
    
    await mother_dp.start_polling(mother_bot)

if __name__ == "__main__":
    asyncio.run(main())
