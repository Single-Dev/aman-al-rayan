from telegram import Update
from telegram.ext import ContextTypes
from src.database.db_manager import DatabaseManager
from src.utils.keyboards import get_cart_keyboard, get_main_menu_keyboard, get_services_inline_keyboard
from src.utils.messages import get_cart_summary, get_services_message
from src.config import SERVICES

db = DatabaseManager()

async def handle_view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View shopping cart"""
    user_id = update.effective_user.id
    query = update.callback_query
    message = update.message
    
    cart_items = db.get_cart(user_id)
    
    if query:
        await query.answer()
    
    cart_msg = get_cart_summary(cart_items)
    
    if cart_items:
        keyboard = get_cart_keyboard(cart_items)
    else:
        keyboard = get_main_menu_keyboard()
    
    if query:
        await query.edit_message_text(
            text=cart_msg,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    else:
        await message.reply_text(
            text=cart_msg,
            parse_mode='Markdown',
            reply_markup=keyboard
        )

async def handle_add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add service to cart from quote"""
    query = update.callback_query
    await query.answer("✅ Added to cart!")
    
    user_id = update.effective_user.id
    service_id = context.user_data.get('selected_service')
    hours = context.user_data.get('selected_hours', 1)
    
    if service_id and service_id in SERVICES:
        service = SERVICES[service_id]
        estimated_price = service['hourly_rate'] * hours
        
        db.add_to_cart(user_id, service_id, hours, estimated_price)
        
        await query.edit_message_text(
            text="✅ Service added to cart!\n\nWould you like to add more services or checkout?",
            reply_markup=get_services_inline_keyboard()
        )

async def handle_remove_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove item from cart"""
    query = update.callback_query
    await query.answer("✅ Item removed!")
    
    # Extract cart_id from callback_data
    cart_id = int(query.data.split('_')[-1])
    
    user_id = update.effective_user.id
    db.remove_from_cart(cart_id)
    
    # Refresh cart view
    await handle_view_cart(update, context)

async def handle_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checkout from cart"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    cart_items = db.get_cart(user_id)
    
    if not cart_items:
        await query.edit_message_text(
            text="🛒 Your cart is empty!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Create orders for each cart item
    order_ids = []
    total_price = 0
    
    for item in cart_items:
        order_id = db.create_order(
            user_id=user_id,
            service_type=item['service_type'],
            hours=item['hours'],
            estimated_price=item['estimated_price']
        )
        order_ids.append(order_id)
        total_price += item['estimated_price']
    
    # Clear cart
    db.clear_cart(user_id)
    
    checkout_msg = f"""
✅ **Checkout Successful!**

Orders Created: {len(order_ids)}
Order IDs: {', '.join([f'#{id}' for id in order_ids])}

💰 Total: AED {total_price}

📱 Our team will contact you to confirm:
• Preferred dates & times
• Special requests
• Final pricing

Thank you for your order! 🙏
    """
    
    await query.edit_message_text(text=checkout_msg, parse_mode='Markdown', reply_markup=None)
    await query.message.reply_text(
        text="✅ Checkout complete! What would you like to do next?",
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

async def handle_clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear entire cart"""
    user_id = update.effective_user.id
    db.clear_cart(user_id)
    
    await update.message.reply_text(
        text="🛒 Cart cleared!",
        reply_markup=get_main_menu_keyboard()
    )
