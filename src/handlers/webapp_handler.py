import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.database.db_manager import DatabaseManager
from src.config import ADMIN_IDS, DATABASE_PATH

db = DatabaseManager(DATABASE_PATH)


async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle data received from app.html via WebApp.sendData()"""
    user = update.effective_user

    if update.web_app_data:
        try:
            # Parse order data from mini app
            order_data = json.loads(update.web_app_data.data)

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
                estimated_price=price_min,
                scheduled_date=date
            )

            # Update with time if provided
            if time:
                db.update_order_time(order_id, time)

            # Create confirmation message
            confirmation_message = (
                f"✅ **Booking Received!**\n\n"
                f"📋 Service: {service_name}\n"
                f"📅 Date: {date}\n"
            )

            if time:
                confirmation_message += f"⏰ Time: {time}\n"

            confirmation_message += (
                f"💰 Price Range: AED {price_min} - {price_max}\n\n"
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

            # Notify admin
            for admin_id in ADMIN_IDS:
                try:
                    admin_message = (
                        f"📱 **New Booking from Mini App**\n\n"
                        f"👤 User: {user.first_name or 'Unknown'} (@{user.username or user.id})\n"
                        f"📋 Service: {service_name}\n"
                        f"📅 Date: {date}\n"
                    )

                    if time:
                        admin_message += f"⏰ Time: {time}\n"

                    admin_message += (
                        f"💰 Price: AED {price_min} - {price_max}\n"
                        f"Order ID: {order_id}\n"
                    )

                    if notes:
                        admin_message += f"📝 Notes: {notes}\n"

                    await context.bot.send_message(
                        chat_id=int(admin_id),
                        text=admin_message,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"Error notifying admin {admin_id}: {e}")

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
