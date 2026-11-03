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
# آیدی عددی ادمین اصلی ربات مادر
ADMIN_ID = 8886868325

bot = Bot(token=MOTHER_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# دیتابیس ساختاریافته در حافظه
database = {
    "bots": {}
}

class BotCreation(StatesGroup):
    waiting_for_token = State()

# --- بخش وب‌سرور برای رایگان ماندن در رندر ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ZEUC Bot is running successfully!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()
# ---------------------------------------------

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # بررسی اینکه آیا کاربر ادمین اصلی است یا کاربر عادی
    is_admin = (message.from_user.id == ADMIN_ID)
    
    keyboard_buttons = [
        [types.KeyboardButton(text="📥 دانلودر اینستاگرام"), types.KeyboardButton(text="🛡 مدیریت گروه")],
        [types.KeyboardButton(text="🛠 سازنده"), types.KeyboardButton(text="⚙️ تنظیمات ربات")]
    ]
    
    # اگر کاربر ادمین اصلی باشد، دکمه مدیریت کل سیستم را هم می‌بیند
    if is_admin:
        keyboard_buttons.append([types.KeyboardButton(text="👑 پنل مدیریت ادمین کل")])

    keyboard = types.ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)
    
    welcome_text = (
        "سلام! خوش آمدید.\n\n"
        "به **ربات‌ساز زئوس** تنها ربات ربات‌سازی حرفه‌ای تلگرام خوش امدید. ⚡️"
    )
    if is_admin:
        welcome_text += "\n\n👑 *شما به عنوان ادمین اصلی ربات شناسایی شدید.*"

    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(F.text == "🛠 سازنده")
async def cmd_builder_info(message: types.Message):
    bot_info = await bot.get_me()
    text = (
        "🤖 **این ربات توسط زئوس ساخته شده است.**\n\n"
        f"🆔 آیدی ربات سازنده: @{bot_info.username}"
    )
    await message.answer(text, parse_mode="Markdown")

