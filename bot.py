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
    """افزایش کیفیت هوشمند، حذف نویز و شارپ‌سازی پیشرفته تصویر با OpenCV"""
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError("تصویر خوانده نشد یا فرمت آن پشتیبانی نمی‌شود.")
    
    # ۱. حذف نویز و پیکسلی بودن اولیه تصویر (جهت پاکسازی افت کیفیت)
    denoised = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    
    # ۲. افزایش ابعاد تصویر با الگوریتم دقیق Lanczos4
    height, width = img.shape[:2]
    new_width = width * 2
    new_height = height * 2
    upscaled = cv2.resize(denoised, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
    
    # ۳. بهبود هوشمند کنتراست موضعی (CLAHE) برای نمایان شدن جزئیات پنهان
    lab = cv2.cvtColor(upscaled, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    
    # ۴. شارپ‌سازی پیشرفته (Unsharp Masking) برای ایجاد وضوح واقعی و لبه‌های کاملاً شفاف
    gaussian = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
    sharp = cv2.addWeighted(enhanced, 1.6, gaussian, -0.6, 0)
    
    # ذخیره فایل با بالاترین کیفیت ممکن
    cv2.imwrite(output_path, sharp, [cv2.IMWRITE_JPEG_QUALITY, 100])

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.respond(
        "سلام! ⚡\n"
        "برای افزایش کیفیت **هوشمند و واقعی** عکس، آن را به صورت **فایل (Document)** بفرستید تا بدون افت فشرده‌سازی تلگرام پردازش شود."
    )

@client.on(events.NewMessage(func=lambda e: e.photo or e.document))
async def photo_handler(event):
    sender = await event.get_sender()
    user_id = sender.id if sender else 'user'
    
    input_file = f"downloads_{user_id}.jpg"
    output_file = f"output_{user_id}.jpg"
    
    status_msg = await event.respond("⏳ در حال دریافت فایل و اعمال پردازش هوشمند کیفیت...")
    
    try:
        await event.client.download_media(event.message, file=input_file)
        await status_msg.edit("⚙️ در حال حذف نویز، تنظیم کنتراست و افزایش وضوح...")
        
        upscale_image(input_file, output_file)
        
        await status_msg.edit("📤 در حال ارسال فایل باکیفیت نهایی...")
        
        await event.respond(
            file=output_file,
            force_document=True,
            message="✨ تصویر شما با افزایش کیفیت هوشمند آماده شد."
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
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    
    print("ربات و وب‌سرویس روشن شدند...")
    client.start(bot_token=BOT_TOKEN)
    client.run_until_disconnected()
