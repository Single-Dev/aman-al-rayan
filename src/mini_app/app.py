from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.mini_app.api.router import router as api_router
from src.config import MINI_APP_CONFIG

# Create FastAPI app
app = FastAPI(
    title="Telegram Mini App",
    description="Telegram Mini App for service booking",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://web.telegram.org",
        "https://*.telegram.org",
        "http://localhost:3000",
        "http://localhost:8000",
        "*"  # For development, restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

# Mount static files for mini apps
static_dir = os.path.join(os.path.dirname(__file__), 'static')
if os.path.exists(static_dir):
    # Note: StaticFiles will be added after version routes are created
    pass


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - info about mini app"""
    return """
    <html>
        <head><title>Telegram Mini App</title></head>
        <body>
            <h1>Telegram Mini App</h1>
            <p>Use <code>/lite</code> or <code>/booking</code> to access the app versions.</p>
            <p><a href="/docs">API Documentation</a></p>
        </body>
    </html>
    """


@app.get("/lite", response_class=HTMLResponse)
async def lite_version(init_data: str = None):
    """Lite version of mini app"""
    lite_html = os.path.join(os.path.dirname(__file__), 'static', 'lite', 'index.html')

    if os.path.exists(lite_html):
        with open(lite_html, 'r') as f:
            content = f.read()
            # Inject initData into the page
            if init_data:
                content = content.replace('<!--INIT_DATA_PLACEHOLDER-->', f'<script>window.initData="{init_data}";</script>')
            return content
    else:
        return "<h1>Lite version not found</h1>"


@app.get("/booking", response_class=HTMLResponse)
async def booking_version(init_data: str = None):
    """Booking version of mini app"""
    booking_html = os.path.join(os.path.dirname(__file__), 'static', 'booking', 'index.html')

    if os.path.exists(booking_html):
        with open(booking_html, 'r') as f:
            content = f.read()
            # Inject initData into the page
            if init_data:
                content = content.replace('<!--INIT_DATA_PLACEHOLDER-->', f'<script>window.initData="{init_data}";</script>')
            return content
    else:
        return "<h1>Booking version not found</h1>"


if __name__ == "__main__":
    import uvicorn

    port = MINI_APP_CONFIG.get('port', 8000)
    uvicorn.run(app, host="0.0.0.0", port=port)
