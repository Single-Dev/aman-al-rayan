import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.database.db_manager import DatabaseManager
from src.utils.keyboards import get_main_menu_keyboard
from src.config import ADMIN_IDS, CONTACT_INFO
from html import escape

logger = logging.getLogger(__name__)
db = DatabaseManager()

async def handle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed referral status and statistics."""
    try:
        user = update.effective_user
        bot = update.get_bot()
        
        # Get detailed stats from database
        stats = db.get_detailed_referral_stats(user.id)
        if not stats:
            # Fallback if user doesn't exist in DB yet
            db.add_or_update_user(user.id, user.username, user.first_name, user.last_name)
            stats = db.get_detailed_referral_stats(user.id)
            
        if not stats:
            raise ValueError("Could not retrieve referral statistics")

        referral_code = stats.get('referral_code', f'ref{user.id}')
        balance = stats.get('referral_balance', 0.0)
        joins = stats.get('referral_joins', 0)
        total_earnings = stats.get('total_earnings', 0.0)
        referred_users = stats.get('referred_users', [])
        
        if bot.username:
            referral_link = f"https://t.me/{bot.username}?start={referral_code}"
            link_section = f"🔗 <b>Share Link:</b> {escape(referral_link)}\n"
        else:
            link_section = ""

        # Build premium message with HTML
        message = (
            "🤝 <b>Referral Program</b>\n\n"
            "Earn <b>20% commission</b> for every confirmed deal from clients you refer!\n\n"
            f"🎫 <b>Your Referral Code:</b> <code>{escape(str(referral_code))}</code>\n"
            f"{link_section}\n"
            "📊 <b>Your Statistics:</b>\n"
            f"• Referred Clients: <code>{joins}</code>\n"
            f"• Current Balance: <code>AED {balance:.2f}</code>\n"
            f"• Total Earned: <code>AED {total_earnings:.2f}</code>\n\n"
        )

        if referred_users:
            message += "👥 <b>Recent Referrals:</b>\n"
            # Show last 5 referrals
            for ref_user in referred_users[:5]:
                name = escape(ref_user.get('first_name') or "User")
                date_str = ref_user.get('created_at', '')
                date = date_str.split(' ')[0] if date_str else "N/A"
                message += f"• {name} (Joined: {date})\n"
            message += "\n"

        message += (
            "💰 <b>How to Withdraw?</b>\n"
            "Contact our admin team to claim your rewards:\n"
            f"• {CONTACT_INFO['phone']}\n"
            f"• {CONTACT_INFO['whatsapp']} (WhatsApp)\n"
        )

        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                text=message,
                parse_mode='HTML',
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                text=message,
                parse_mode='HTML',
                reply_markup=get_main_menu_keyboard()
            )
    except Exception as e:
        logger.error(f"Error in handle_referral: {e}", exc_info=True)
        error_msg = f"❌ Error fetching referral details: {escape(str(e))}"
        if update.callback_query:
            try:
                await update.callback_query.answer()
                await update.callback_query.edit_message_text(text=error_msg, parse_mode='HTML', reply_markup=get_main_menu_keyboard())
            except Exception:
                pass
        else:
            await update.message.reply_text(text=error_msg, parse_mode='HTML', reply_markup=get_main_menu_keyboard())

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
