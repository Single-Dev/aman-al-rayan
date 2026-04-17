#!/bin/bash
# Telegram Mini App Setup Script

echo "🚀 Setting up Telegram Mini App..."

# 1. Install dependencies
echo "1️⃣  Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✅ Dependencies installed"

# 2. Initialize database
echo "2️⃣  Initializing database..."
python3 -c "from src.database.db_manager import DatabaseManager; db = DatabaseManager(); print('✅ Database initialized')"

if [ $? -ne 0 ]; then
    echo "⚠️  Database initialization warning (may already exist)"
fi

# 3. Validate configuration
echo "3️⃣  Validating configuration..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

required = ['TELEGRAM_BOT_TOKEN', 'BOT_USERNAME']
missing = [k for k in required if not os.getenv(k)]

if missing:
    print(f'❌ Missing config: {missing}')
    exit(1)
else:
    print('✅ Configuration valid')
"

if [ $? -ne 0 ]; then
    echo "❌ Configuration validation failed"
    exit 1
fi

# 4. Test FastAPI import
echo "4️⃣  Testing FastAPI setup..."
python3 -c "
try:
    from src.mini_app.app import app
    from src.mini_app.security import validate_init_data
    from src.mini_app.models import UserData
    print('✅ FastAPI app imports successfully')
except Exception as e:
    print(f'❌ FastAPI import error: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# 5. Verify folders
echo "5️⃣  Verifying folder structure..."
dirs=(
    "src/mini_app"
    "src/mini_app/api"
    "src/mini_app/versions/lite"
    "src/mini_app/versions/booking"
    "src/mini_app/static/lite"
    "src/mini_app/static/booking"
)

for dir in "${dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "❌ Missing directory: $dir"
        exit 1
    fi
done
echo "✅ All folders exist"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "1. Terminal 1: python3 -m uvicorn src.mini_app.app:app --host 0.0.0.0 --port 8000 --reload"
echo "2. Terminal 2: python3 main.py"
echo ""
echo "Or use: ./deploy.sh to start both services"
