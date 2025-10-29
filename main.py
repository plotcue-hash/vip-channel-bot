from pyrogram import Client, filters
import os

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

bot = Client("vip_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@bot.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_text(
        "👋 Welcome to the VIP Channel Bot!\n\n"
        "To get VIP access, please complete your payment.\n"
        "Once payment is confirmed, you’ll receive your exclusive link 💎"
    )

bot.run()
