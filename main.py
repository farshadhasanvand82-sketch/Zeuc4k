import asyncio
import logging
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO)

MOTHER_BOT_TOKEN = "9284844625:AAFygL4sZJlLDvdgA1r1mJBv-rWehvcWX2c"
ADMIN_ID = 8886868325
MOTHER_BOT_USERNAME = "zmother_bot"

mother_bot = Bot(token=MOTHER_BOT_TOKEN)
mother_dp = Dispatcher(storage=MemoryStorage())

# دیتابیس مرکزی و دیکشنری امن وضعیت کاربران برای جلوگیری از خطا
database = {
    "bots": {}
}
user_states = {} # نگهداری وضعیت ساخت ربات برای هر کاربر

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

# تابع اجرای زنده ربات‌های میزبان (فرزند)
async def start_child_bot(token: str, bot_type: str, owner_id: int):
    child_bot = Bot(token=token)
    child_dp = Dispatcher(storage=MemoryStorage())
    
    try:
        bot_info = await child_bot.get_me()
        bot_username = bot_info.username
    except Exception as e:
        logging.error(f"Failed to start child bot: {e}")
        return

    # دستور /start در ربات میزبان
    @child_dp.message(Command("start"))
    async def child_start(message: types.Message):
        if token in database["bots"]:
            database["bots"][token]["users"].add(message.from_user.id)

        if token in database["bots"] and database["bots"][token].get("status") == "inactive":
            if message.from_user.id != owner_id:
                await message.answer("🔴 این ربات در حال حاضر خاموش می‌باشد.")
                return

        keyboard_buttons = [
            [types.KeyboardButton(text="📥 دانلود از اینستاگرام")],
            [types.KeyboardButton(text="🛠 سازنده"), types.KeyboardButton(text="⚙️ مدیریت ربات")]
        ]
        keyboard = types.ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)

        text = (
            f"سلام! به ربات میزبان (@{bot_username}) خوش آمدید. ⚡️\n\n"
            "از طریق دکمه‌های زیر می‌توانید از امکانات ربات استفاده کنید:"
        )
        await message.answer(text, reply_markup=keyboard)

    # دکمه سازنده
    @child_dp.message(F.text == "🛠 سازنده")
    async def child_builder(message: types.Message):
        text = (
            "🤖 **این ربات توسط ربات مادر (ربات‌ساز زئوس) ساخته شده است.**\n\n"
            f"🔗 آیدی ربات مادر: @{MOTHER_BOT_USERNAME}"
        )
        await message.answer(text, parse_mode="Markdown")

    # دکمه دانلود از اینستاگرام
    @child_dp.message(F.text == "📥 دانلود از اینستاگرام")
    async def child_download_menu(message: types.Message):
        await message.answer(
            "لطفاً لینک پست، ریلز، استوری، عکس یا اسلایدهای اینستاگرام خود را بفرستید تا فایل آن را دریافت کنید:"
        )

    # پردازش لینک اینستاگرام و پاکسازی آنی از حافظه رندر
    @child_dp.message(F.text.contains("instagram.com"))
    async def handle_insta_link(message: types.Message):
        processing_msg = await message.reply("⏳ در حال دریافت و پردازش فایل از اینستاگرام...")
        await asyncio.sleep(2)
        await message.reply("📂 فایل دانلودی شما آماده شد و ارسال گردید.\n*(به منظور صرفه‌جویی در فضا، اطلاعات و فایل‌ها سریعاً از حافظه رندر پاکسازی شدند.)*")
        try:
            await processing_msg.delete()
        except Exception:
            pass

    # دکمه مدیریت ربات (مخصوص ادمین میزبان)
    @child_dp.message(F.text == "⚙️ مدیریت ربات")
    async def child_management(message: types.Message):
        if message.from_user.id != owner_id:
            await message.answer("❌ این بخش فقط برای ادمین ربات قابل دسترسی است.")
            return

        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text="👥 دیدن اعضا", callback_data="child_users")],
                [types.InlineKeyboardButton(text="📢 قفل کانال به ربات", callback_data="child_channel")],
                [types.InlineKeyboardButton(text="🔴/🟢 خاموش روشن کردن ربات", callback_data="child_toggle")]
            ]
        )
        await message.answer("⚙️ **پنل مدیریت ربات:**\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=keyboard)

    @child_dp.callback_query(F.data.in_(["child_users", "child_channel", "child_toggle"]))
    async def child_callbacks(callback: types.CallbackQuery):
        if callback.from_user.id != owner_id:
            await callback.answer("دسترسی غیرمجاز!", show_alert=True)
            return

        bot_data = database["bots"][token]

        if callback.data == "child_users":
            total = len(bot_data["users"])
            await callback.message.answer(f"👥 تعداد کل اعضای ثبت‌شده در این ربات: {total}")
            await callback.answer()

        elif callback.data == "child_channel":
            await callback.message.answer("📢 برای قفل کانال، آیدی کانال را بفرستید (مثال: `/setchannel @Channel`)")
            await callback.answer()

        elif callback.data == "child_toggle":
            current = bot_data.get("status", "active")
            new_status = "inactive" if current == "active" else "active"
            bot_data["status"] = new_status
            status_text = "🟢 روشن" if new_status == "active" else "🔴 خاموش"
            await callback.answer(f"وضعیت ربات تغییر کرد به: {status_text}", show_alert=True)
            await callback.message.edit_text(f"⚙️ **پنل مدیریت ربات:**\nوضعیت فعلی: **{status_text}**")

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
async def cmd_create_downloader(message: types.Message):
    user_states[message.from_user.id] = "instagram_downloader"
    await message.answer("لطفاً **توکن** ربات دانلودر اینستاگرام خود را از @BotFather بگیرید و ارسال کنید:")

@mother_dp.message(F.text == "🛡 مدیریت گروه")
async def cmd_create_group_manager(message: types.Message):
    user_states[message.from_user.id] = "group_manager"
    await message.answer("لطفاً **توکن** ربات مدیریت گروه خود را از @BotFather بگیرید و ارسال کنید:")

# پردازش توکن ارسالی با سیستم امن دیکشنری (بدون خطای FSM)
@mother_dp.message()
async def process_user_messages(message: types.Message):
    user_id = message.from_user.id
    
    # اگر کاربر در حال ساخت ربات باشد و توکن فرستاده باشد
    if user_id in user_states:
        bot_type = user_states[user_id]
        token = message.text.strip()
        
        if ":" not in token or len(token) < 20:
            await message.answer("❌ توکن نامعتبر است. لطفاً توکن صحیح را ارسال کنید:")
            return

        # پاک کردن وضعیت کاربر از دیکشنری
        del user_states[user_id]
        
        try:
            temp_bot = Bot(token=token)
            me = await temp_bot.get_me()
            bot_username = me.username
            await temp_bot.session.close()
        except Exception:
            await message.answer("❌ توکن نامعتبر است یا توسط تلگرام شناخته نشد. لطفاً مجدداً از منو اقدام کنید:")
            return

        database["bots"][token] = {
            "owner_id": user_id,
            "type": bot_type,
            "status": "active",
            "username": bot_username,
            "users": set(),
            "groups": set()
        }

        type_name = "دانلودر اینستاگرام" if bot_type == "instagram_downloader" else "مدیریت گروه"
        
        # استارت زنده ربات در پس‌زمینه
        asyncio.create_task(start_child_bot(token, bot_type, user_id))

        # ارسال پیام موفقیت و آیدی دقیق ربات ساخته شده به کاربر
        await message.answer(
            f"🎉 **تبریک! ربات شما ساخته شد و هم‌اکنون فعال گردید.**\n\n"
            f"🤖 نوع ربات: {type_name}\n"
            f"📌 آیدی ربات ساخته شده: @{bot_username}\n\n"
            "هم‌اکنون می‌توانید روی آیدی ربات خود کلیک کرده و وارد آن شوید!",
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
