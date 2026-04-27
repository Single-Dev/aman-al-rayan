from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from src.config import SERVICES, SUBSCRIPTION_PLANS

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu keyboard with navigation buttons"""
    from src.config import MINI_APP_URL
    keyboard = [
        [KeyboardButton("📲 Book Service", web_app=WebAppInfo(url=MINI_APP_URL))],
        ["🧹 Services", "💼 Subscriptions"],
        ["📞 Contact", "🤝 Referral"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_phone_request_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard for requesting contact phone number"""
    keyboard = [
        [KeyboardButton("Share phone number", request_contact=True)]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_services_inline_keyboard() -> InlineKeyboardMarkup:
    """Get services selection keyboard"""
    buttons = []
    for service_id, service_info in SERVICES.items():
        buttons.append([InlineKeyboardButton(
            service_info['name'],
            callback_data=f'service_{service_id}'
        )])
    
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data='back_to_main')])
    return InlineKeyboardMarkup(buttons)

def get_hours_selection_keyboard(service_id: str) -> InlineKeyboardMarkup:
    """Get hours selection keyboard"""
    buttons = []
    for hour in range(1, 9):
        buttons.append([InlineKeyboardButton(
            f"{hour} hour{'s' if hour > 1 else ''}",
            callback_data=f'hours_{service_id}_{hour}'
        )])

    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data='back_to_services')])
    return InlineKeyboardMarkup(buttons)

def get_order_confirmation_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Get order confirmation keyboard"""
    buttons = [
        [InlineKeyboardButton("✅ Confirm Order", callback_data=f'confirm_order_{order_id}')],
        [InlineKeyboardButton("❌ Cancel", callback_data=f'cancel_order_{order_id}')],
        [InlineKeyboardButton("📝 Add Notes", callback_data=f'add_notes_{order_id}')],
    ]
    return InlineKeyboardMarkup(buttons)

def get_subscription_plans_keyboard() -> InlineKeyboardMarkup:
    """Get subscription plans keyboard"""
    buttons = []
    for plan_id, plan_info in SUBSCRIPTION_PLANS.items():
        plan_button_text = f"{plan_info['name']} - AED {plan_info['price_min']}-{plan_info['price_max']}"
        buttons.append([InlineKeyboardButton(
            plan_button_text,
            callback_data=f'plan_{plan_id}'
        )])
    
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data='back_to_main')])
    return InlineKeyboardMarkup(buttons)

def get_schedule_date_keyboard() -> InlineKeyboardMarkup:
    """Get date selection keyboard"""
    buttons = [
        [InlineKeyboardButton("📆 Today", callback_data='date_today')],
        [InlineKeyboardButton("📆 Tomorrow", callback_data='date_tomorrow')],
        [InlineKeyboardButton("📆 This Week", callback_data='date_this_week')],
        [InlineKeyboardButton("📆 Next Week", callback_data='date_next_week')],
        [InlineKeyboardButton("📝 Custom Date", callback_data='date_custom')],
        [InlineKeyboardButton("⬅️ Back", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(buttons)

def get_cart_keyboard(cart_items: list) -> InlineKeyboardMarkup:
    """Get cart management keyboard"""
    buttons = []
    for item in cart_items:
        buttons.append([InlineKeyboardButton(
            f"❌ Remove {item.get('service_type', 'Item')}",
            callback_data=f'remove_from_cart_{item["cart_id"]}'
        )])
    
    buttons.append([InlineKeyboardButton("🛍️ Checkout", callback_data='checkout')])
    buttons.append([InlineKeyboardButton("🧹 Continue Shopping", callback_data='back_to_main')])
    
    return InlineKeyboardMarkup(buttons)

def get_contact_keyboard() -> InlineKeyboardMarkup:
    """Get contact options keyboard"""
    buttons = [
        [InlineKeyboardButton("📞 Call Us", callback_data='contact_call')],
        [InlineKeyboardButton("💬 WhatsApp", callback_data='contact_whatsapp')],
        [InlineKeyboardButton("📧 Email", callback_data='contact_email')],
        [InlineKeyboardButton("🌐 Visit Website", callback_data='contact_website')],
        [InlineKeyboardButton("⬅️ Back", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(buttons)

def get_time_selection_keyboard() -> InlineKeyboardMarkup:
    """Get time selection keyboard"""
    buttons = [
        [InlineKeyboardButton("🕐 9:00 AM", callback_data='time_09:00'),
         InlineKeyboardButton("🕐 10:00 AM", callback_data='time_10:00')],
        [InlineKeyboardButton("🕐 11:00 AM", callback_data='time_11:00'),
         InlineKeyboardButton("🕐 12:00 PM", callback_data='time_12:00')],
        [InlineKeyboardButton("🕐 1:00 PM", callback_data='time_13:00'),
         InlineKeyboardButton("🕐 2:00 PM", callback_data='time_14:00')],
        [InlineKeyboardButton("🕐 3:00 PM", callback_data='time_15:00'),
         InlineKeyboardButton("🕐 4:00 PM", callback_data='time_16:00')],
        [InlineKeyboardButton("🕐 5:00 PM", callback_data='time_17:00'),
         InlineKeyboardButton("🕐 6:00 PM", callback_data='time_18:00')],
        [InlineKeyboardButton("📝 Custom Time", callback_data='time_custom')],
        [InlineKeyboardButton("⬅️ Back", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(buttons)

def get_deal_negotiation_keyboard(deal_id: int) -> InlineKeyboardMarkup:
    """Get deal negotiation keyboard for admin"""
    buttons = [
        [InlineKeyboardButton("✅ Accept", callback_data=f'accept_deal_{deal_id}')],
        [InlineKeyboardButton("💰 Counter Offer", callback_data=f'counter_deal_{deal_id}')]
    ]
    return InlineKeyboardMarkup(buttons)

def get_user_deal_response_keyboard(deal_id: int) -> InlineKeyboardMarkup:
    """Get deal response keyboard for user"""
    buttons = [
        [InlineKeyboardButton("✅ Accept", callback_data=f'user_accept_{deal_id}')],
        [InlineKeyboardButton("💰 Counter Offer", callback_data=f'user_counter_{deal_id}')],
        # [InlineKeyboardButton("❌ Reject", callback_data=f'user_cancel_{deal_id}')]
    ]
    return InlineKeyboardMarkup(buttons)

def get_location_request_keyboard() -> ReplyKeyboardMarkup:
    """Get keyboard for requesting location sharing"""
    keyboard = [
        [KeyboardButton("📍 Share Location", request_location=True)]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_yes_no_keyboard(callback_prefix: str) -> InlineKeyboardMarkup:
    """Get yes/no confirmation keyboard"""
    buttons = [
        [InlineKeyboardButton("✅ Yes", callback_data=f'{callback_prefix}_yes'),
         InlineKeyboardButton("❌ No", callback_data=f'{callback_prefix}_no')]
    ]
    return InlineKeyboardMarkup(buttons)
