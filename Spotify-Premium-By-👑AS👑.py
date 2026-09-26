import logging
import threading
import time
import requests
from flask import Flask
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# --- FLASK WEB SERVER FOR RENDER ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Spotify Bot is running fine!"

def run_flask():
    app_flask.run(host="0.0.0.0", port=10000)

# --- CONFIGURATION DETAILS ---
BOT_TOKEN = "8882295285:AAEbOoRjPWQFdFJD9-3CZV2Uohue8brUEiI"
ADMIN_ID = 8313247547
UPI_ID = "7276052050@fam"
AMOUNT = 50
FILE_LINK = "https://t.me/+yllpACDskUFiNGE1"

RENDER_APP_URL = "https://spotify-tele-bot.onrender.com"

USER_DATA = {}

def keep_alive():
    while True:
        time.sleep(120)
        try:
            requests.get(RENDER_APP_URL)
        except Exception:
            pass

QR_CODE_URL = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={UPI_ID}%26pn=Merchant%26am={AMOUNT}%26cu=INR"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- CUSTOMER FLOW ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USER_DATA[user.id] = {"step": "WAITING_PHOTO"}
    
    msg = (
        f"Aapka swagat hai, {user.first_name}!\n\n"
        f"Spotify Premium (Lifetime With Updates) Lene ke liye aapko **₹{AMOUNT}** ka payment karna hoga.\n"
        f"📌 **UPI ID:** `{UPI_ID}`\n\n"
        f"Upar diye gaye QR Code ko scan karke payment karein. **Kripya exact ₹{AMOUNT} hi bhejein.**\n\n"
        f"Payment karne ke baad, Payment ka **Screenshot** yahan bhejein.\n\n"
        f"👑 Owner - Aditya Services (@asoffcial) 👑"
    )
    
    await update.message.reply_photo(
        photo=QR_CODE_URL,
        caption=msg,
        parse_mode="Markdown"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in USER_DATA and USER_DATA[user.id].get("step") == "WAITING_PHOTO":
        photo_id = update.message.photo[-1].file_id
        USER_DATA[user.id]["photo_id"] = photo_id
        USER_DATA[user.id]["step"] = "WAITING_UTR"
        
        await update.message.reply_text(
            "Screenshot mil gaya hai! Ab kripya apna **12-digit UTR / Transaction No** yahan type karke bhejein:"
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    
    if user.id in USER_DATA and USER_DATA[user.id].get("step") == "WAITING_UTR":
        photo_id = USER_DATA[user.id].get("photo_id")
        
        # Confirmation to Customer
        await update.message.reply_text(
            "Wait Until Your Payment Is Verified , You Will Receive Your File Whithin 1 Hour"
        )
        
        # Admin Notification
        admin_caption = (
            f"🎵 **Naya Spotify Premium Payment Request!**\n\n"
            f"👤 **User:** {user.first_name} (@{user.username})\n"
            f"🆔 **User ID:** `{user.id}`\n"
            f"💳 **Amount:** ₹{AMOUNT}\n"
            f"🔢 **UTR Number:** `{text}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⚙️ **Action Commands (Click to Copy):**\n"
            f"✅ Approve: `/approve {user.id}`\n"
            f"❌ Reject: `/reject {user.id}`"
        )

        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_id,
            caption=admin_caption,
            parse_mode="Markdown"
        )
        
        USER_DATA.pop(user.id, None)

# --- ADMIN COMMANDS ---
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if len(context.args) == 0:
        await update.message.reply_text("❌ Kripya User ID bhi dalein!\nExample: `/approve 12345678`", parse_mode="Markdown")
        return

    target_id = int(context.args[0])

    try:
        # Send New Spotify Channel Link to Customer
        await context.bot.send_message(
            chat_id=target_id,
            text=f"✅ **Aapka Spotify Premium payment successfully verify ho gaya hai!**\n\n📁 **Aapki File Ka Channel Link:**\n{FILE_LINK}"
        )
        await update.message.reply_text(f"✅ Successful! User `{target_id}` ko Spotify link bhej diya gaya hai.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error sending link: `{e}`", parse_mode="Markdown")

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) == 0:
        await update.message.reply_text("❌ Kripya User ID bhi dalein!\nExample: `/reject 12345678`", parse_mode="Markdown")
        return

    target_id = int(context.args[0])

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text="❌ Aapka payment verify nahi ho paya. Kripya sahi UTR aur Screenshot ke sath dobara koshish karein."
        )
        await update.message.reply_text(f"❌ User `{target_id}` ka request reject kar diya gaya hai.", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: `{e}`", parse_mode="Markdown")

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("reject", reject))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Spotify Bot is live...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    