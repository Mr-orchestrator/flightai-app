"""
FlightAI Authentication
Email + password auth with bcrypt hashing and JWT tokens
"""

import os
from datetime import datetime, timedelta

import bcrypt
from jose import jwt, JWTError
from fastapi import HTTPException, Request


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "flightai-dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, email: str, name: str) -> str:
    """Create a JWT token with user info."""
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRY_DAYS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Returns payload dict."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_current_user(request: Request) -> dict:
    """
    FastAPI dependency: extract and validate JWT from Authorization header.
    Returns dict with user_id, email, name.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authentication token")

    token = auth_header.split(" ", 1)[1]
    payload = decode_token(token)

    return {
        "user_id": payload["sub"],
        "email": payload["email"],
        "name": payload["name"],
    }


def get_optional_user(request: Request) -> dict | None:
    """
    Extract user from JWT if present, return None if not authenticated.
    Does not raise — used for optional auth on endpoints like search-flights.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return {
            "user_id": payload["sub"],
            "email": payload["email"],
            "name": payload["name"],
        }
    except JWTError:
        return None
