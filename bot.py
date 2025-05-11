import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TELEGRAM_TOKEN = "your token telegram bot"

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
    file_path = f"{video.file_unique_id}.mp4"
    await file.download_to_drive(file_path)

    try:
        # 1. Ambil server upload dari DoodStream
        server_resp = requests.get(f"https://doodapi.com/api/upload/server?key={api_key}")
        server_data = server_resp.json()
        if server_data.get("status") != 200:
            return await update.message.reply_text("❌ Gagal mengambil server upload. Periksa API key kamu.")

        upload_url = server_data["result"] + f"?{api_key}"

        # 2. Upload ke DoodStream
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"api_key": api_key}
            upload_resp = requests.post(upload_url, files=files, data=data)

        result = upload_resp.json()
        if result.get("status") == 200 and "result" in result:
            file_info = result["result"][0]
            link = file_info.get("download_url")
            await update.message.reply_text(f"✅ Upload sukses!\n📎 Link: {link}")
        else:
            await update.message.reply_text("❌ Upload gagal. Coba ulangi.")
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi kesalahan saat upload:e")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

#Jalankan bot
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("api", save_api_key))
app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
app.run_polling()
