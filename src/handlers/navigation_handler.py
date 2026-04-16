from telegram import Update
from telegram.ext import ContextTypes
from src.utils.keyboards import get_main_menu_keyboard
from src.database.db_manager import DatabaseManager

db = DatabaseManager()

async def handle_back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button to main menu"""
    query = update.callback_query
    await query.answer()
    
    text = """
🏠 **Main Menu:**

What would you like to do?

🧹 Browse our services
📋 Book a cleaning session
💼 Subscribe to regular plans
🛒 Manage your cart
📞 Contact us

Let's get started! 👇
    """
    
    await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=None)
    await query.message.reply_text(
        text="Welcome back to the main menu!",
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )

async def handle_back_to_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back button to services"""
    from src.handlers.service_handler import handle_services
    await handle_services(update, context)

async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands"""
    await update.message.reply_text(
        text="❓ I don't understand that command.\n\nUse the buttons below to navigate.",
        reply_markup=get_main_menu_keyboard()
    )
