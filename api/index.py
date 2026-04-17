"""
Vercel ASGI entrypoint for Telegram Mini App
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

# Import FastAPI app
from src.mini_app.app import app

# Export for Vercel (uses Vercel's ASGI handler)
# No changes needed - just import and expose the app
