from telegram import Update
from telegram.ext import ContextTypes
from src.utils.keyboards import get_contact_keyboard, get_main_menu_keyboard
from src.utils.messages import get_contact_message
from src.config import CONTACT_INFO
from src.utils.api_client import WebsiteAPI

api = WebsiteAPI()

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact information"""
    query = update.callback_query
    message = update.message
    
    contact_msg = get_contact_message()
    
    if query:
        await query.answer()
        await query.edit_message_text(text=contact_msg, parse_mode='Markdown', reply_markup=None)
        await query.message.reply_text(
            text="Choose an option from the main menu below.",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.reply_text(
            text=contact_msg,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )

async def handle_contact_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle contact action selection"""
    query = update.callback_query
    logger.info(f"Handling contact action: {query.data}")
    await query.answer()
    
    action = query.data.replace('contact_', '')
    
    if action == 'call':
        text = f"""
☎️ **Call Us Now:**

📞 {CONTACT_INFO['phone']}
📞 {CONTACT_INFO['phone2']}
📞 {CONTACT_INFO['phone3']}

Available 24/7 for inquiries!
        """
    
    elif action == 'whatsapp':
        whatsapp_url = api.get_whatsapp_url("Hi, I'm interested in booking a cleaning service!")
        text = f"""
💬 **Chat on WhatsApp:**

Click the link below to message us:
{whatsapp_url}

Or send to: {CONTACT_INFO['whatsapp']}

Fastest response time! ✅
        """
    
    elif action == 'email':
        text = f"""
📧 **Send us an Email:**

Email: {CONTACT_INFO['email']}

Include:
• Your location
• Preferred service type
• Preferred dates/times
• Any special requests

We'll respond within 2 hours!
        """
    
    elif action == 'website':
        website_url = "https://aman-al-rayan.base44.app"
        text = f"""
🌐 **Visit Our Website:**

{website_url}

On our website you can:
✅ View all services
✅ Get instant quotes
✅ Read customer reviews
✅ Browse subscription plans
✅ Contact us directly
        """
    
    else:
        text = "Action not recognized."
    
    await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=None)
    await query.message.reply_text(
        text="Use the main menu below:",
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )
