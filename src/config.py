import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'amanalrayan_bot')
WEBSITE_URL = os.getenv('WEBSITE_URL', 'https://aman-al-rayan.base44.app')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

# Mini App URL
MINI_APP_URL = os.getenv('MINI_APP_URL', 'https://your-vercel-domain.vercel.app/app.html')

# Database Configuration
DATABASE_PATH = 'data/bot_database.db'

# Services Configuration
SERVICES = {
    'standard_cleaning': {
        'name': '🧹 Standard Cleaning',
        'description': 'Regular weekly or bi-weekly cleaning for your home',
    },
    'deep_cleaning': {
        'name': '✨ Deep Cleaning',
        'description': 'Thorough deep cleaning service for all surfaces',
    },
    'office_cleaning': {
        'name': '🏢 Office Cleaning',
        'description': 'Professional office and commercial space cleaning',
    },
    'mosque_cleaning': {
        'name': '🕌 Mosque Cleaning',
        'description': 'Specialized mosque and religious space cleaning',
    },
    'move_in_out': {
        'name': '📦 Move-In/Move-Out',
        'description': 'Complete cleaning for moving in or out',
    }
}

# Subscription Plans
SUBSCRIPTION_PLANS = {
    'basic': {
        'name': 'Basic Sparkle',
        'frequency': 'Every 2 weeks',
        'price_min': 180,
        'price_max': 200,
        'description': 'Ideal for small apartments or low-maintenance homes'
    },
    'premium': {
        'name': 'Premium Shine',
        'frequency': 'Weekly',
        'price_min': 330,
        'price_max': 350,
        'description': 'Perfect for families or busy professionals'
    },
    'elite': {
        'name': 'Elite Maintenance',
        'frequency': '2 times a week',
        'price_min': 750,
        'price_max': 800,
        'description': 'For larger villas or high-end clients'
    }
}

# Contact Information
CONTACT_INFO = {
    'phone': '+971 55 686 5394',
    'phone2': '+971 58 865 7140',
    'phone3': '+971 54 435 8365',
    'email': 'amanalrayan@gmail.com',
    'whatsapp': '+971556865394'
}

# Website Admin Credentials
WEBSITE_ADMIN = {
    'username': 'zet',
    'password': 'zetDXB123'
}
