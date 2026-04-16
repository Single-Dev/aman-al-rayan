from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import logging
from src.database.db_manager import DatabaseManager
from src.utils.keyboards import get_schedule_date_keyboard, get_main_menu_keyboard, get_yes_no_keyboard, get_time_selection_keyboard, get_location_request_keyboard
from src.utils.messages import get_order_confirmation_message
from src.config import CONTACT_INFO
from src.handlers.service_handler import (
    handle_payment_proposal,
    handle_deal_message,
    handle_user_counter_price,
    handle_user_counter_message,
    handle_admin_counter_price,
    handle_admin_counter_message
)

logger = logging.getLogger(__name__)
db = DatabaseManager()

async def handle_confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle order confirmation"""
    query = update.callback_query
    await query.answer()
    
    # Extract order_id from callback_data
    order_id = int(query.data.split('_')[-1])
    
    # Ask for scheduling
    await query.edit_message_text(
        text="📅 When would you like to schedule the service?",
        reply_markup=get_schedule_date_keyboard()
    )
    
    context.user_data['current_order_id'] = order_id

async def handle_schedule_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle schedule date selection"""
    query = update.callback_query
    await query.answer()
    
    date_type = query.data.replace('date_', '')
    today = datetime.now()
    
    scheduled_date = None
    if date_type == 'today':
        scheduled_date = today.strftime('%Y-%m-%d')
    elif date_type == 'tomorrow':
        scheduled_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
    elif date_type == 'this_week':
        scheduled_date = (today + timedelta(days=3)).strftime('%Y-%m-%d')
    elif date_type == 'next_week':
        scheduled_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')
    elif date_type == 'custom':
        await query.edit_message_text(
            text="📝 Please send your preferred date in format: YYYY-MM-DD (e.g., 2026-04-20)"
        )
        context.user_data['awaiting_custom_date'] = True
        return
    
    order_id = context.user_data.get('current_order_id')
    if order_id:
        db.update_order_status(order_id, 'scheduled', None)
        
        # Check if user details are complete
        user = db.get_user(update.effective_user.id)
        if not user or not user.get('email') or not user.get('address'):
            # Ask for user details sequentially
            context.user_data['collecting_details'] = True
            context.user_data['detail_step'] = 'email'
            
            await query.edit_message_text(
                text="📧 **Please provide your email address:**\n\nExample: user@example.com",
                parse_mode='Markdown'
            )
        else:
            # Ask for preferred time
            context.user_data['awaiting_time_selection'] = True
            await query.edit_message_text(
                text="🕐 **What time would you prefer for the service?**\n\nPlease select your preferred time:",
                parse_mode='Markdown',
                reply_markup=get_time_selection_keyboard()
            )

