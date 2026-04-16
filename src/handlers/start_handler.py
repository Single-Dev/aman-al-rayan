from telegram import Update
from telegram.ext import ContextTypes
from src.database.db_manager import DatabaseManager
from src.utils.keyboards import get_main_menu_keyboard
from src.utils.messages import get_welcome_message
from src.config import ADMIN_IDS


db = DatabaseManager()

async def send_referral_notifications(new_user: dict, referrer: dict, bot):
    """Notify admin and referrer when a new client joins by referral."""
    referrer_username = f"@{referrer.get('username')}" if referrer.get('username') else f"User ID {referrer.get('user_id')}"
    new_user_tag = f"@{new_user.get('username')}" if new_user.get('username') else f"User ID {new_user.get('user_id')}"

    invitation_message = (
        "🎉 A new client joined using your referral code!\n\n"
        f"• Client: {new_user_tag}\n"
        f"• Client ID: {new_user.get('user_id')}\n"
        "• Referral Reward: 20% of their confirmed deal amount\n\n"
        "We will notify you when they make a confirmed deal."
    )

    await bot.send_message(chat_id=referrer['user_id'], text=invitation_message)

    if ADMIN_IDS:
        admin_message = (
            "📣 New referral signup!\n\n"
            f"• New client: {new_user_tag} (ID: {new_user.get('user_id')})\n"
            f"• Referred by: {referrer_username} (ID: {referrer.get('user_id')})\n"
            "• Reward: 20% of confirmed deal value\n"
        )

        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(chat_id=int(admin_id), text=admin_message)
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
