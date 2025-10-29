cat > payments.py << 'EOF'
import os
import requests
import logging
from datetime import datetime, timedelta
from telegram import LabeledPrice, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, MessageHandler, filters, PreCheckoutQueryHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoPayments:
    def __init__(self):
        self.api_key = os.getenv("NOWPAYMENTS_API_KEY")
        self.base_url = "https://api.nowpayments.io/v1"
    
    async def create_crypto_invoice(self, user_id, amount_usd=10.00):
        try:
            payload = {
                "price_amount": amount_usd,
                "price_currency": "usd", 
                "pay_currency": "usdt",
                "order_id": f"vip_{user_id}_{int(datetime.now().timestamp())}",
                "order_description": "VIP Channel Access - 1 Month",
                "ipn_callback_url": f"{os.getenv('WEBHOOK_URL', 'https://your-app.onrender.com')}/crypto_webhook",
                "success_url": f"https://t.me/your_bot?start=payment_success",
                "cancel_url": f"https://t.me/your_bot?start=payment_cancelled"
            }
            
            headers = {"x-api-key": self.api_key}
            response = requests.post(f"{self.base_url}/invoice", json=payload, headers=headers)
            
            if response.status_code == 201:
                data = response.json()
                return {
                    "success": True,
                    "invoice_url": data.get("invoice_url"),
                    "payment_id": data.get("id"),
                    "amount_usd": amount_usd,
                    "pay_currency": "USDT",
                    "wallet_address": data.get("pay_address"),
                    "expiry": datetime.now() + timedelta(hours=1)
                }
            else:
                logger.error(f"Crypto API error: {response.text}")
                return {"success": False, "error": "Payment service unavailable"}
                
        except Exception as e:
            logger.error(f"Crypto payment error: {e}")
            return {"success": False, "error": "Payment system error"}

class TelegramStarsManager:
    async def create_stars_invoice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        context.user_data["pending_payment"] = {
            "user_id": user_id,
            "type": "stars",
            "timestamp": datetime.now()
        }
        
        title = "🌟 VIP Channel Access"
        description = "1 month access to exclusive VIP content and features"
        payload = f"vip_access_{user_id}_{int(datetime.now().timestamp())}"
        currency = "XTR"
        prices = [LabeledPrice("VIP Access (1 Month)", 100)]
        
        await context.bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=os.getenv("TELEGRAM_STARS_TOKEN"),
            currency=currency,
            prices=prices,
            start_parameter="vip-subscription"
        )

class PaymentHandler:
    def __init__(self):
        self.crypto = CryptoPayments()
        self.stars = TelegramStarsManager()
    
    async def show_payment_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            ["⭐ Pay with Telegram Stars"],
            ["🪙 Pay with Crypto (USDT)"],
            ["❌ Cancel"]
        ]
        
        await update.message.reply_text(
            "💰 *Choose Payment Method*\n\n"
            "⭐ *Telegram Stars* - Instant access, paid with Stars\n"
            "🪙 *Crypto* - Pay with USDT (TRC20)\n\n"
            "VIP Access: $10/month",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
            parse_mode="Markdown"
        )
    
    async def handle_payment_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        choice = update.message.text
        user_id = update.effective_user.id
        
        if "Stars" in choice:
            await self.stars.create_stars_invoice(update, context)
        elif "Crypto" in choice:
            await self.handle_crypto_payment(update, context, user_id)
        elif "Cancel" in choice:
            await update.message.reply_text("Payment cancelled.", reply_markup=ReplyKeyboardRemove())
    
    async def handle_crypto_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        payment_data = await self.crypto.create_crypto_invoice(user_id)
        
        if payment_data["success"]:
            context.user_data["pending_crypto_payment"] = {
                **payment_data,
                "user_id": user_id,
                "timestamp": datetime.now()
            }
            
            message = (
                "🪙 *Crypto Payment Instructions*\n\n"
                f"*Amount:* ${payment_data['amount_usd']} USDT\n"
                f"*Network:* TRC20 (Tron)\n"
                f"*Wallet Address:*\n`{payment_data['wallet_address']}`\n\n"
                f"📍 *Send exact amount to the address above*\n"
                f"⏰ *Expires in:* 1 hour\n\n"
                f"After sending, use /check_payment to verify"
            )
            
            await update.message.reply_text(message, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        else:
            await update.message.reply_text("❌ Crypto payment service unavailable. Try Telegram Stars.", reply_markup=ReplyKeyboardRemove())
    
    async def check_crypto_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if "pending_crypto_payment" not in context.user_data:
            await update.message.reply_text("No pending payment found.")
            return
        
        await update.message.reply_text(
            "🔍 *Payment Status Check*\n\n"
            "For automatic verification, we're setting up instant confirmation.\n\n"
            "In the meantime, please send your transaction hash to @admin for manual verification.",
            parse_mode="Markdown"
        )

async def stars_pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def stars_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    await grant_vip_access(user_id, duration_days=30)
    
    await update.message.reply_text(
        "🎉 *Payment Successful!*\n\nYou now have VIP access for 1 month!\n\nUse /vip to access exclusive content.",
        parse_mode="Markdown"
    )
    
    if "pending_payment" in context.user_data:
        del context.user_data["pending_payment"]

async def grant_vip_access(user_id: int, duration_days: int = 30):
    expiry_date = datetime.now() + timedelta(days=duration_days)
    logger.info(f"Granted VIP access to user {user_id} until {expiry_date}")

def setup_payment_handlers(application):
    payment_handler = PaymentHandler()
    
    application.add_handler(MessageHandler(
        filters.Regex("^(💰 Buy VIP Access|/buy)$"), 
        payment_handler.show_payment_options
    ))
    
    application.add_handler(MessageHandler(
        filters.Regex("^(⭐ Pay with Telegram Stars|🪙 Pay with Crypto|❌ Cancel)$"),
        payment_handler.handle_payment_choice
    ))
    
    application.add_handler(MessageHandler(
        filters.Regex("^/check_payment$"),
        payment_handler.check_crypto_payment
    ))
    
    application.add_handler(PreCheckoutQueryHandler(stars_pre_checkout))
    application.add_handler(MessageHandler(
        filters.SUCCESSFUL_PAYMENT, 
        stars_successful_payment
    ))
EOF
