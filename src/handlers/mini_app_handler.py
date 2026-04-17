import json
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from src.database.db_manager import DatabaseManager
from src.config import MINI_APP_CONFIG, DATABASE_PATH
from src.utils.keyboards import get_mini_app_keyboard

db = DatabaseManager(DATABASE_PATH)


async def handle_mini_app_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mini app button click (from main menu or other places)"""
    user = update.effective_user
    query = update.callback_query

    if query:
        await query.answer()

    # Get user's preferred version
    preferred_version = db.get_user_preferred_version(user.id)

    # Create or update session
    db.create_mini_app_session(user.id, preferred_version)

    message_text = (
        f"🎯 Choose your app experience:\n\n"
        f"**Quick Service** - Browse and get quotes fast\n"
        f"**Full Booking** - Complete calendar and scheduling\n\n"
        f"Tap 'Open App' below to launch."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📲 Quick Service", web_app=WebAppInfo(url=f"{MINI_APP_CONFIG['url']}/lite?user_id={user.id}"))],
        [InlineKeyboardButton("📅 Full Booking", web_app=WebAppInfo(url=f"{MINI_APP_CONFIG['url']}/booking?user_id={user.id}"))],
        [InlineKeyboardButton("⬅️ Back", callback_data='back_to_main')]
    ])

    if query:
        try:
            await query.edit_message_text(message_text, parse_mode='Markdown', reply_markup=keyboard)
        except BadRequest:
            await query.message.reply_text(message_text, parse_mode='Markdown', reply_markup=keyboard)
    else:
        await update.message.reply_text(message_text, parse_mode='Markdown', reply_markup=keyboard)


async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data received from mini app via WebApp.sendData()"""
    user = update.effective_user

    if update.web_app_data:
        try:
            # Parse order data from mini app
            order_data = json.loads(update.web_app_data.data)

            # Create order in database
            service_id = order_data.get('service_id')
            date = order_data.get('date')
            time = order_data.get('time')
            proposed_price = order_data.get('proposed_price', 250)
            notes = order_data.get('notes', '')
            version = order_data.get('version', 'lite')

            # Create order
            order_id = db.create_order(
                user_id=user.id,
                service_type=service_id,
                hours=1,
                estimated_price=proposed_price,
                scheduled_date=date
            )

            # Update with time if provided
            if time:
                db.update_order_time(order_id, time)

            # Create deal if custom price was proposed
            if proposed_price:
                db.create_deal(
                    order_id=order_id,
                    proposed_price=proposed_price,
                    proposed_by='user',
                    message=notes or f"Submitted from {version} mini app"
                )

            # Update session
            db.set_user_preference(user.id, version)

            # Notify user
            confirmation_message = (
                "✅ **Order Received!**\n\n"
                f"📅 Date: {date}\n"
                f"⏰ Time: {time or 'Not specified'}\n"
                f"💰 Your Price: AED {proposed_price}\n\n"
                "We'll review your proposal and get back to you shortly. "
                "You'll receive updates via this chat."
            )

            await update.message.reply_text(
                confirmation_message,
                parse_mode='Markdown'
            )

            # Log to admin if needed
            from src.config import ADMIN_IDS
            admin_message = (
                f"📲 **New Mini App Order**\n\n"
                f"User: {user.first_name or 'Unknown'} (@{user.username or user.id})\n"
                f"Service: {service_id}\n"
                f"Date: {date}\n"
                f"Time: {time or 'Not specified'}\n"
                f"Proposed Price: AED {proposed_price}\n"
                f"Version: {version}\n"
                f"Order ID: {order_id}"
            )

            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(chat_id=int(admin_id), text=admin_message, parse_mode='Markdown')
                except Exception as e:
                    print(f"Error notifying admin: {e}")

        except json.JSONDecodeError as e:
            await update.message.reply_text(f"❌ Error processing order: Invalid data format")
        except Exception as e:
            await update.message.reply_text(f"❌ Error creating order: {str(e)}")
            print(f"Error handling web app data: {e}")
    else:
        await update.message.reply_text("❌ No data received from mini app")