# پنل مدیریت اختصاصی ادمین کل
@dp.message(F.text == "👑 پنل مدیریت ادمین کل")
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ شما دسترسی به این بخش ندارید.")
        return
        
    total_bots = len(database["bots"])
    text = (
        "👑 **پنل مدیریت ادمین کل زئوس**\n\n"
        f"🤖 تعداد کل ربات‌های ساخته شده در سیستم: `{total_bots}`\n\n"
        "از طریق این بخش می‌توانید نظارت کامل روی ربات‌ساز داشته باشید."
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📥 دانلودر اینستاگرام")
async def cmd_create_downloader(message: types.Message, state: FSMContext):
    await state.update_data(bot_type="instagram_downloader")
    await message.answer(
        "لطفاً **توکن** ربات جدیدی که از @BotFather برای دانلودر اینستاگرام گرفتید را ارسال کنید:"
    )
    await state.set_state(BotCreation.waiting_for_token)

@dp.message(F.text == "🛡 مدیریت گروه")
async def cmd_create_group_manager(message: types.Message, state: FSMContext):
    await state.update_data(bot_type="group_manager")
    await message.answer(
        "لطفاً **توکن** ربات جدیدی که از @BotFather برای مدیریت گروه گرفتید را ارسال کنید:\n\n"
        "*(پس از ارسال، ربات ساخته شده و می‌توانید آن را به گروه خود ببرید و ادمین کنید)*"
    )
    await state.set_state(BotCreation.waiting_for_token)

@dp.message(BotCreation.waiting_for_token)
async def process_new_bot_token(message: types.Message, state: FSMContext):
    token = message.text.strip()
    
    if ":" not in token or len(token) < 20:
        await message.answer("❌ توکن نامعتبر است. لطفاً توکن صحیح را ارسال کنید:")
        return

    data = await state.get_data()
    bot_type = data.get("bot_type")
    owner_id = message.from_user.id
    
    database["bots"][token] = {
        "owner_id": owner_id,
        "type": bot_type,
        "status": "active",
        "channel": None,
        "users": set(),
        "groups": set(),
        "settings": {
            "anti_spam": True,
            "bad_words_filter": True,
            "anti_link": True
        }
    }

    await state.clear()
    type_name = "دانلودر اینستاگرام" if bot_type == "instagram_downloader" else "مدیریت گروه"
    
    await message.answer(
        f"🎉 **تبریک! ربات {type_name} شما با موفقیت ساخته شد و فعال گردید.**\n\n"
        "می‌توانید از منوی زیر یا پنل تنظیمات برای مدیریت آن استفاده کنید.",
        parse_mode="Markdown"
    )

@dp.message(F.text == "⚙️ تنظیمات ربات")
async def bot_settings_menu(message: types.Message):
    user_id = message.from_user.id
    user_bots = [t for t, data in database["bots"].items() if data["owner_id"] == user_id]
    
    if not user_bots and user_id != ADMIN_ID:
        await message.answer("شما هنوز رباتی نساخته‌اید! از دکمه‌های ربات‌ساز اقدام به ساخت ربات کنید.")
        return

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="👥 مشاهده کاربران", callback_data="show_users")],
            [types.InlineKeyboardButton(text="🛡 مشاهده گروه‌ها", callback_data="show_groups")],
            [types.InlineKeyboardButton(text="📢 تنظیم قفل کانال", callback_data="set_channel")],
            [types.InlineKeyboardButton(text="🔴/🟢 روشن/خاموش کردن ربات", callback_data="toggle_status")]
        ]
    )
    await message.answer("⚙️ **پنل مدیریت ربات‌های شما:**\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data.in_(["show_users", "show_groups", "set_channel", "toggle_status"]))
async def handle_settings_callbacks(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_token = next((t for t, data in database["bots"].items() if data["owner_id"] == user_id), None)
    
    if not user_token and user_id != ADMIN_ID:
        await callback.answer("رباتی یافت نشد!", show_alert=True)
        return

    # اگر ادمین کل باشد و رباتی نساخته باشد، پیام مناسب بدهد
    if not user_token and user_id == ADMIN_ID:
        await callback.answer("شما به عنوان ادمین کل رباتی نساخته‌اید.", show_alert=True)
        return

    bot_data = database["bots"][user_token]

    if callback.data == "show_users":
        total_users = len(bot_data["users"])
        users_list = "\n".join([str(uid) for uid in list(bot_data["users"])[:20]])
        text = f"👥 **تعداد کل کاربران ربات:** {total_users}\n\n**لیست آیدی کاربران:**\n{users_list if users_list else 'کاربری ثبت نشده است.'}"
        await callback.message.answer(text, parse_Mode="Markdown")
        await callback.answer()

    elif callback.data == "show_groups":
        total_groups = len(bot_data["groups"])
        groups_list = "\n".join([str(gid) for gid in list(bot_data["groups"])])
        text = f"🛡 **تعداد گروه‌های تحت مدیریت:** {total_groups}\n\n**لیست شناسه گروه‌ها:**\n{groups_list if groups_list else 'ربات هنوز در گروهی اضافه نشده است.'}"
        await callback.message.answer(text, parse_mode="Markdown")
        await callback.answer()

    elif callback.data == "set_channel":
        await callback.message.answer("برای تنظیم قفل کانال، آیدی کانال را بفرستید (مثال: `/setchannel @ChannelUsername`)", parse_mode="Markdown")
        await callback.answer()

    elif callback.data == "toggle_status":
        current_status = bot_data["status"]
        new_status = "inactive" if current_status == "active" else "active"
        bot_data["status"] = new_status
        status_text = "🟢 روشن" if new_status == "active" else "🔴 خاموش"
        await callback.answer(f"وضعیت ربات تغییر کرد به: {status_text}", show_alert=True)
        await callback.message.edit_text(f"⚙️ **پنل مدیریت ربات:**\nوضعیت فعلی: **{status_text}**", parse_mode="Markdown")

@dp.message(F.text.startswith("/bot"))
async def group_bot_settings_command(message: types.Message):
    if message.chat.type not in ["group", "supergroup"]:
        return
        
    if not message.reply_to_message or message.reply_to_message.from_user.id != (await bot.get_me()).id:
        return

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🗑 حذف لینک: فعال/غیرفعال", callback_data="grp_toggle_link")],
            [types.InlineKeyboardButton(text="🤬 حذف کلمات رکیک: فعال/غیرفعال", callback_data="grp_toggle_badwords")],
            [types.InlineKeyboardButton(text="⚡️ ضد اسپم: فعال/غیرفعال", callback_data="grp_toggle_spam")]
        ]
    )
    await message.reply(
        "🛠 **تنظیمات ربات در این گروه:**\n"
        "مدیر عزیز، از طریق دکمه‌های زیر می‌توانید قابلیت‌های مدیریتی این گروه را تنظیم کنید:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def main():
    server_thread = Thread(target=run_web_server, daemon=True)
    server_thread.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
