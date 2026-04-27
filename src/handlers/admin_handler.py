from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database.db_manager import DatabaseManager
from src.config import ADMIN_IDS
import logging

db = DatabaseManager()
logger = logging.getLogger(__name__)

async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command for admins"""
    user = update.effective_user

    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to access the admin panel.")
        return

    keyboard = [
        [InlineKeyboardButton("👥 View All Users", callback_data="admin_view_users")],
        [InlineKeyboardButton("💰 Change User Balance", callback_data="admin_manage_balances")],
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_statistics")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔧 *Admin Panel*\n\n"
        "Choose an option:\n\n"
        "*Quick Command:*\n"
        "/setbalance <user_id> <amount>\n\n"
        "Example: /setbalance 123456789 500",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_setbalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /setbalance command for admin to set user balance directly"""
    user = update.effective_user

    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    # Get arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Invalid format!\n\n"
            "Usage: /setbalance <user_id> <amount>\n\n"
            "Example: /setbalance 123456789 500.00"
        )
        logger.warning(f"Invalid setbalance command from admin {user.id}: args={context.args}")
        return

    try:
        target_user_id = int(context.args[0])
        amount = float(context.args[1])

        if amount < 0:
            await update.message.reply_text("❌ Amount must be positive!")
            return
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid input!\n\n"
            "User ID must be a number and amount must be a valid number.\n\n"
            "Usage: /setbalance 123456789 500.00"
        )
        logger.warning(f"Invalid setbalance values from admin {user.id}: {context.args}")
        return

    # Check if user exists
    target_user = db.get_user(target_user_id)
    if not target_user:
        await update.message.reply_text(f"❌ User {target_user_id} not found in the database.")
        logger.warning(f"Admin {user.id} tried to set balance for non-existent user {target_user_id}")
        return

    # Update balance
    logger.info(f"Admin {user.id} attempting to set balance for user {target_user_id} to {amount}")
    success = db.set_referral_balance(target_user_id, amount)

    if success:
        # Notify admin
        await update.message.reply_text(
            f"✅ *Balance Updated Successfully!*\n\n"
            f"User: {target_user.get('first_name', 'N/A')} {target_user.get('last_name', 'N/A')}\n"
            f"User ID: {target_user_id}\n"
            f"New Balance: AED {amount:.2f}",
            parse_mode='Markdown'
        )

        # Notify user
        try:
            await update.get_bot().send_message(
                chat_id=target_user_id,
                text=f"💰 *Balance Updated*\n\n"
                     f"Your referral balance has been updated to: *AED {amount:.2f}*\n\n"
                     f"Thank you!",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")
            await update.message.reply_text(f"⚠️ Balance updated but couldn't notify user (user might have blocked bot).")

        logger.info(f"Balance successfully updated for user {target_user_id}: AED {amount}")
    else:
        await update.message.reply_text(
            f"❌ *Failed to update balance*\n\n"
            f"There was a database error. Please check the logs.",
            parse_mode='Markdown'
        )
        logger.error(f"Failed to set balance for user {target_user_id} to {amount}")


async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin panel callbacks"""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await query.edit_message_text("❌ You are not authorized.")
        return

    data = query.data

    if data == "admin_manage_balances":
        await show_balance_management(query, context)
    elif data == "admin_statistics":
        await show_statistics(query, context)
    elif data == "back_to_main":
        from src.utils.keyboards import get_main_menu_keyboard
        await query.edit_message_text(
            "Welcome back to the main menu!",
            reply_markup=None
        )
        await query.message.reply_text(
            "Choose an option from the main menu below.",
            reply_markup=get_main_menu_keyboard()
        )
    elif data == "back_to_admin":
        await handle_back_to_admin(query, context)
    elif data == "admin_view_users":
        await show_users_list(query, context, page=0)
    elif data.startswith("user_page_"):
        page = int(data.split("_")[-1])
        await show_users_list(query, context, page=page)
    elif data.startswith("view_user_"):
        user_id = int(data.split("_")[-1])
        await show_user_details(query, context, user_id)
    elif data.startswith("edit_balance_"):
        user_id = int(data.split("_")[-1])
        await prompt_balance_edit(query, context, user_id)

async def show_users_list(query, context, page=0):
    """Show paginated list of users"""
    users_per_page = 5
    offset = page * users_per_page

    # Get total users count
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    conn.close()

    # Get users for this page
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT user_id, username, first_name, last_name, referral_balance, referral_joins
        FROM users
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, (users_per_page, offset))
    users = cursor.fetchall()
    conn.close()

    text = f"👥 *Users List* (Page {page + 1})\n\n"
    keyboard = []

    for user in users:
        name = user['username'] or f"{user['first_name']} {user['last_name'] or ''}".strip()
        balance = user['referral_balance'] or 0.0
        joins = user['referral_joins'] or 0
        text += f"👤 {name} (ID: {user['user_id']})\n"
        text += f"   Balance: AED {balance:.2f} | Referrals: {joins}\n\n"

        keyboard.append([
            InlineKeyboardButton(
                f"👁️ View {name}",
                callback_data=f"view_user_{user['user_id']}"
            )
        ])

    # Pagination buttons
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"user_page_{page-1}"))
    if offset + users_per_page < total_users:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"user_page_{page+1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([InlineKeyboardButton("🔙 Back to Admin", callback_data="back_to_admin")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def show_user_details(query, context, user_id):
    """Show detailed information about a user"""
    stats = db.get_detailed_referral_stats(user_id)

    if not stats:
        await query.edit_message_text(
            "❌ User not found.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Users", callback_data="admin_view_users")
            ]])
        )
        return

    text = "👤 *User Details*\n\n"
    text += f"**ID:** {stats['user_id']}\n"
    text += f"**Name:** {stats['first_name']} {stats['last_name'] or ''}\n"
    if stats['username']:
        text += f"**Username:** @{stats['username']}\n"
    if stats['phone_number']:
        text += f"**Phone:** {stats['phone_number']}\n"
    if stats['email']:
        text += f"**Email:** {stats['email']}\n"
    text += f"**Referral Code:** {stats['referral_code']}\n"
    text += f"**Current Balance:** AED {stats['referral_balance']:.2f}\n"
    text += f"**Referred Users:** {stats['referral_joins']}\n"
    text += f"**Total Deals:** {stats['total_deals']}\n"
    text += f"**Total Earnings:** AED {stats['total_earnings']:.2f}\n"
    text += f"**Total Deal Value:** AED {stats['total_deal_value']:.2f}\n"
    text += f"**Joined:** {stats['created_at']}\n\n"

    if stats.get('referred_users'):
        text += "🤝 **Users Invited:**\n"
        for ref_user in stats['referred_users'][:10]:  # Show last 10
            ref_name = ref_user['username'] or ref_user['first_name']
            text += f"• {ref_name} (ID: `{ref_user['user_id']}`)\n"
        if len(stats['referred_users']) > 10:
            text += f"• _...and {len(stats['referred_users']) - 10} more_\n"
        text += "\n"

    if stats.get('earnings_history'):
        text += "💰 **Earnings History:**\n"
        for earn in stats['earnings_history'][:10]:  # Show last 10
            text += f"• AED {earn['reward_amount']:.2f} from {earn['referred_name']}\n"
        if len(stats['earnings_history']) > 10:
            text += f"• _...and {len(stats['earnings_history']) - 10} more_\n"
        text += "\n"

    keyboard = [
        [InlineKeyboardButton("💰 Edit Balance", callback_data=f"edit_balance_{user_id}")],
        [InlineKeyboardButton("🔙 Back to Users", callback_data="admin_view_users")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def prompt_balance_edit(query, context, user_id):
    """Prompt admin to enter new balance"""
    stats = db.get_detailed_referral_stats(user_id)
    if not stats:
        await query.edit_message_text("❌ User not found.")
        return

    context.user_data['editing_balance_user_id'] = user_id

    text = f"💰 *Edit Balance for {stats['first_name']} {stats['last_name'] or ''}*\n\n"
    text += f"Current Balance: AED {stats['referral_balance']:.2f}\n\n"
    text += "Please enter the new balance amount (e.g., 150.50):\n\n"
    text += "_Send the amount as a message_"

    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data=f"view_user_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def prompt_set_balance_by_id(query, context):
    """Prompt admin to enter a user chat ID and amount"""
    context.user_data['admin_set_balance_pending'] = True

    text = (
        "💰 *Set Balance by Chat ID*\n\n"
        "Send the user chat ID and new balance in one message, for example:\n"
        "`123456789 150.00`\n\n"
        "You can also use /set_balance <user_id> <amount> directly."
    )
    keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="back_to_admin")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_admin_set_balance_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin input for setting balance by chat ID"""
    user = update.effective_user

    logger.info(f"Balance message handler called - User ID: {user.id}, Admin IDs: {ADMIN_IDS}, Flag: {context.user_data.get('admin_set_balance_pending')}")

    if user.id not in ADMIN_IDS:
        logger.warning(f"User {user.id} is not an admin")
        return

    if not context.user_data.get('admin_set_balance_pending'):
        logger.info(f"Balance pending flag not set for user {user.id}")
        return

    logger.info(f"Processing balance update for user {user.id}")
    context.user_data.pop('admin_set_balance_pending', None)

    parts = update.message.text.strip().split()
    if len(parts) != 2:
        await update.message.reply_text(
            "❌ Please send exactly two values: the chat ID and the new balance amount.\n"
            "Example: `123456789 150.00`",
            parse_mode='Markdown'
        )
        context.user_data['admin_set_balance_pending'] = True
        return

    try:
        target_user_id = int(parts[0])
        amount = float(parts[1])
        if amount < 0:
            raise ValueError("Negative amount")
    except ValueError:
        await update.message.reply_text(
            "❌ Please provide a valid chat ID and positive amount.\n"
            "Example: `123456789 150.00`",
            parse_mode='Markdown'
        )
        context.user_data['admin_set_balance_pending'] = True
        return

    target_user = db.get_user(target_user_id)
    if not target_user:
        logger.warning(f"User {target_user_id} not found in database")
        await update.message.reply_text(f"❌ No user found with Telegram ID {target_user_id}.")
        context.user_data['admin_set_balance_pending'] = True
        return

    logger.info(f"Found user: {target_user}")
    logger.info(f"Calling set_referral_balance for user {target_user_id} with amount {amount}")
    success = db.set_referral_balance(target_user_id, amount)
    logger.info(f"set_referral_balance returned: {success}")

    if success:
        try:
            await update.get_bot().send_message(
                chat_id=target_user_id,
                text=(f"💰 Your referral balance has been updated by admin.\n\n"
                      f"New balance: AED {amount:.2f}\n\n"
                      "Please message the admin if you want to withdraw funds.")
            )
        except Exception as e:
            logger.error(f"Failed to notify user {target_user_id}: {e}")

        await update.message.reply_text(
            f"✅ Balance updated successfully!\n\n"
            f"User {target_user_id} now has AED {amount:.2f}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin", callback_data="back_to_admin")
            ]])
        )
        logger.info(f"Balance updated for user {target_user_id}: AED {amount}")
    else:
        await update.message.reply_text("❌ Failed to update balance. Please try again.")
        context.user_data['admin_set_balance_pending'] = True

