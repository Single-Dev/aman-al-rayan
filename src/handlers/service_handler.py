import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.database.db_manager import DatabaseManager
from src.utils.keyboards import (
    get_main_menu_keyboard,
    get_services_inline_keyboard,
    get_hours_selection_keyboard,
    get_phone_request_keyboard
)
from src.utils.messages import (
    get_services_message,
    get_service_details_message
)
from src.config import SERVICES

logger = logging.getLogger(__name__)
db = DatabaseManager()

async def handle_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle services browsing"""
    query = update.callback_query
    message = update.message
    user = update.effective_user
    user_id = user.id

    db.add_or_update_user(
        user_id=user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )

    db_user = db.get_user(user_id)
    if not db_user or not db_user.get('phone_number'):
        prompt_text = (
            "📱 Please share your phone number so our admin can contact you.\n\n"
            "Tap the button below to share it."
        )
        if query:
            await query.answer()
            await query.edit_message_text(text=prompt_text, reply_markup=None)
            await query.message.reply_text(
                text="Tap the button below to share your phone number.",
                reply_markup=get_phone_request_keyboard()
            )
        else:
            await message.reply_text(
                text=prompt_text,
                reply_markup=get_phone_request_keyboard()
            )
        context.user_data['awaiting_phone'] = True
        return
    
    if query:
        await query.answer()
        text = get_services_message()
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=get_services_inline_keyboard()
        )
    else:
        text = get_services_message()
        await message.reply_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=get_services_inline_keyboard()
        )

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle service selection"""
    query = update.callback_query
    logger.info(f"Handling service selection: {query.data}")
    await query.answer()
    
    # Extract service_id from callback_data
    service_id = query.data.replace('service_', '')
    
    if service_id not in SERVICES:
        await query.edit_message_text("Service not found.")
        return
    
    # Store selected service in context
    context.user_data['selected_service'] = service_id
    
    text = get_service_details_message(service_id)
    
    await query.edit_message_text(
        text=text,
        parse_mode='Markdown',
        reply_markup=get_hours_selection_keyboard(service_id)
    )

async def handle_hours_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle hours selection"""
    query = update.callback_query
    logger.info(f"Handling hours selection: {query.data}")
    await query.answer()
    
    # Parse callback_data: hours_SERVICE_ID_HOURS
    parts = query.data.split('_')
    service_id = parts[1] + '_' + parts[2] if len(parts) > 3 else parts[1]
    
    # Find the hours in the callback data
    for i, part in enumerate(parts):
        if i > 0 and part.isdigit():
            hours = int(part)
            break
    else:
        hours = 1
    
    # Better parsing for service_id and hours
    callback_data = query.data
    # Format: hours_standard_cleaning_1
    if callback_data.count('_') >= 2:
        last_part = callback_data.rsplit('_', 1)[-1]
        hours = int(last_part)
        service_id = callback_data.replace(f'hours_', '').replace(f'_{hours}', '')
    
    if service_id not in SERVICES:
        await query.edit_message_text("Service not found.")
        return
    
    service = SERVICES[service_id]

    # Store in context
    context.user_data['selected_service'] = service_id
    context.user_data['selected_hours'] = hours
    
    # Ask for payment willingness
    payment_text = f"""
🧹 **{service['name']}** - {hours} hour{'s' if hours > 1 else ''}

💰 **How much are you willing to pay for this service?**

Please enter your proposed price in AED (e.g., 500, 750, 1000).

Our admin will review your offer and respond with a deal.
    """
    
    await query.edit_message_text(
        text=payment_text,
        parse_mode='Markdown',
        reply_markup=None
    )
    
    context.user_data['awaiting_payment'] = True

async def handle_payment_proposal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment proposal from user"""
    text = update.message.text.strip()
    
    # Validate payment amount
    try:
        proposed_price = float(text.replace('AED', '').replace('aed', '').strip())
        if proposed_price <= 0:
            raise ValueError("Invalid amount")
    except ValueError:
        await update.message.reply_text(
            "❌ **Invalid amount.**\n\nPlease enter a valid number (e.g., 500, 750, 1000).",
            parse_mode='Markdown'
        )
        return
    
    context.user_data['awaiting_payment'] = False
    context.user_data['proposed_price'] = proposed_price
    
    # Ask for optional message
    await update.message.reply_text(
        f"✅ **Price proposed: AED {proposed_price}**\n\n💬 **Optional: Add a message to your proposal**\n\nSend your message or type 'skip' to continue:",
        parse_mode='Markdown'
    )
    
    context.user_data['awaiting_deal_message'] = True

async def handle_deal_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deal message from user"""
    text = update.message.text.strip()
    
    message = None if text.lower() == 'skip' else text
    context.user_data['awaiting_deal_message'] = False
    
    # Create order and deal
    service_id = context.user_data.get('selected_service')
    hours = context.user_data.get('selected_hours')
    proposed_price = context.user_data.get('proposed_price')
    
    if not all([service_id, hours, proposed_price]):
        await update.message.reply_text("❌ Order details lost. Please start over.")
        return
    
    # Create order
    order_id = db.create_order(
        user_id=update.effective_user.id,
        service_type=service_id,
        hours=hours
    )
    
    # Create deal proposal
    deal_id = db.create_deal(
        order_id=order_id,
        proposed_price=proposed_price,
        proposed_by='user',
        message=message
    )
    
    context.user_data['current_order_id'] = order_id
    
    # Send to admin
    await send_deal_to_admin(order_id, deal_id, update.get_bot())
    
    # Confirm to user
    service = SERVICES[service_id]
    confirmation_text = f"""
✅ **Deal Proposal Sent!**

🧹 **Service:** {service['name']}
⏰ **Duration:** {hours} hour{'s' if hours > 1 else ''}
💰 **Your Offer:** AED {proposed_price}

📝 **Message:** {message or 'None'}

Our admin will review your proposal and respond soon. You'll be notified of any counter-offers or acceptance.

⏳ **Please wait for admin response...**
    """
    
    await update.message.reply_text(
        text=confirmation_text,
        parse_mode='Markdown'
    )

async def send_deal_to_admin(order_id: int, deal_id: int, bot):
    """Send deal proposal to admin"""
    from src.config import ADMIN_IDS, SERVICES

    order = db.get_order_with_deals(order_id)
    if not order:
        return

    service = SERVICES.get(order['service_type'], {})
    latest_deal = order['deals'][0] if order['deals'] else None
    if not latest_deal:
        return

    customer = db.get_user(order['user_id']) or {}
    admin_message = f"""
💰 **NEW DEAL PROPOSAL!**

📋 **Order Details:**
• Order ID: #{order_id}
• Service: {service.get('name', order['service_type'])}
• Hours: {order['hours']}
• Proposed Price: AED {latest_deal['proposed_price']}

👤 **Customer Contact Information:**
• User ID: `{order['user_id']}`
• Name: {customer.get('first_name', 'N/A')} {customer.get('last_name', 'N/A')}
• Username: @{customer.get('username', 'N/A')}
• Phone: {customer.get('phone_number', 'N/A')}
• Email: {customer.get('email', 'N/A')}
• Address: {customer.get('address', 'N/A')}
• Location: {customer.get('location', 'Not provided')}

💬 **Message:** {latest_deal.get('message', 'None')}

