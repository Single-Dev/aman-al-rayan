# Simple Telegram Mini App - Setup Guide

Your Telegram bot now has an integrated mini app using **app.html**!

## 📁 What You Have

- **app.html** - The mini app UI (clean HTML file, all-in-one)
- **Telegram Bot** - Handles commands and displays the mini app button
- **Built-in Integration** - Bot automatically sends/receives data from the mini app

## 🚀 Quick Setup

### Step 1: Deploy app.html to Vercel

```bash
# 1. Go to Vercel: https://vercel.com/new
# 2. Create a project → "Import Git Repository"
# 3. Select your repo
# 4. Deploy
# You'll get: https://your-project.vercel.app
```

### Step 2: Get Your app.html URL

After Vercel deployment, your URL will be:
```
https://your-project.vercel.app/app.html
```

### Step 3: Update .env

Edit `.env`:
```
MINI_APP_URL=https://your-project.vercel.app/app.html
```

### Step 4: Run the Bot

```bash
python3 main.py
```

### Step 5: Test in Telegram

1. Send `/start` to your bot: **@aman_al_rayan_bot**
2. Click **"📲 Book Service"** button
3. The mini app opens! ✅

## 📋 Flow Diagram

```
User sends /start
    ↓
Bot shows "📲 Book Service" button
    ↓
User clicks button
    ↓
app.html opens in Telegram
    ↓
User selects service, date, time
    ↓
User clicks "Send Booking Request"
    ↓
Data sent back to bot
    ↓
Bot shows confirmation message
    ↓
Admin gets notified
```

## 📱 Features in app.html

- **Service Selection** - Choose from 5 services
- **Date Picker** - Select preferred date
- **Time Slot** - Optional time selection
- **Price Display** - Shows estimated price range
- **Special Requests** - Add notes
- **One-Click Booking** - Send to bot

## 🔧 How It Works

### When User Clicks "Book Service"
- Telegram opens the WebApp at `MINI_APP_URL`
- User is authenticated automatically by Telegram
- User completes the form

### When User Submits
```javascript
// app.html sends this data:
{
  "service_id": "deep_cleaning",
  "service_name": "✨ Deep Cleaning",
  "date": "2026-04-20",
  "time": "14:00",
  "price_min": 220,
  "price_max": 280,
  "notes": "..."
}
```

### Bot Receives Data
- Saves order to database
- Sends confirmation to user
- Notifies admin

## 📊 Files Changed

### Created:
- `app.html` - Mini app HTML file
- `src/handlers/webapp_handler.py` - Handles data from mini app

### Updated:
- `main.py` - Added WebApp handler
- `src/handlers/start_handler.py` - Added mini app button
- `src/config.py` - Added MINI_APP_URL config
- `.env` - Added MINI_APP_URL

### Removed/Cleaned:
- ❌ All FastAPI code
- ❌ All vercel.json config
- ❌ All mini_app folder
- ✅ Simplified to just app.html

## 🎯 Deployment Steps (Detailed)

### Option 1: Vercel (Recommended - Free)

1. **Go to Vercel**: https://vercel.com
2. **Sign in with GitHub**
3. **Click "New Project"**
4. **Import your repository**
5. **Click "Deploy"** (automatic)
6. **Wait 1-2 minutes** for deployment
7. **Get URL**: Your project URL appears
8. **Your app.html is at**: `https://your-project.vercel.app/app.html`

### Option 2: GitHub Pages

1. Enable GitHub Pages in repo settings
2. Set source to `main` branch
3. Your public URL: `https://username.github.io/tg-app/app.html`

### Option 3: Any Static Host

Upload `app.html` to any static hosting service and get the direct URL.

## ✅ Complete Setup Checklist

- [ ] Deploy app.html to Vercel/GitHub Pages
- [ ] Get your full app.html URL
- [ ] Update `.env` with `MINI_APP_URL=your_url`
- [ ] Run `python3 main.py`
- [ ] Send `/start` to bot
- [ ] Click "📲 Book Service"
- [ ] Test booking submission
- [ ] Check bot for confirmation
- [ ] Done! ✅

## 🔗 Important Config

In `.env`:
```
MINI_APP_URL=https://your-vercel-domain.vercel.app/app.html
```

In `src/config.py`:
```python
MINI_APP_URL = os.getenv('MINI_APP_URL', 'https://...')
```

## 🚨 Requirements

- **HTTPS URL** (Telegram requires secure connection)
- **Real domain** (not localhost)
- **Valid SSL certificate** (Vercel/GitHub Pages provide this automatically)

## 💡 To Customize

Edit `app.html` to:
- Change colors/styling
- Add/remove services
- Modify price ranges
- Change button text
- Add new fields

All changes are in the `SERVICES` object at the top of the script section.

## 🐛 Troubleshooting

### "Mini app doesn't load"
- Check URL is HTTPS
- Check it's the correct full URL
- Test URL in browser first

### "Bot doesn't get data"
- Check `handle_web_app_data` is registered in `main.py`
- Check `allowed_updates` includes `web_app_data`
- Check logs for errors

### "Button doesn't show"
- Make sure `.env` file is updated
- Restart bot: `python3 main.py`
- Send `/start` again

## 📞 Now You Have

✅ **Simple app.html** - All-in-one HTML file
✅ **Telegram Bot** - Runs locally or anywhere
✅ **Integration** - Automatic data flow
✅ **Orders saved** - In local database
✅ **Admin notifications** - They're notified

**Just deploy app.html and run the bot!** 🚀