async def handle_balance_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle balance edit input from admin for a selected user"""
    user = update.effective_user
    logger.info(f"handle_balance_edit called - Admin ID: {user.id}, editing_balance_user_id in context: {'editing_balance_user_id' in context.user_data}")

    if user.id not in ADMIN_IDS:
        logger.warning(f"User {user.id} is not an admin")
        return

    if 'editing_balance_user_id' not in context.user_data:
        logger.info(f"No editing_balance_user_id in context for user {user.id}")
        return

    target_user_id = context.user_data['editing_balance_user_id']

    logger.info(f"Processing balance edit for target user {target_user_id}, amount from message: {update.message.text}")

    try:
        amount = float(update.message.text.strip())
        if amount < 0:
            raise ValueError("Negative amount")
    except ValueError:
        logger.warning(f"Invalid amount entered: {update.message.text}")
        await update.message.reply_text("❌ Please enter a valid positive number.")
        return

    target_user = db.get_user(target_user_id)
    if not target_user:
        logger.warning(f"User {target_user_id} not found in database")
        await update.message.reply_text(f"❌ No user found with Telegram ID {target_user_id}.")
        return

    logger.info(f"Calling set_referral_balance for user {target_user_id} with amount {amount}")
    success = db.set_referral_balance(target_user_id, amount)
    logger.info(f"set_referral_balance returned: {success}")

    if success:
        # Only delete the flag after successful update
        del context.user_data['editing_balance_user_id']
        try:
            await update.get_bot().send_message(
                chat_id=target_user_id,
                text=(f"💰 Your referral balance has been updated by admin.\n\n"
                      f"New balance: AED {amount:.2f}\n\n"
                      "Please message the admin if you want to withdraw funds.")
            )
        except Exception:
            pass

        await update.message.reply_text(
            f"✅ Balance updated successfully!\n\n"
            f"User {target_user_id} now has AED {amount:.2f}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Back to Admin", callback_data="back_to_admin")
            ]])
        )
    else:
        await update.message.reply_text("❌ Failed to update balance. Please try again.")

async def show_balance_management(query, context):
    """Show balance management options"""
    text = "💰 *Change User Balance*\n\n"
    text += "Enter a user's ID and the new balance amount in this format:\n"
    text += "`<user_id> <amount>`\n\n"
    text += "Example: `123456789 500`"

    keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="back_to_admin")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    context.user_data['admin_set_balance_pending'] = True

async def show_statistics(query, context):
    """Show overall statistics"""
    conn = db.get_connection()
    cursor = conn.cursor()

    # Total users
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']

    # Total referral balance
    cursor.execute("SELECT COALESCE(SUM(referral_balance), 0) as total FROM users")
    total_balance = cursor.fetchone()['total']

    # Total referral earnings
    cursor.execute("SELECT COALESCE(SUM(reward_amount), 0) as total FROM referral_earnings")
    total_earnings = cursor.fetchone()['total']

    # Total deals
    cursor.execute("SELECT COUNT(*) as count FROM referral_earnings")
    total_deals = cursor.fetchone()['count']

    conn.close()

    text = "📊 *Statistics*\n\n"
    text += f"👥 Total Users: {total_users}\n"
    text += f"💰 Total Referral Balance: AED {total_balance:.2f}\n"
    text += f"📈 Total Referral Earnings: AED {total_earnings:.2f}\n"
    text += f"🤝 Total Referral Deals: {total_deals}\n"

    keyboard = [[InlineKeyboardButton("🔙 Back to Admin", callback_data="back_to_admin")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_back_to_admin(query, context):
    """Handle back to admin panel"""
    keyboard = [
        [InlineKeyboardButton("📊 Statistics", callback_data="admin_statistics")],
        [InlineKeyboardButton("💰 Change User Balance", callback_data="admin_manage_balances")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "🔧 *Admin Panel*\n\n"
        "Choose an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )