cat > bot.py << 'EOF'
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from payments import setup_payment_handlers

load_dotenv()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["💰 Buy VIP Access"], ["ℹ️ Info"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Welcome to VIP Channel Bot! Get exclusive access to premium content.",
        reply_markup=reply_markup
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌟 VIP Channel Bot\n\n"
        "Get access to exclusive content, early features, and premium community.\n\n"
        "Click 'Buy VIP Access' to get started!"
    )

def main():
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(MessageHandler(filters.Regex("^(ℹ️ Info|/info)$"), info))
    
    setup_payment_handlers(application)
    
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
EOF
