#!/bin/bash
# Telegram Mini App Deployment Script
# Runs both FastAPI (mini app) and Telegram Bot

set -e

echo "🚀 Telegram Mini App with Bot - Deployment"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if dependencies are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
python3 -c "import telegram, fastapi, uvicorn" 2>/dev/null || {
    echo -e "${RED}❌ Missing dependencies. Run: pip install -r requirements.txt${NC}"
    exit 1
}
echo -e "${GREEN}✅ Dependencies OK${NC}"

# Create logs directory if it doesn't exist
mkdir -p logs

# Clean up any stray processes
echo -e "${YELLOW}Cleaning up old processes...${NC}"
pkill -f "uvicorn src.mini_app" || true
pkill -f "main.py" || true
sleep 1

# Start FastAPI server
echo -e "${YELLOW}Starting mini app server (port 8000)...${NC}"
python3 -m uvicorn src.mini_app.app:app --host 0.0.0.0 --port 8000 > logs/miniapp.log 2>&1 &
MINIAPP_PID=$!
sleep 2

# Check if FastAPI started successfully
if ! kill -0 $MINIAPP_PID 2>/dev/null; then
    echo -e "${RED}❌ Failed to start mini app${NC}"
    cat logs/miniapp.log
    exit 1
fi
echo -e "${GREEN}✅ Mini app started (PID: $MINIAPP_PID)${NC}"

# Start Telegram Bot
echo -e "${YELLOW}Starting Telegram bot...${NC}"
python3 main.py > logs/bot.log 2>&1 &
BOT_PID=$!
sleep 2

# Check if bot started successfully
if ! kill -0 $BOT_PID 2>/dev/null; then
    echo -e "${RED}❌ Failed to start bot${NC}"
    kill $MINIAPP_PID
    cat logs/bot.log
    exit 1
fi
echo -e "${GREEN}✅ Bot started (PID: $BOT_PID)${NC}"

echo ""
echo -e "${GREEN}=========================================="
echo "✅ Services Running Successfully!"
echo "=========================================${NC}"
echo "Mini App Server: http://localhost:8000"
echo "Mini App Lite:   http://localhost:8000/lite"
echo "Mini App Booking: http://localhost:8000/booking"
echo "API Docs:        http://localhost:8000/docs"
echo ""
echo "Bot Status: Running (polling mode)"
echo "Send /start to your bot to test"
echo ""
echo -e "${YELLOW}Logs:${NC}"
echo "  Mini app: tail -f logs/miniapp.log"
echo "  Bot:      tail -f logs/bot.log"
echo ""
echo -e "${YELLOW}To stop services:${NC}"
echo "  kill $MINIAPP_PID     # Mini app"
echo "  kill $BOT_PID         # Bot"
echo "  ./deploy.sh stop      # Both"
echo ""

# Handle cleanup
trap "echo -e '\n${YELLOW}Stopping services...${NC}' && kill $MINIAPP_PID $BOT_PID 2>/dev/null; echo -e '${GREEN}Services stopped${NC}'" EXIT

# Keep script running
wait
