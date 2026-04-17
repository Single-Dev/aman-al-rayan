from fastapi import Depends, HTTPException, Query
from typing import Optional
import sys
import os

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.mini_app.security import validate_init_data, parse_user_data
from src.mini_app.models import UserData
from src.config import TELEGRAM_BOT_TOKEN


async def get_user_from_init_data(init_data: Optional[str] = Query(None)) -> UserData:
    """
    Dependency to extract and validate user from Telegram WebApp initData.

    Args:
        init_data: WebAppInitData from Telegram

    Returns:
        Validated UserData

    Raises:
        HTTPException: If init_data is invalid or missing
    """
    if not init_data:
        raise HTTPException(status_code=401, detail="Missing initData")

    # Validate the signature
    params = validate_init_data(init_data, TELEGRAM_BOT_TOKEN)
    if params is None:
        raise HTTPException(status_code=401, detail="Invalid initData signature")

    # Parse user data
    user_info = parse_user_data(params)
    if user_info is None or 'id' not in user_info:
        raise HTTPException(status_code=401, detail="Invalid user data in initData")

    return UserData(**user_info)


async def get_current_user(init_data: str = Query(...)) -> int:
    """
    Get current user ID from validated init_data.

    Args:
        init_data: WebAppInitData from Telegram

    Returns:
        User ID

    Raises:
        HTTPException: If validation fails
    """
    user = await get_user_from_init_data(init_data)
    return user.id
