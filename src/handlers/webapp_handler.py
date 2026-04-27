import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database.db_manager import DatabaseManager
from src.config import ADMIN_IDS, DATABASE_PATH

db = DatabaseManager(DATABASE_PATH)


async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data received from app.html via WebApp.sendData()"""
    user = update.effective_user
    message = update.effective_message

    if message and message.web_app_data:
        try:
            # Parse order data from mini app
            order_data = json.loads(message.web_app_data.data)

            # Extract fields
            service_id = order_data.get('service_id')
            service_name = order_data.get('service_name')
            date = order_data.get('date')
            time = order_data.get('time', '')
            price_min = order_data.get('price_min', 180)
            price_max = order_data.get('price_max', 350)
            notes = order_data.get('notes', '')

            # Create order in database
            order_id = db.create_order(
                user_id=user.id,
                service_type=service_id,
                hours=1,
                scheduled_date=date,
                notes=notes
            )

            # Update with time if provided
            if time:
                db.update_order_time(order_id, time)

            # Set estimated price in order
            proposed_price = order_data.get('proposed_price', price_min)
            db.update_order_status(order_id, 'pending', final_price=proposed_price)

            # Create a deal for this proposed price
            deal_id = db.create_deal(
                order_id=order_id,
                proposed_price=proposed_price,
                proposed_by='user',
                message=f"Initial proposal from Mini App: {notes}" if notes else "Initial proposal from Mini App"
            )

            # Create confirmation message
            confirmation_message = (
                f"✅ **Booking Received!**\n\n"
                f"📋 Service: {service_name}\n"
                f"📅 Date: {date}\n"
            )

            if time:
                confirmation_message += f"⏰ Time: {time}\n"

            confirmation_message += (
                f"💰 Your Proposed Price: AED {proposed_price}\n"
                f"📊 Range: AED {price_min} - {price_max}\n\n"
            )

            if notes:
                confirmation_message += f"📝 Notes: {notes}\n\n"

            confirmation_message += (
                "We'll review your booking and contact you soon to confirm details."
            )

            # Send confirmation to user
            await update.message.reply_text(
                confirmation_message,
                parse_mode='Markdown'
            )

            # Notify admin asynchronously to prevent timeouts
            asyncio.create_task(notify_admins_of_booking(
                context, user, service_name, date, time, proposed_price, price_min, price_max, order_id, notes, deal_id
            ))

        except json.JSONDecodeError:
            await update.message.reply_text(
                "❌ Error: Invalid data format from booking app"
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error creating booking: {str(e)}"
            )
            print(f"Error handling web app data: {e}")
    else:
        await update.message.reply_text(
            "❌ No data received from booking app"
        )


async def notify_admins_of_booking(context, user, service_name, date, time, proposed_price, price_min, price_max, order_id, notes, deal_id):
    """Asynchronous admin notification"""
    from src.utils.keyboards import get_deal_negotiation_keyboard
    
    for admin_id in ADMIN_IDS:
        try:
            admin_message = (
                f"📱 **New Booking from Mini App**\n\n"
                f"👤 User: {user.first_name or 'Unknown'} (@{user.username or user.id})\n"
                f"🆔 User ID: `{user.id}`\n"
                f"📋 Service: {service_name}\n"
                f"📅 Date: {date}\n"
            )

            if time:
                admin_message += f"⏰ Time: {time}\n"

            admin_message += (
                f"💰 Proposed Price: AED {proposed_price}\n"
                f"📊 Price Range: AED {price_min} - {price_max}\n"
                f"Order ID: {order_id}\n"
            )

            if notes:
                admin_message += f"📝 Notes: {notes}\n"

            await context.bot.send_message(
                chat_id=int(admin_id),
                text=admin_message,
                parse_mode='Markdown',
                reply_markup=get_deal_negotiation_keyboard(deal_id)
            )
        except Exception as e:
            print(f"Error notifying admin {admin_id}: {e}")
