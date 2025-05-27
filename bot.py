from pyrogram import Client, filters
import requests
import os

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Client("dood_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_api_keys = {} 

@bot.on_message(filters.command("start") & filters.private)
async def start(bot, message):
    await message.reply("👋 Halo! {message.chat.first_name}\nKirim `/api your_doodstream_api_key` untuk mulai.")

@bot.on_message(filters.command("api") & filters.private)
async def set_api(bot, message):
    try:
        api_key = message.text.split(" ", 1)[1]
        user_api_keys[message.from_user.id] = api_key
        await message.reply("✅ API key disimpan.")
    except IndexError:
        await message.reply("⚠️ Format salah. Gunakan: `/api your_api_key`")

@bot.on_message((filters.video | filters.document) & filters.private)
async def handle_video(bot, message):
    user_id = message.from_user.id
    api_key = user_api_keys.get(user_id)

    if not api_key:
        return await message.reply("❗ API key belum diset. Gunakan `/api your_key`.")

    await message.reply("📥 Mengunduh video...")
    file_path = await message.download()
    
    try:
        server = requests.get(f"https://doodapi.co/api/upload/server?key={api_key}").json()
        upload_url = server["result"]

        await message.reply("⏫ Mengunggah ke DoodStream...")
        with open(file_path, 'rb') as f:
            res = requests.post(f"{upload_url}?{api_key}", files={'file': f}, data={'api_key': api_key})
        result = res.json()

        if result.get("status") == 200:
            await message.reply(f"✅ Sukses!\n📎 Pesan: {result}")
        else:
            await message.reply(f"❌ Gagal upload:\n {result}")
    except Exception as e:
        await message.reply(f"❌ Terjadi kesalahan:\n {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

bot.run()
