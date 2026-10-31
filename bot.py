import os
import cv2
import numpy as np
import threading
from flask import Flask
from telethon import TelegramClient, events

# اطلاعات تلگرام و توکن ربات
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
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
        raise ValueError("تصویر خوانده نشد یا فرمت آن پشتیبانی نمی‌شود.")
    
    height, width = img.shape[:2]
    new_width = width * 2
    new_height = height * 2
    
    # بزرگ‌نمایی با کیفیت بالا
    upscaled = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
    
    # اعمال فیلتر شارپ برای وضوح بیشتر جزئیات
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharp = cv2.filter2D(upscaled, -1, kernel)
    
    # ذخیره با بالاترین کیفیت خروجی
    cv2.imwrite(output_path, sharp, [cv2.IMWRITE_JPEG_QUALITY, 100])

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.respond(
        "سلام! ⚡\n"
        "برای اینکه عکس شما با **بالاترین کیفیت و بدون افت رزولوشن** پردازش شود، لطفاً آن را به صورت **فایل (Document)** بفرستید."
    )

@client.on(events.NewMessage(func=lambda e: e.photo or e.document))
async def photo_handler(event):
    sender = await event.get_sender()
    user_id = sender.id if sender else 'user'
    
    input_file = f"downloads_{user_id}.jpg"
    output_file = f"output_{user_id}.jpg"
    
    status_msg = await event.respond("⏳ در حال دریافت فایل با کیفیت اصلی...")
    
    try:
        # دانلود فایل یا عکس با حفظ کیفیت کامل
        await event.client.download_media(event.message, file=input_file)
        await status_msg.edit("⚙️ در حال پردازش و افزایش وضوح تصویر...")
        
        upscale_image(input_file, output_file)
        
        await status_msg.edit("📤 در حال ارسال تصویر نهایی به صورت فایل...")
        
        # ارسال به صورت فایل (Document) تا تلگرام کیفیت آن را فشرده نکند
        await event.respond(
            file=output_file,
            force_document=True,
            message="✨ تصویر باکیفیت شما آماده است."
        )
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit(f"❌ خطایی در پردازش رخ داد: {str(e)}")
        
    finally:
        # پاکسازی آنی فایل‌های موقت از سرور
        if os.path.exists(input_file):
            os.remove(input_file)
        if os.path.exists(output_file):
            os.remove(output_file)

if __name__ == "__main__":
    # اجرای وب‌سرویس در ترد جداگانه
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    print("ربات و وب‌سرویس روشن شدند...")
    client.start(bot_token=BOT_TOKEN)
    client.run_until_disconnected()
