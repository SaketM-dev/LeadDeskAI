"""Supabase Auth token verification and active staff authorization."""
import os
from typing import Optional

import httpx
from fastapi import Depends, Header, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import engine


def require_staff_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """Validate the bearer token with Supabase Auth and require an active staff mapping."""
    base_url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    anon_key = os.getenv("SUPABASE_ANON_KEY", "").strip()
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Sign in is required.")
    if not base_url or not anon_key:
        raise HTTPException(status_code=503, detail="Supabase authentication is not configured.")

    try:
        response = httpx.get(
            f"{base_url}/auth/v1/user",
            headers={"apikey": anon_key, "Authorization": f"Bearer {token}"},
            timeout=5.0,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Supabase authentication is unavailable.") from exc
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Your session is invalid or expired. Sign in again.")
    try:
        auth_user = response.json()
        auth_user_id = str(auth_user["id"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=401, detail="Supabase returned an invalid user session.")

    try:
        with engine.connect() as connection:
            staff = connection.execute(text("""
                SELECT id, email, display_name, role, is_active
                FROM public.app_users
                WHERE supabase_auth_user_id = :auth_user_id
                LIMIT 1
            """), {"auth_user_id": auth_user_id}).mappings().first()
    except SQLAlchemyError as exc:
        # Do not return connection details or credentials to the caller.
        raise HTTPException(status_code=503, detail="Staff access could not be checked.") from exc
    if not staff or not staff["is_active"]:
        raise HTTPException(status_code=403, detail="This account is not enabled for the staff workspace.")
    return dict(staff)


def require_roles(*roles: str):
    def dependency(staff: dict = Depends(require_staff_user)) -> dict:
        if staff["role"] not in roles:
            raise HTTPException(status_code=403, detail="Your staff role cannot perform this action.")
        return staff
    return dependency
