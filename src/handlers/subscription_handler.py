from telegram import Update
from telegram.ext import ContextTypes
from src.database.db_manager import DatabaseManager
from src.utils.keyboards import get_subscription_plans_keyboard, get_main_menu_keyboard, get_yes_no_keyboard
from src.utils.messages import get_subscription_plans_message
from src.config import SUBSCRIPTION_PLANS, CONTACT_INFO
import logging

logger = logging.getLogger(__name__)

db = DatabaseManager()

async def handle_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subscription browsing"""
    query = update.callback_query
    message = update.message
    
    if query:
        await query.answer()
        text = get_subscription_plans_message()
        await query.edit_message_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=get_subscription_plans_keyboard()
        )
    else:
        text = get_subscription_plans_message()
        await message.reply_text(
            text=text,
            parse_mode='Markdown',
            reply_markup=get_subscription_plans_keyboard()
        )

async def handle_plan_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subscription plan selection"""
    query = update.callback_query
    logger.info(f"Handling plan selection: {query.data}")
    await query.answer()
    
    # Extract plan_id from callback_data
    plan_id = query.data.replace('plan_', '')
    
    if plan_id not in SUBSCRIPTION_PLANS:
        await query.edit_message_text("Plan not found.")
        return
    
    plan = SUBSCRIPTION_PLANS[plan_id]
    context.user_data['selected_plan'] = plan_id
    
    plan_detail_msg = f"""
💼 **{plan['name']}**

📅 Frequency: {plan['frequency']}
💰 Price: AED {plan['price_min']}-{plan['price_max']}/month

📝 Description:
{plan['description']}

✅ **Benefits:**
• Save up to 20% compared to one-time bookings
• Priority scheduling
• Dedicated cleaning team
• Flexible pause/resume
• Cancel anytime, no contracts

Would you like to subscribe to this plan?
    """
    
    await query.edit_message_text(
        text=plan_detail_msg,
        parse_mode='Markdown',
        reply_markup=get_yes_no_keyboard('subscribe_plan')
    )

async def handle_subscription_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle subscription confirmation"""
    query = update.callback_query
    await query.answer()
    
    action = query.data.split('_')[-1]
    
    if action == 'yes':
        user_id = update.effective_user.id
        plan_id = context.user_data.get('selected_plan')
        
        if plan_id:
            # Save subscription to database
            subscription_id = db.add_subscription(user_id, plan_id)
            plan = SUBSCRIPTION_PLANS.get(plan_id, {})
            
            # Get user details
            user = db.get_user(user_id)
            
            # Send subscription request directly to admin
            await send_subscription_to_admin(subscription_id, plan, user, update.get_bot())
            
            confirmation_msg = "Thank you for your subscription request! \nWe will connect you soon."
            
            await query.edit_message_text(text=confirmation_msg)
            await update.effective_chat.send_message(
                text="What would you like to do next?",
                reply_markup=get_main_menu_keyboard()
            )
            return
    else:
        await query.edit_message_text(
            text="❌ Subscription request cancelled.\n\nWould you like to explore other plans?",
            reply_markup=get_subscription_plans_keyboard()
        )

async def handle_my_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's active subscription"""
    user_id = update.effective_user.id
    subscription = db.get_user_subscription(user_id)
    
    if subscription:
        plan = SUBSCRIPTION_PLANS.get(subscription['plan_type'], {})
        msg = f"""
📋 **Your Active Subscription:**

Subscription ID: #{subscription['subscription_id']}
Plan: {plan.get('name', 'Unknown')}
Status: {subscription['status'].upper()}
Started: {subscription['start_date']}

Monthly Price: AED {plan.get('price_min', 'N/A')}-{plan.get('price_max', 'N/A')}

✅ You're saving 20% with this subscription!

Need to manage your subscription?
Contact us:
📞 {CONTACT_INFO['phone']}
💬 {CONTACT_INFO['whatsapp']}
        """
    else:
        msg = """
📋 **No Active Subscription**

You don't have an active subscription yet.

Browse our plans to:
✅ Save up to 20%
✅ Flexible scheduling
✅ No contracts
✅ Cancel anytime
        """
    
    await update.message.reply_text(
        text=msg,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

async def send_subscription_to_admin(subscription_id: int, plan: dict, user: dict, bot):
    """Send subscription request notification to admin"""
    from src.config import ADMIN_IDS
    from datetime import datetime
    
    if not ADMIN_IDS:
        return
    
    admin_message = f"""
💼 **NEW SUBSCRIPTION REQUEST!**

📋 **Subscription Details:**
• Subscription ID: #{subscription_id}
• Plan: {plan.get('name', 'Unknown')}
• Frequency: {plan.get('frequency', '')}
• Monthly Price: AED {plan.get('price_min', 'N/A')}-{plan.get('price_max', 'N/A')}

👤 **Customer Information:**
• Name: {user.get('first_name', 'N/A')} {user.get('last_name', 'N/A')}
• Username: @{user.get('username', 'N/A')}
• Phone: {user.get('phone_number', 'N/A')}
• Email: {user.get('email', 'N/A')}
• Address: {user.get('address', 'N/A')}

⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📞 **Action Required:** Contact customer to finalize subscription details and arrange first service.

💬 **Note:** This subscription request was sent directly from the bot - no website API submission needed.
    """
    
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=int(admin_id),
                text=admin_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send subscription notification to {admin_id}: {e}")
