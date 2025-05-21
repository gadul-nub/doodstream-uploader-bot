import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TELEGRAM_TOKEN = "8160463425:AAGyXQ99qTTEI8yt_kr0BVDBiPJu8TngUJs"

user_api_keys = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Halo! Kirim token API DoodStream kamu dulu dengan format:\n" "/api KEY_KAMU")

async def save_api_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return await update.message.reply_text("Format salah! Gunakan: /api KEY_KAMU")
    user_api_keys[update.effective_user.id] = context.args[0]
    await update.message.reply_text("✅ API key tersimpan. Silakan kirim video untuk diunggah.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    api_key = user_api_keys.get(user_id)
    if not api_key:
        return await update.message.reply_text("🚫 Kamu belum mengatur API key. Gunakan /api KEY_KAMU dulu.")

    video = update.message.video or update.message.document
    if not video:
        return await update.message.reply_text("🚫 Silakan kirim file video.")

    file = await context.bot.get_file(video.file_id)
    file_url = file.file_path

    await update.message.reply_text("⏳ Mencoba unggah file langsung dari URL Telegram...")

    response = requests.get(f"https://doodapi.co/api/upload/url?key={api_key}&url={file_url}")

    result = response.json()
    if result.get("status") == 200 and isinstance(result.get("result"), list):
        if result["result"]:
            return await update.message.reply_text(f"✅ Upload sukses!\n📎 Link: {result}")
        else:
            return await update.message.reply_text("⚠️ Respons kosong dari DoodStream. Mungkin file tidak diterima.")
    else:
        await update.message.reply_text("❌ Upload via URL gagal.")
        await update.message.reply_text(f"🧾 Detail: {result}")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("api", save_api_key))
app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))

app.run_polling()
