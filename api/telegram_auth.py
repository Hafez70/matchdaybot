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

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# Get bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> TelegramUser:
    """
    FastAPI dependency to get authenticated Telegram user.
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: TelegramUser = Depends(get_current_user)):
            return {"user_id": user.id}
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )
    
    # Check auth type is "tma"
    if credentials.scheme.lower() != "tma":
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authorization scheme: {credentials.scheme}. Expected 'tma'"
        )
    
    if not BOT_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Bot token not configured"
        )
    
    try:
        init_data = validate_init_data(credentials.credentials, BOT_TOKEN)
        return init_data.user
    except ValueError as e:
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

