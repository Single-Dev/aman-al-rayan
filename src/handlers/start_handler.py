from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database.db_manager import DatabaseManager
from src.utils.keyboards import get_main_menu_keyboard
from src.utils.messages import get_welcome_message
from src.config import ADMIN_IDS, MINI_APP_URL


db = DatabaseManager()

async def send_referral_notifications(new_user: dict, referrer: dict, bot):
    """Notify admin and referrer when a new client joins by referral."""
    referrer_name = f"{referrer.get('first_name') or ''} {referrer.get('last_name') or ''}".strip() or "Unknown"
    referrer_tag = f"@{referrer.get('username')}" if referrer.get('username') else f"ID: {referrer.get('user_id')}"
    
    new_user_name = f"{new_user.get('first_name') or ''} {new_user.get('last_name') or ''}".strip() or "Unknown"
    new_user_tag = f"@{new_user.get('username')}" if new_user.get('username') else f"ID: {new_user.get('user_id')}"

    invitation_message = (
        "🎉 **New Referral Signup!**\n\n"
        f"👤 **New Client:** {new_user_name} ({new_user_tag})\n"
        f"🤝 **Invited By:** {referrer_name} ({referrer_tag})\n"
        "💰 **Potential Reward:** 20% of their first confirmed deal\n\n"
        "We will notify you when they complete a booking!"
    )

    # Notify Referrer
    try:
        await bot.send_message(chat_id=referrer['user_id'], text=invitation_message, parse_mode='Markdown')
    except Exception:
        pass

    # Notify Admin
    if ADMIN_IDS:
        admin_message = (
            "🚀 **Detailed Referral Notification**\n\n"
            "📈 **Signup Event**\n"
            f"• **New User:** {new_user_name}\n"
            f"• **User ID:** `{new_user.get('user_id')}`\n"
            f"• **Username:** {new_user_tag}\n\n"
            f"🔗 **Referrer:** {referrer_name}\n"
            f"• **Referrer ID:** `{referrer.get('user_id')}`\n"
            f"• **Referrer Username:** {referrer_tag}\n"
            "───────────────────\n"
            "Status: Awaiting first booking..."
        )

        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(chat_id=int(admin_id), text=admin_message, parse_mode='Markdown')
            except Exception:
                pass

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    referral_arg = context.args[0] if context.args else None
    existing_user = db.get_user(user.id)

    referrer_id = None
    if referral_arg:
        referral_code = referral_arg
        if referral_code.startswith('ref'):
            referral_code = referral_code[3:]
        if referral_code.isdigit():
            referrer_id = int(referral_code)
        else:
            referrer = db.get_user_by_referral_code(referral_arg)
            if referrer:
                referrer_id = referrer['user_id']

    if referrer_id == user.id:
        referrer_id = None

    db.add_or_update_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        referrer_id=referrer_id
    )

    if referrer_id and not existing_user:
        referrer = db.get_user(referrer_id)
        if referrer:
            db.increment_referral_joins(referrer_id)
            new_user = db.get_user(user.id)
            await send_referral_notifications(new_user, referrer, update.get_bot())

    welcome_message = get_welcome_message(user.first_name or "Friend")

    # Use MINI_APP_URL from config
    from src.config import MINI_APP_URL
    
    # Send welcome message with main menu keyboard
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command or help button"""
    from src.utils.messages import get_help_message
    
    help_message = get_help_message()
    
    await update.message.reply_text(
        help_message,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )
