"""
Telegram Mini App Authentication for FastAPI
Based on: https://docs.telegram-mini-apps.com/platform/authorizing-user
"""

import os
import hmac
import hashlib
import time
from urllib.parse import parse_qsl
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

# Load environment variables from config.env
config_path = Path(__file__).parent.parent / "config.env"
if config_path.exists():
    load_dotenv(config_path)

# Get bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Development mode - bypass auth for local testing
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
DEV_USER_ID = int(os.getenv("DEV_USER_ID", "93205092"))

# Security scheme
security = HTTPBearer(auto_error=False)


@dataclass
class TelegramUser:
    """Telegram User data from init data"""
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: bool = False
    photo_url: Optional[str] = None


@dataclass
class TelegramInitData:
    """Parsed Telegram Init Data"""
    user: TelegramUser
    auth_date: int
    hash: str
    query_id: Optional[str] = None
    start_param: Optional[str] = None


def parse_user_data(user_str: str) -> TelegramUser:
    """Parse user JSON string from init data"""
    import json
    user_data = json.loads(user_str)
    return TelegramUser(
        id=user_data.get("id", 0),
        first_name=user_data.get("first_name", ""),
        last_name=user_data.get("last_name"),
        username=user_data.get("username"),
        language_code=user_data.get("language_code"),
        is_premium=user_data.get("is_premium", False),
        photo_url=user_data.get("photo_url")
    )


def validate_init_data(init_data: str, bot_token: str, expires_in: int = 3600) -> TelegramInitData:
    """
    Validate Telegram Mini App init data.
    
    Args:
        init_data: Raw init data string from Telegram WebApp
        bot_token: Your bot's token
        expires_in: How long the init data is valid (in seconds)
    
    Returns:
        TelegramInitData object with parsed user info
    
    Raises:
        ValueError: If validation fails
    """
    # Parse the init data
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    
    if "hash" not in parsed:
        raise ValueError("Missing hash in init data")
    
    received_hash = parsed.pop("hash")
    
    # Check auth_date is not expired
    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > expires_in:
        raise ValueError("Init data expired")
    
    # Create data-check-string
    # Sort alphabetically and join with newlines
    data_check_arr = sorted([f"{k}={v}" for k, v in parsed.items()])
    data_check_string = "\n".join(data_check_arr)
    
    # Create secret key: HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256
    ).digest()
    
    # Calculate hash: HMAC-SHA256(secret_key, data_check_string)
    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Compare hashes
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid hash - data may be tampered")
    
    # Parse user data
    if "user" not in parsed:
        raise ValueError("Missing user in init data")
    
    user = parse_user_data(parsed["user"])
    
    return TelegramInitData(
        user=user,
        auth_date=auth_date,
        hash=received_hash,
        query_id=parsed.get("query_id"),
        start_param=parsed.get("start_param")
    )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> TelegramUser:
    """
    FastAPI dependency to get authenticated Telegram user.
    Checks both Authorization header and X-Telegram-Init-Data header (for Apache proxy).
    In DEV_MODE, returns a mock user for local testing.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: TelegramUser = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # DEV MODE: Return mock user for local testing
    if DEV_MODE:
        logger.info(f"[DEV MODE] Returning mock user ID: {DEV_USER_ID}")
        return TelegramUser(
            id=DEV_USER_ID,
            first_name="Dev User",
            username="devuser"
        )
    
    init_data_raw: Optional[str] = None
    
    # Try Authorization header first
    if credentials and credentials.scheme.lower() == "tma":
        init_data_raw = credentials.credentials
        logger.info("Auth via Authorization header")
    
    # Fallback to X-Telegram-Init-Data header (Apache strips Authorization)
    if not init_data_raw:
        init_data_raw = request.headers.get("X-Telegram-Init-Data")
        if init_data_raw:
            logger.info("🔐 Auth via X-Telegram-Init-Data header")
    
    if not init_data_raw:
        logger.warning("🔴 Auth failed: No credentials provided")
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )
    
    if not BOT_TOKEN:
        logger.error("🔴 Auth failed: BOT_TOKEN not configured!")
        raise HTTPException(
            status_code=500,
            detail="Bot token not configured"
        )
    
    logger.info(f"🔐 BOT_TOKEN present: {BOT_TOKEN[:10]}...")
    
    try:
        init_data = validate_init_data(init_data_raw, BOT_TOKEN)
        logger.info(f"✅ Auth success for user {init_data.user.id}")
        return init_data.user
    except ValueError as e:
        logger.warning(f"🔴 Auth failed: {e}")
        logger.debug(f"🔴 Init data (first 100 chars): {init_data_raw[:100]}...")
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[TelegramUser]:
    """
    FastAPI dependency to get optional Telegram user.
    Returns None if not authenticated (for public endpoints).
    """
    if not credentials or credentials.scheme.lower() != "tma":
        return None
    
    if not BOT_TOKEN:
        return None
    
    try:
        init_data = validate_init_data(credentials.credentials, BOT_TOKEN)
        return init_data.user
    except ValueError:
        return None