async def handle_add_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle adding notes to order"""
    query = update.callback_query
    await query.answer()
    
    order_id = int(query.data.split('_')[-1])
    context.user_data['current_order_id'] = order_id
    context.user_data['awaiting_notes'] = True
    
    await query.edit_message_text(
        text="📝 Please add any special requests or notes for the service:\n\n(Send /done when finished)"
    )

async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time selection"""
    query = update.callback_query
    await query.answer()
    
    time_value = query.data.replace('time_', '')
    
    if time_value == 'custom':
        await query.edit_message_text(
            text="📝 **Please send your preferred time in 24-hour format:**\n\nExample: 14:30 (for 2:30 PM)",
            parse_mode='Markdown'
        )
        context.user_data['awaiting_custom_time'] = True
        return
    
    # Validate time format
    try:
        if ':' in time_value:
            hours, minutes = time_value.split(':')
            hours, minutes = int(hours), int(minutes)
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError
        else:
            raise ValueError
    except ValueError:
        await query.edit_message_text(
            text="❌ Invalid time format. Please select from the options or try custom time.",
            reply_markup=get_time_selection_keyboard()
        )
        return
    
    # Save selected time
    context.user_data['selected_time'] = time_value
    context.user_data['awaiting_time_selection'] = False
    
    # Update order with preferred time
    order_id = context.user_data.get('current_order_id')
    if order_id:
        db.update_order_time(order_id, time_value)
    
    # Show final order confirmation
    order_id = context.user_data.get('current_order_id')
    if order_id:
        order = db.get_order_with_deals(order_id)
        
        if order:
            latest_offer = order.get('deals', [])[0] if order.get('deals') else None
            confirmation_msg = get_order_confirmation_message(
                order_id,
                order['service_type'],
                order['hours'],
                latest_offer['proposed_price'] if latest_offer else None
            )
            
            await query.edit_message_text(
                text=confirmation_msg,
                parse_mode='Markdown',
                reply_markup=get_yes_no_keyboard('finalize_order')
            )
        else:
            await query.edit_message_text(
                text="❌ Order not found. Please try again.",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        await query.edit_message_text(
            text="❌ Order details lost. Please start over.",
            reply_markup=get_main_menu_keyboard()
        )

async def handle_cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle order cancellation"""
    query = update.callback_query
    await query.answer()
    
    order_id = int(query.data.split('_')[-1])
    db.update_order_status(order_id, 'cancelled')
    
    await query.edit_message_text(
        text="❌ Order cancelled.\n\nWould you like to book another service?",
        reply_markup=None
    )
    await query.message.reply_text(
        text="✅ Order cancelled. Use the main menu below to continue.",
        reply_markup=get_main_menu_keyboard()
    )

async def handle_finalize_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle final order confirmation"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    parts = callback_data.split('_')
    
    if len(parts) >= 2 and parts[0] == 'finalize' and parts[1] == 'order':
        action = parts[-1]  # 'yes' or 'no'
        
        if action == 'yes':
            order_id = context.user_data.get('current_order_id')
            if order_id:
                db.update_order_status(order_id, 'confirmed')
                
                # Get complete order and user details for notification
                orders = db.get_user_orders(update.effective_user.id, limit=100)
                order = next((o for o in orders if o['order_id'] == order_id), None)
                user = db.get_user(update.effective_user.id)
                
                contact_msg = f"""
✅ **Order Confirmed!**

Order ID: #{order_id}

📞 **Our team will contact you shortly:**
• {CONTACT_INFO['phone']}
• {CONTACT_INFO['whatsapp']} (WhatsApp)

📋 Have your order details ready for confirmation.

🙏 Thank you for choosing Aman Al Rayan!
                """
                
                await query.edit_message_text(
                    text=contact_msg,
                    parse_mode='Markdown',
                    reply_markup=None
                )
                await query.message.reply_text(
                    text="✅ Order confirmed! Use the main menu below to continue.",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu_keyboard()
                )
                
                # Send admin notification
                await send_admin_notification(order, user, update.get_bot())
            else:
                await query.edit_message_text(
                    text="❌ Order not found. Please try again.",
                    reply_markup=None
                )
                await query.message.reply_text(
                    text="❌ Order not found. Please try again. Use the menu below to continue.",
                    reply_markup=get_main_menu_keyboard()
                )
        else:  # 'no'
            await query.edit_message_text(
                text="❌ Order not finalized.\n\nWould you like to try again?",
                reply_markup=None
            )
            await query.message.reply_text(
                text="❌ Order not finalized. Use the main menu below to continue.",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        await query.edit_message_text(
            text="❌ Invalid action.",
            reply_markup=None
        )
        await query.message.reply_text(
            text="❌ Invalid action. Use the main menu below to continue.",
            reply_markup=get_main_menu_keyboard()
        )

async def handle_contact_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shared contact from the user"""
    contact = update.message.contact
    user = update.effective_user

    if contact and contact.phone_number:
        db.add_or_update_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=contact.phone_number
        )
        context.user_data['awaiting_phone'] = False

        await update.message.reply_text(
            "✅ Phone number saved. Here are the available services:",
            reply_markup=get_main_menu_keyboard()
        )
        from src.handlers.service_handler import handle_services
        await handle_services(update, context)
    else:
        await update.message.reply_text(
            "❌ I couldn't read your phone number. Please try sharing it again."
        )

