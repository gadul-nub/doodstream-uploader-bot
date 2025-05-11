import os
import asyncio
import logging
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

    waiting_msg = await update.message.reply_text("⏳ Sedang mengunggah videomu ke DoodStream...")

    asyncio.create_task(process_upload(context, update, video, api_key, waiting_msg.message_id))

async def process_upload(context, update, video, api_key, reply_to_msg_id):
    file = await context.bot.get_file(video.file_id)
    file_path = f"{video.file_unique_id}.mp4"
    await file.download_to_drive(file_path)

    try:
        server_resp = requests.get(f"https://doodapi.co/api/upload/server?key={api_key}")
        server_data = server_resp.json()
        if server_data.get("status") != 200:
            return await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Gagal mengambil server upload.", reply_to_message_id=reply_to_msg_id)

        upload_url = server_data["result"] + f"?{api_key}"
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"api_key": api_key}
            upload_resp = requests.post(upload_url, files=files, data=data)

        result = upload_resp.json()
        if result.get("status") == 200 and "result" in result:
            link = result["result"][0].get("download_url")
            return await context.bot.send_message(chat_id=update.effective_chat.id, text=f"✅ Upload sukses!\n📎 Link: {link}", reply_to_message_id=reply_to_msg_id)
        else:
            return await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ Upload gagal. Coba lagi.", reply_to_message_id=reply_to_msg_id)

    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"❌ Terjadi kesalahan: {e}", reply_to_message_id=reply_to_msg_id)

    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("api", save_api_key))
app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_video))
app.run_polling()