⚡ **Action Required:** Accept or Offer again.
    """

    from src.utils.keyboards import get_deal_negotiation_keyboard

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=int(admin_id),
                text=admin_message,
                parse_mode='Markdown',
                reply_markup=get_deal_negotiation_keyboard(deal_id)
            )
        except Exception as e:
            logger.error(f"Failed to send deal to admin {admin_id}: {e}")

async def handle_admin_deal_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin accept/counter/reject actions"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_', 2)
    action = f"{parts[0]}_{parts[1]}" if len(parts) > 1 else parts[0]
    deal_id = int(parts[2]) if len(parts) > 2 else None

    if not deal_id:
        await query.edit_message_text("❌ Invalid deal ID.")
        return

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT order_id FROM deals WHERE deal_id = ?', (deal_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await query.edit_message_text("❌ Deal not found.")
        return

    order_id = row[0]
    order = db.get_order_with_deals(order_id)
    if not order:
        await query.edit_message_text("❌ Order not found.")
        return

    latest_deal = order['deals'][0] if order['deals'] else None
    if not latest_deal:
        await query.edit_message_text("❌ No deal found for this order.")
        return

    if action == 'accept_deal':
        db.update_deal_status(deal_id, 'accepted')
        db.update_order_status(order_id, 'confirmed', latest_deal['proposed_price'])

        order_user = db.get_user(order['user_id'])
        if order_user and order_user.get('referrer_id'):
            reward = db.add_referral_earning(order_user['referrer_id'], order_user['user_id'], order_id, latest_deal['proposed_price'])
            if reward:
                referrer = db.get_user(order_user['referrer_id'])
                # Notify Referrer
                try:
                    await update.get_bot().send_message(
                        chat_id=order_user['referrer_id'],
                        text=(
                            f"💰 **You earned AED {reward:.2f}!**\n\n"
                            f"Your referred client {order_user.get('first_name', 'Friend')} just confirmed a booking.\n"
                            f"The reward has been added to your balance."
                        ),
                        parse_mode='Markdown'
                    )
                except Exception:
                    pass
                
                # Notify Admin about the transaction
                from src.config import ADMIN_IDS
                for admin_id in ADMIN_IDS:
                    try:
                        admin_ref_msg = (
                            "💸 **Referral Reward Issued**\n\n"
                            f"👤 **From User:** {order_user.get('first_name')} (@{order_user.get('username', 'N/A')})\n"
                            f"🆔 User ID: `{order_user.get('user_id')}`\n"
                            f"🔗 **To Referrer:** {referrer.get('first_name')} (@{referrer.get('username', 'N/A')})\n"
                            f"🆔 Referrer ID: `{order_user.get('referrer_id')}`\n"
                            f"📦 **Order ID:** #{order_id}\n"
                            f"💰 **Deal Amount:** AED {latest_deal['proposed_price']}\n"
                            f"🎁 **Reward Amount:** AED {reward:.2f}\n"
                            "───────────────────\n"
                            "Status: Balance Updated ✅"
                        )
                        await update.get_bot().send_message(chat_id=int(admin_id), text=admin_ref_msg, parse_mode='Markdown')
                    except Exception:
                        pass

        # Prepare customer contact details for admin confirmation
        customer_details = f"""
✅ **DEAL ACCEPTED!**

📋 **Order Details:**
• Order ID: #{order_id}
• Service: {SERVICES.get(order['service_type'], {}).get('name', order['service_type'])}
• Hours: {order['hours']}
• Accepted Price: AED {latest_deal['proposed_price']}

👤 **Customer Contact Information:**
• User ID: {order['user_id']}
• Name: {order_user.get('first_name', 'N/A')} {order_user.get('last_name', 'N/A')}
• Username: @{order_user.get('username', 'N/A')}
• Phone: {order_user.get('phone_number', 'N/A')}
• Email: {order_user.get('email', 'N/A')}
• Address: {order_user.get('address', 'N/A')}
• Location: {order_user.get('location', 'Not provided')}

