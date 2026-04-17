# Telegram Mini App Setup Guide

This application now includes a fully integrated Telegram mini app system with two versions: **Lite** and **Booking**.

## Features

### Lite Version
- Quick service browser
- Fast quote generation
- Minimal interface (< 20KB)
- Perfect for quick service lookups

### Booking Version
- Full calendar date picker
- Time slot selection  
- Deal negotiation
- Service comparison
- Complete order summary

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup:**
   Ensure your `.env` file contains:
   ```
   TELEGRAM_BOT_TOKEN=your_token
   MINI_APP_URL=http://localhost:8000  # or your production URL
   MINI_APP_PORT=8000
   ```

## Running the Application

### Option 1: Run Both Separately (Development)

**Terminal 1 - Start the mini app server:**
```bash
python -m uvicorn src.mini_app.app:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Start the Telegram bot:**
```bash
python main.py
```

### Option 2: Run as Background Services (Production)

**Using systemd:**

Create `/etc/systemd/system/telegram-miniapp.service`:
```ini
[Unit]
Description=Telegram Mini App Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/tg-app
ExecStart=/usr/bin/python3 -m uvicorn src.mini_app.app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/telegram-bot.service`:
```ini
[Unit]
Description=Telegram Service Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/tg-app
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable telegram-miniapp telegram-bot
sudo systemctl start telegram-miniapp telegram-bot
```

## Architecture

### Mini App Folder Structure
```
src/mini_app/
├── app.py              # FastAPI application
├── security.py         # Telegram signature validation
├── models.py           # Pydantic models
├── api/
│   ├── router.py       # API endpoints
│   └── dependencies.py # Auth dependencies
├── versions/
│   ├── lite/          # Lightweight version
│   └── booking/       # Full booking version
└── static/
    ├── lite/          # Lite HTML/CSS/JS
    └── booking/       # Booking HTML/CSS/JS
```

### Database Schema

New tables added:
- `mini_app_sessions` - Track active mini app sessions
- `user_preferences` - Store user version preferences

### API Endpoints

**Base URL:** `/api/v1`

- `GET /user` - Get current user profile
- `GET /services` - List all services
- `POST /quote` - Get Quote for a service
- `POST /submit-order` - Submit an order from mini app
- `GET /versions` - Get available app versions
- `GET /health` - Health check

## Security Considerations

1. **Telegram Signature Validation:**
   - All mini app requests validate the `initData` signature using HMAC-SHA256
   - Signature uses Bot Token as the secret key
   - Invalid signatures are rejected with 401 Unauthorized

2. **CORS Configuration:**
   - Whitelist Telegram domains: `https://web.telegram.org`
   - Restrict in production to Telegram domains only

3. **Database:**
   - User data from mini app is stored in the same SQLite database
   - Orders created in mini app use the same system as bot orders

## Integration with Bot

When a user clicks "📲 Mini App" button in the bot:
1. Bot shows version selection (Lite or Booking)
2. Bot generates a WebApp URL with user context
3. Mini app validates user via Telegram signature
4. User completes action in mini app
5. Mini app sends data back via `Telegram.WebApp.sendData()`
6. Bot receives `web_app_data` update with order information
7. Order is saved to database and admin is notified

## Testing the Mini App

1. **Start both services:**
   ```bash
   # Terminal 1
   python -m uvicorn src.mini_app.app:app --reload
   
   # Terminal 2
   python main.py
   ```

2. **Send `/start` to your bot on Telegram**

3. **Click "📲 Mini App" button**

4. **Select Lite or Booking version**

5. **Complete an order in the mini app**

6. **Check bot chat for confirmation message**

## Switching Between Versions

Users can change their preferred version:
- Each time they open the mini app, their preference is updated
- Next time they open, they'll see the last-used version by default
- They can always switch versions by clicking the alternate option

## Troubleshooting

### Mini app not loading
- Check `MINI_APP_URL` in `.env` (must be HTTPS in production, HTTP in development)
- Ensure FastAPI server is running on the correct port
- Check browser console for JavaScript errors

### Orders not being received
- Check that `handle_web_app_data` is registered in main.py
- Verify `allowed_updates` includes `web_app_data`
- Check bot logs for errors

### Validation errors
- Ensure `TELEGRAM_BOT_TOKEN` is correct
- Check that initData is being passed to the mini app
- Verify timestamp is recent (within 24 hours)

## Performance Tips

- **Lite version:** < 50KB total size (HTML + inline CSS + JS)
- **Booking version:** ~200KB (includes flatpickr calendar library)
- Cache static assets at CDN level in production
- Use gzip compression for API responses
- Consider Redis for session management at scale

## Deployment to Production

1. **Get HTTPS URL** for mini app (Telegram requires HTTPS)
2. **Update MINI_APP_URL** in `.env`
3. **Validate Telegram domain** in mini app CORS settings
4. **Use production database** (not test SQLite)
5. **Add rate limiting** to API endpoints
6. **Monitor logs** for errors and security issues
7. **Set up auto-restart** via systemd or PM2

## Support for Adding More Versions

To add a new mini app version (e.g., "premium"):

1. Create folder: `src/mini_app/versions/premium/`
2. Add HTML file: `src/mini_app/static/premium/index.html`
3. Update `MINI_APP_VERSIONS` in `src/config.py`
4. Add route in `src/mini_app/app.py`:
   ```python
   @app.get("/premium", response_class=HTMLResponse)
   async def premium_version(init_data: str = None):
       # Load premium HTML
   ```
5. Version is automatically available via bot UI

## Next Steps

- [ ] Add analytics/logging for mini app usage
- [ ] Implement Redis caching for user preferences
- [ ] Add push notifications from mini app
- [ ] Create admin dashboard for mini app analytics
- [ ] A/B test different UI layouts
- [ ] Add PWA manifest for app-like experience
