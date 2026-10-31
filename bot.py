import os
import cv2
import threading
from flask import Flask
from telethon import TelegramClient, events

# اطلاعات تلگرام و توکن ربات
API_ID = 611335
API_HASH = "d524b414d21f4d37f08684c1df41ac9d"
BOT_TOKEN = "9232669247:AAGhQMuFITXbT-w-G-4qsAB9njUPFNO9y-E"

# پورت وب‌سرویس برای رندر
PORT = int(os.environ.get("PORT", 10000))

# راه‌اندازی سرور وب فلاسْک روی ترد اصلی برای پاسخ به رندر
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Robot is up and running!"

def run_web():
    web_app.run(host="0.0.0.0", port=PORT)

# راه‌اندازی کلاینت ربات با Telethon
client = TelegramClient('bot_session', API_ID, API_HASH)

def upscale_image(input_path: str, output_path: str):
    """افزایش کیفیت و وضوح تصویر با الگوریتم‌های OpenCV"""
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError("تصویر خوانده نشد.")
    
    height, width = img.shape[:2]
    new_width = width * 2
    new_height = height * 2
    
    upscaled = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
    
    gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    sharp = cv2.convertScaleAbs(upscaled - 0.3 * cv2.cvtColor(laplacian, cv2.COLOR_GRAY2BGR))
    
    cv2.imwrite(output_path, sharp)

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.respond(
        "سلام! ⚡\n"
        "عکس خود را بفرستید تا کیفیت و رزولوشن آن را به صورت هوشمند افزایش دهم."
    )

@client.on(events.NewMessage(func=lambda e: e.photo or e.document))
async def photo_handler(event):
    sender = await event.get_sender()
    user_id = sender.id if sender else 'user'
    
    input_file = f"downloads_{user_id}.jpg"
    output_file = f"output_{user_id}.jpg"
    
    status_msg = await event.respond("⏳ در حال دریافت و پردازش تصویر...")
    
    try:
        await event.client.download_media(event.message, file=input_file)
        await status_msg.edit("⚙️ در حال اعمال الگوریتم‌های افزایش کیفیت...")
        
        upscale_image(input_file, output_file)
        
        await status_msg.edit("📤 در حال ارسال تصویر نهایی...")
        await event.respond(
            file=output_file,
            message="✨ تصویر شما با موفقیت افزایش کیفیت پیدا کرد."
        )
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit(f"❌ خطایی در پردازش رخ داد: {str(e)}")
        
    finally:
        # پاکسازی آنی و ایمن فایل‌های موقت از سرور
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == "__main__":
    # اجرای وب‌سرویس در ترد جداگانه
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    print("ربات و وب‌سرویس روشن شدند...")
    # راه‌اندازی کلاینت تلگرام و اتصال
    client.start(bot_token=BOT_TOKEN)
    client.run_until_disconnected()
