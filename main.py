#!/usr/bin/env python3
"""
Aman Al Rayan Telegram Bot
Main entry point for the Telegram bot application
"""

import logging
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import re

from src.config import TELEGRAM_BOT_TOKEN
from src.database.db_manager import DatabaseManager

# Import handlers
from src.handlers.start_handler import handle_start, handle_help
from src.handlers.service_handler import (
    handle_services,
    handle_service_selection,
    handle_hours_selection,
    handle_admin_deal_action,
    handle_user_deal_response,
)
from src.handlers.order_handler import (
    handle_confirm_order,
    handle_schedule_date,
    handle_time_selection,
    handle_add_notes,
    handle_cancel_order,
    handle_finalize_order,
    handle_contact_share,
    handle_location_share,
    handle_text_input,
)
from src.handlers.cart_handler import (
    handle_view_cart,
    handle_add_to_cart,
    handle_remove_from_cart,
    handle_checkout,
    handle_clear_cart,
)
from src.handlers.contact_handler import handle_contact, handle_contact_action
from src.handlers.subscription_handler import (
    handle_subscriptions,
    handle_plan_selection,
    handle_subscription_confirmation,
    handle_my_subscription,
)
from src.handlers.referral_handler import handle_referral, handle_set_balance
from src.handlers.admin_handler import (
    handle_admin_command,
    handle_admin_callback,
    handle_balance_edit,
    handle_admin_set_balance_message,
    handle_setbalance_command,
)
from src.handlers.navigation_handler import handle_back_to_main, handle_back_to_services
from src.handlers.webapp_handler import handle_web_app_data

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


service_pattern = re.compile(r"^service_.*$")
hours_pattern = re.compile(r"^hours_.*$")
plan_pattern = re.compile(r"^plan_.*$")
contact_action_pattern = re.compile(r"^contact_.*$")


async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors safely for both messages and callback queries."""
    logger.error("Exception while handling update:", exc_info=context.error)

    if update is None:
        return

    callback_query = getattr(update, "callback_query", None)
    if callback_query:
        try:
            await callback_query.answer(
                "Sorry, an error occurred. Please try again.",
                show_alert=True,
            )
        except Exception:
            pass

    message = getattr(update, "message", None)
    if message:
        try:
            await message.reply_text(
                "Sorry, an error occurred. Please try again."
            )
        except Exception:
            pass


def main():
    """Start the bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error(
            "TELEGRAM_BOT_TOKEN not found. Please set it in your .env file."
        )
        return

    db = DatabaseManager()
    db.init_database()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("help", handle_help))

    application.add_handler(
        CallbackQueryHandler(handle_services, pattern=r"^services$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_service_selection, pattern=service_pattern)
    )
    application.add_handler(
        CallbackQueryHandler(handle_hours_selection, pattern=hours_pattern)
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_admin_deal_action,
            pattern=r"^(accept_deal|counter_deal|reject_deal)_.*$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_user_deal_response,
            pattern=r"^(user_accept|user_counter|user_cancel)_.*$",
        )
    )
    application.add_handler(
        CallbackQueryHandler(handle_confirm_order, pattern=r"^confirm_order_.*$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_schedule_date, pattern=r"^date_.*$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_time_selection, pattern=r"^time_.*$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_view_cart, pattern=r"^cart$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_add_to_cart, pattern=r"^add_to_cart_.*$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_remove_from_cart, pattern=r"^remove_from_cart_.*$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_checkout, pattern=r"^checkout$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_clear_cart, pattern=r"^clear_cart$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_add_notes, pattern=r"^add_notes_.*$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_cancel_order, pattern=r"^cancel_order_.*$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_finalize_order, pattern=r"^finalize_order_.*$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_contact, pattern=r"^contact$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_contact_action, pattern=contact_action_pattern)
    )
    application.add_handler(
        CallbackQueryHandler(handle_subscriptions, pattern=lambda data: data == "subscription")
    )
    application.add_handler(
        CallbackQueryHandler(handle_plan_selection, pattern=plan_pattern)
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_subscription_confirmation,
            pattern=r"^subscribe_plan_.*$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(handle_my_subscription, pattern=r"^my_subscription$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_back_to_main, pattern=r"^back_to_main$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_back_to_services, pattern=r"^back_to_services$")
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_admin_callback,
            pattern=r"^(admin_|back_to_admin|view_user_|edit_balance_|user_page_).*$"
        )
    )

    application.add_handler(CommandHandler("referral", handle_referral))
    application.add_handler(CallbackQueryHandler(handle_referral, pattern=r"^referral$"))
    application.add_handler(CommandHandler("set_balance", handle_set_balance))
    application.add_handler(CommandHandler("setbalance", handle_setbalance_command))
    application.add_handler(CommandHandler("admin", handle_admin_command))

    application.add_handler(
        MessageHandler(filters.CONTACT, handle_contact_share)
    )
    application.add_handler(
        MessageHandler(filters.LOCATION, handle_location_share)
    )
    # Handle WebApp data from mini app
    application.add_handler(
        MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data)
    )
    # Handle all other text input
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)
    )
    # Handle admin-specific message operations (AFTER text input)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_set_balance_message)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_balance_edit)
    )

    application.add_error_handler(error_handler)

    logger.info("Bot started successfully!")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()