async def handle_location_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shared location from the user"""
    location = update.message.location
    user = update.effective_user

    if location:
        location_text = f"📍 Location: {location.latitude}, {location.longitude}"
        
        # Save location to user profile
        db.add_or_update_user(user_id=user.id, location=location_text)
        
        # Forward location to admin
        from src.config import ADMIN_IDS
        for admin_id in ADMIN_IDS:
            try:
                await update.get_bot().send_message(
                    chat_id=int(admin_id),
                    text=f"📍 **Location received from customer**\n\n👤 {user.first_name} {user.last_name or ''}\n📱 @{user.username or 'N/A'}\n\n{location_text}",
                    parse_mode='Markdown'
                )
                await update.get_bot().send_location(
                    chat_id=int(admin_id),
                    latitude=location.latitude,
                    longitude=location.longitude
                )
            except Exception as e:
                logger.error(f"Failed to forward location to admin {admin_id}: {e}")
        
        await update.message.reply_text(
            "✅ **Location saved and sent to admin!**\n\nOur team will use this to better serve you.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ I couldn't read your location. Please try sharing it again."
        )

async def handle_user_details_collection(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Handle collecting user details during order process"""
    user_id = update.effective_user.id
    step = context.user_data.get('detail_step', 'email')
    
    if step == 'email':
        # Validate email
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, text.strip()):
            await update.message.reply_text(
                "❌ **Please enter a valid email address:**\n\nExample: user@example.com",
                parse_mode='Markdown'
            )
            return
        
        # Save email
        db.add_or_update_user(user_id=user_id, email=text.strip())
        context.user_data['detail_step'] = 'address'
        
        await update.message.reply_text(
            "✅ **Email saved!**\n\n📍 **Now please send your full address:**\n\nExample: Villa 123, Jumeirah Beach Residence, Dubai, UAE",
            parse_mode='Markdown'
        )
        
    elif step == 'address':
        if len(text.strip()) < 10:
            await update.message.reply_text(
                "❌ **Please provide a complete address:**\n\nExample: Villa 123, Jumeirah Beach Residence, Dubai, UAE",
                parse_mode='Markdown'
            )
            return
        
        # Save address
        db.add_or_update_user(user_id=user_id, address=text.strip())
        context.user_data['detail_step'] = 'location'
        
        await update.message.reply_text(
            "✅ **Address saved!**\n\n📍 **Optional: Share your location**\n\nYou can share your exact location for better service, or type 'skip' to continue.",
            parse_mode='Markdown',
            reply_markup=get_location_request_keyboard()
        )
        
    elif step == 'location':
        if text.lower() in ['skip', 'none', 'no']:
            # Skip location sharing
            context.user_data['detail_step'] = 'notes'
            
            await update.message.reply_text(
                "✅ **Location skipped!**\n\n📝 **Any special notes or requests?**\n\nSend 'none' if no special notes, or describe your requirements:",
                parse_mode='Markdown'
            )
        else:
            # They might have sent location via keyboard, wait for it
            await update.message.reply_text(
                "📍 **Please share your location using the button above, or type 'skip' to continue.**",
                parse_mode='Markdown',
                reply_markup=get_location_request_keyboard()
            )
        
    elif step == 'notes':
        # Save notes if provided
        notes = text.strip() if text.lower() != 'none' else None
        
        # Complete details collection
        context.user_data['collecting_details'] = False
        context.user_data.pop('detail_step', None)
        
        # Now ask for preferred time
        context.user_data['awaiting_time_selection'] = True
        
        await update.message.reply_text(
            "✅ **Details saved!**\n\n🕐 **What time would you prefer for the service?**\n\nPlease select your preferred time:",
            parse_mode='Markdown',
            reply_markup=get_time_selection_keyboard()
        )

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for notes, dates, and main menu navigation"""
    text = update.message.text.strip()
    logger.info(f"Handling text input: '{text}' from user {update.effective_user.id}")

    # Handle main menu buttons FIRST (so admins can still use navigation)
    if "Services" in text:
        from src.handlers.service_handler import handle_services
        await handle_services(update, context)
        return

    if "Subscriptions" in text:
        from src.handlers.subscription_handler import handle_subscriptions
        await handle_subscriptions(update, context)
        return

    if "Contact" in text:
        from src.handlers.contact_handler import handle_contact
        await handle_contact(update, context)
        return

    if "Referral" in text:
        from src.handlers.referral_handler import handle_referral
        await handle_referral(update, context)
        return

    # Handle user details collection
    if context.user_data.get('collecting_details'):
        return await handle_user_details_collection(update, context, text)

    # Handle custom time entry
    if context.user_data.get('awaiting_custom_time'):
        context.user_data['awaiting_custom_time'] = False
        
        try:
            # Validate time format (HH:MM)
            if ':' not in text:
                raise ValueError("Missing colon")
            
            hours, minutes = text.split(':')
            hours, minutes = int(hours), int(minutes)
            
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError("Invalid time range")
            
            time_value = f"{hours:02d}:{minutes:02d}"
            context.user_data['selected_time'] = time_value
            
            # Show final order confirmation
            order_id = context.user_data.get('current_order_id')
            if order_id:
                order = db.get_order_with_deals(order_id)
                
                if order:
                    latest_offer = order.get('deals', [])[0] if order.get('deals') else None
                    confirmation_msg = get_order_confirmation_message(
                        order_id,
                        order['service_type'],
                        order['hours'],
                        latest_offer['proposed_price'] if latest_offer else None
                    )
                    
                    await update.message.reply_text(
                        text=confirmation_msg,
                        parse_mode='Markdown',
                        reply_markup=get_yes_no_keyboard('finalize_order')
                    )
                else:
                    await update.message.reply_text(
                        "❌ Order not found. Please try again.",
                        reply_markup=get_main_menu_keyboard()
                    )
            else:
                await update.message.reply_text(
                    "❌ Order details lost. Please start over.",
                    reply_markup=get_main_menu_keyboard()
                )
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ **Invalid time format.**\n\nPlease use 24-hour format: HH:MM\n\nExample: 14:30 (for 2:30 PM)",
                parse_mode='Markdown',
                reply_markup=get_time_selection_keyboard()
            )
        return

    # Handle negotiation and deal messages
    if context.user_data.get('awaiting_payment'):
        return await handle_payment_proposal(update, context)
    if context.user_data.get('awaiting_deal_message'):
        return await handle_deal_message(update, context)
    if context.user_data.get('awaiting_user_counter_price'):
        return await handle_user_counter_price(update, context)
    if context.user_data.get('awaiting_user_counter_message'):
        return await handle_user_counter_message(update, context)
    if context.user_data.get('awaiting_admin_counter_price'):
        return await handle_admin_counter_price(update, context)
    if context.user_data.get('awaiting_admin_counter_message'):
        return await handle_admin_counter_message(update, context)

    # Fallback numeric payment handling when service and hours are selected
    if context.user_data.get('selected_service') and context.user_data.get('selected_hours'):
        if context.user_data.get('awaiting_payment') is None or not context.user_data.get('awaiting_payment'):
            try:
                proposed_price = float(text.replace('AED', '').replace('aed', '').strip())
                if proposed_price > 0:
                    context.user_data['awaiting_payment'] = True
                    return await handle_payment_proposal(update, context)
            except ValueError:
                pass

    # Handle order notes
    if context.user_data.get('awaiting_notes'):
        if text.lower() == '/done':
            context.user_data['awaiting_notes'] = False
            await update.message.reply_text(
                "✅ Notes added! Your order has been updated.",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                "📝 Note added. Send /done when finished."
            )
        return

    # If admin is setting balance, don't send error message (let admin handler process it)
    if context.user_data.get('admin_set_balance_pending') or context.user_data.get('editing_balance_user_id'):
        return

    await update.message.reply_text(
        text="❓ I didn't recognize that option. Please use the menu buttons below.",
        reply_markup=get_main_menu_keyboard()
    )

async def send_admin_notification(order: dict, user: dict, bot):
    """Send notification to admin users about new order"""
    from src.config import ADMIN_IDS, SERVICES
    from datetime import datetime
    
    if not ADMIN_IDS:
        return
    
    service = SERVICES.get(order['service_type'], {})
    latest_deal = db.get_latest_deal(order['order_id'])
    deal_text = ""
    if latest_deal:
        deal_text = f"\n• Proposed Price: AED {latest_deal['proposed_price']}\n• Deal Status: {latest_deal['status'].title()}\n"
    
    admin_message = f"""
🚨 **NEW ORDER RECEIVED!**

📋 **Order Details:**
• Order ID: #{order['order_id']}
• Service: {service.get('name', order['service_type'])}
• Hours: {order['hours']}
• Scheduled Date: {order.get('scheduled_date', 'Not set')}
• Preferred Time: {order.get('preferred_time', 'Not set')}
• Status: {order['status']}{deal_text}

👤 **Customer Information:**
• Name: {user.get('first_name', 'N/A')} {user.get('last_name', 'N/A')}
• Username: @{user.get('username', 'N/A')}
• Phone: {user.get('phone_number', 'N/A')}
• Email: {user.get('email', 'N/A')}
• Address: {user.get('address', 'N/A')}
• Location: {user.get('location', 'Not provided')}
• Notes: {order.get('notes', 'None')}

⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📱 **Action Required:** Contact customer to confirm details and schedule service.
    """
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=int(admin_id),
                text=admin_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send admin notification to {admin_id}: {e}")
