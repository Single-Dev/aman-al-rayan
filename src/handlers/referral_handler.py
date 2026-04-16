from telegram import Update
from telegram.ext import ContextTypes
from src.database.db_manager import DatabaseManager
from src.utils.keyboards import get_main_menu_keyboard
from src.config import ADMIN_IDS, CONTACT_INFO


db = DatabaseManager()

async def handle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral status and sharing information."""
    try:
        user = update.effective_user
        bot = update.get_bot()
        referral_info = db.get_referral_info(user.id) or {}
        referral_code = referral_info.get('referral_code', f'ref{user.id}')
        balance = referral_info.get('referral_balance', 0.0)
        joins = referral_info.get('referral_joins', 0)

        if bot.username:
            referral_link = f"https://t.me/{bot.username}?start={referral_code}"
            message = (
                "🤝 *Referral Program*\n\n"
                f"*Your referral code:* `{referral_code}`\n"
                f"*Share link:* {referral_link}\n\n"
                f"*Current balance:* AED {balance:.2f}\n"
                f"*Referred clients:* {joins}\n\n"
                "Earn 20% of every confirmed deal made by clients you refer.\n\n"
                "To withdraw your balance, please contact our admin team:\n"
                f"• {CONTACT_INFO['phone']}\n"
                f"• {CONTACT_INFO['whatsapp']}\n\n"
                "You can also ask the admin to update your balance manually if needed."
            )
        else:
            message = (
                "🤝 *Referral Program*\n\n"
                f"*Your referral code:* `{referral_code}`\n\n"
                f"*Current balance:* AED {balance:.2f}\n"
                f"*Referred clients:* {joins}\n\n"
                "Earn 20% of every confirmed deal made by clients you refer.\n\n"
                "To withdraw your balance, please contact our admin team:\n"
                f"• {CONTACT_INFO['phone']}\n"
                f"• {CONTACT_INFO['whatsapp']}\n\n"
                "You can also ask the admin to update your balance manually if needed."
            )

        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text=message,
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                text=message,
                reply_markup=get_main_menu_keyboard()
            )
    except Exception as e:
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text=f"Sorry, an error occurred in referral: {str(e)}",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                text=f"Sorry, an error occurred in referral: {str(e)}",
                reply_markup=get_main_menu_keyboard()
            )

async def handle_set_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow admin to set referral balance for a user."""
    user = update.effective_user
    args = context.args or []

    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if len(args) < 2:
        await update.message.reply_text("Usage: /set_balance <user_id> <amount>")
        return

    try:
        target_user_id = int(args[0])
        amount = float(args[1])
    except ValueError:
        await update.message.reply_text("❌ Please provide a valid user ID and amount.")
        return

    target_user = db.get_user(target_user_id)
    if not target_user:
        await update.message.reply_text(f"❌ No user found with Telegram ID {target_user_id}.")
        return

    success = db.set_referral_balance(target_user_id, amount)
    if success:
        await update.message.reply_text(f"✅ Referral balance for {target_user_id} has been set to AED {amount:.2f}.")
        try:
            await update.get_bot().send_message(
                chat_id=target_user_id,
                text=(f"💰 Your referral balance has been updated by admin.\n\n"
                      f"New balance: AED {amount:.2f}\n\n"
                      "Please message the admin if you want to withdraw funds.")
            )
        except Exception:
            pass
    else:
        await update.message.reply_text("❌ Failed to update the referral balance. Please try again.")