📞 **Please contact the customer to finalize scheduling.**
        """

        await query.edit_message_text(text=customer_details, parse_mode='Markdown')

        await update.get_bot().send_message(
            chat_id=order['user_id'],
            text=f"✅ **Your deal has been accepted!**\n\nService: {SERVICES.get(order['service_type'], {}).get('name', order['service_type'])}\nHours: {order['hours']}\nPrice: AED {latest_deal['proposed_price']}\n\nOur admin will contact you shortly to finalize scheduling.",
            parse_mode='Markdown'
        )
        return

    if action == 'reject_deal':
        db.update_deal_status(deal_id, 'rejected')
        db.update_order_status(order_id, 'cancelled')

        await query.edit_message_text(text="❌ Deal rejected. The user has been notified.")
        await update.get_bot().send_message(
            chat_id=order['user_id'],
            text=f"❌ **Your deal has been rejected.**\n\nYou can start again by selecting a service.",
            parse_mode='Markdown'
        )
        return

    if action == 'counter_deal':
        db.update_deal_status(deal_id, 'countered')
        context.user_data['admin_counter_deal_id'] = deal_id
        context.user_data['awaiting_admin_counter_price'] = True
        await query.edit_message_text(
            text="💰 Please send your counter offer price in AED:",
            parse_mode='Markdown'
        )
        return

async def handle_user_deal_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user accept/counter/cancel actions"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_', 2)
    action = f"{parts[0]}_{parts[1]}" if len(parts) > 1 else parts[0]
    deal_id = int(parts[2]) if len(parts) > 2 else None

    if not deal_id:
        await query.edit_message_text("❌ Invalid deal ID.")
        return

    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT order_id FROM deals WHERE deal_id = ?', (deal_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        await query.edit_message_text("❌ Deal not found.")
        return

    order_id = row[0]
    order = db.get_order_with_deals(order_id)
    if not order:
        await query.edit_message_text("❌ Order not found.")
        return

    latest_deal = order['deals'][0] if order['deals'] else None
    if not latest_deal:
        await query.edit_message_text("❌ No deal found for this order.")
        return

    from src.config import ADMIN_IDS

    if action == 'user_accept':
        db.update_deal_status(deal_id, 'accepted')
        db.update_order_status(order_id, 'confirmed', latest_deal['proposed_price'])

        order_user = db.get_user(order['user_id'])
        if order_user and order_user.get('referrer_id'):
            reward = db.add_referral_earning(order_user['referrer_id'], order_user['user_id'], order_id, latest_deal['proposed_price'])
            if reward:
                referrer = db.get_user(order_user['referrer_id'])
                # Notify Referrer
                try:
                    await update.get_bot().send_message(
                        chat_id=order_user['referrer_id'],
                        text=(
                            f"💰 **You earned AED {reward:.2f}!**\n\n"
                            f"Your referred client {order_user.get('first_name', 'Friend')} just confirmed a booking.\n"
                            f"The reward has been added to your balance."
                        ),
                        parse_mode='Markdown'
                    )
                except Exception:
                    pass
                
                # Notify Admin about the transaction
                from src.config import ADMIN_IDS
                for admin_id in ADMIN_IDS:
                    try:
                        admin_ref_msg = (
                            "💸 **Referral Reward Issued (User Accepted)**\n\n"
                            f"👤 **From User:** {order_user.get('first_name')} (@{order_user.get('username', 'N/A')})\n"
                            f"🔗 **To Referrer:** {referrer.get('first_name')} (@{referrer.get('username', 'N/A')})\n"
                            f"📦 **Order ID:** #{order_id}\n"
                            f"💰 **Deal Amount:** AED {latest_deal['proposed_price']}\n"
                            f"🎁 **Reward Amount:** AED {reward:.2f}\n"
                            "───────────────────\n"
                            "Status: Balance Updated ✅"
                        )
                        await update.get_bot().send_message(chat_id=int(admin_id), text=admin_ref_msg, parse_mode='Markdown')
                    except Exception:
                        pass

        await query.edit_message_text(text="✅ You accepted the deal. Admin has been notified.")
        if ADMIN_IDS:
            await update.get_bot().send_message(
                chat_id=int(ADMIN_IDS[0]),
                text=f"✅ **Deal accepted by user for Order #{order_id}.**\n\nPrice: AED {latest_deal['proposed_price']}\n\nPlease follow up to finalize scheduling.",
                parse_mode='Markdown'
            )
        return

    if action == 'user_cancel':
        db.update_deal_status(deal_id, 'rejected')
        db.update_order_status(order_id, 'cancelled')
        await query.edit_message_text(text="❌ You cancelled the deal request. You can start again anytime.")
        if ADMIN_IDS:
            await update.get_bot().send_message(
                chat_id=int(ADMIN_IDS[0]),
                text=f"❌ **User cancelled deal for Order #{order_id}.**",
                parse_mode='Markdown'
            )
        return

    if action == 'user_counter':
        db.update_deal_status(deal_id, 'countered')
        context.user_data['user_counter_deal_id'] = deal_id
        context.user_data['awaiting_user_counter_price'] = True
        await query.edit_message_text(
            text="💰 Please send your counter offer price in AED:",
            parse_mode='Markdown'
        )
        return

async def handle_user_counter_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        proposed_price = float(text.replace('AED', '').replace('aed', '').strip())
        if proposed_price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ **Invalid amount.**\n\nPlease enter a valid number (e.g., 500, 750, 1000).",
            parse_mode='Markdown'
        )
        return

    context.user_data['awaiting_user_counter_price'] = False
    context.user_data['awaiting_user_counter_message'] = True
    context.user_data['user_counter_price'] = proposed_price

    await update.message.reply_text(
        f"✅ **Counter offer price noted: AED {proposed_price}**\n\n💬 **Optional: Add a message to your counter offer**\n\nSend your message or type 'skip' to continue:",
        parse_mode='Markdown'
    )

async def handle_user_counter_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    message = None if text.lower() == 'skip' else text

    deal_id = context.user_data.get('user_counter_deal_id')
    if not deal_id:
        await update.message.reply_text("❌ Counter offer session expired. Please try again.")
        return

    order_id = None
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT order_id FROM deals WHERE deal_id = ?', (deal_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        order_id = row[0]

    if not order_id:
        await update.message.reply_text("❌ Original order not found. Please start a new deal.")
        return

    proposed_price = context.user_data.get('user_counter_price')
    if not proposed_price:
        await update.message.reply_text("❌ Counter offer price not found. Please try again.")
        return

    new_deal_id = db.create_deal(
        order_id=order_id,
        proposed_price=proposed_price,
        proposed_by='user',
        message=message
    )

    context.user_data.pop('user_counter_deal_id', None)
    context.user_data.pop('user_counter_price', None)
    context.user_data['awaiting_user_counter_message'] = False

    await send_deal_to_admin(order_id, new_deal_id, update.get_bot())
    await update.message.reply_text(
        "✅ Your counter offer has been sent to admin. Please wait for their response.",
        parse_mode='Markdown'
    )

async def handle_admin_counter_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        proposed_price = float(text.replace('AED', '').replace('aed', '').strip())
        if proposed_price <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ **Invalid amount.**\n\nPlease enter a valid number (e.g., 500, 750, 1000).",
            parse_mode='Markdown'
        )
        return

    context.user_data['awaiting_admin_counter_price'] = False
    context.user_data['awaiting_admin_counter_message'] = True
    context.user_data['admin_counter_price'] = proposed_price

    await update.message.reply_text(
        text=f"✅ **Counter offer price noted: AED {proposed_price}**\n\n💬 **Optional: Add a message to your counter offer**\n\nSend your message or type 'skip' to continue:",
        parse_mode='Markdown'
    )

async def handle_admin_counter_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    message = None if text.lower() == 'skip' else text

    deal_id = context.user_data.get('admin_counter_deal_id')
    if not deal_id:
        await update.message.reply_text("❌ Counter offer session expired. Please try again.")
        return

    order_id = None
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT order_id FROM deals WHERE deal_id = ?', (deal_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        order_id = row[0]

    if not order_id:
        await update.message.reply_text("❌ Original order not found. Please try again.")
        return

    proposed_price = context.user_data.get('admin_counter_price')
    if not proposed_price:
        await update.message.reply_text("❌ Counter offer price not found. Please try again.")
        return

    new_deal_id = db.create_deal(
        order_id=order_id,
        proposed_price=proposed_price,
        proposed_by='admin',
        message=message
    )

    context.user_data.pop('admin_counter_deal_id', None)
    context.user_data.pop('admin_counter_price', None)
    context.user_data['awaiting_admin_counter_message'] = False

    order = db.get_order_with_deals(order_id)
    if order:
        from src.utils.keyboards import get_user_deal_response_keyboard
        latest_deal = order['deals'][0]
        await update.get_bot().send_message(
            chat_id=order['user_id'],
            text=f"💰 **Admin Counter Offer Received!**\n\nService: {SERVICES.get(order['service_type'], {}).get('name', order['service_type'])}\nHours: {order['hours']}\nPrice: AED {latest_deal['proposed_price']}\nMessage: {latest_deal.get('message', 'None')}",
            parse_mode='Markdown',
            reply_markup=get_user_deal_response_keyboard(new_deal_id)
        )

    await update.message.reply_text(
        "✅ Counter offer sent to the customer.",
        parse_mode='Markdown'
    )
