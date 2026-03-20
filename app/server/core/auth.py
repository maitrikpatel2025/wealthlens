"""
Supabase auth verification for WealthLens API.
Verifies tokens via Supabase Auth API (no JWT secret needed).
"""

import os
from typing import Optional

import httpx
from fastapi import Request, HTTPException


SUPABASE_URL = os.getenv("SUPABASE_URL", "") or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")


async def verify_supabase_token(request: Request) -> Optional[str]:
    """Verify access token by calling Supabase Auth API.

    Returns the user UUID if valid, None if no auth header present.
    Raises HTTPException 401 if token is present but invalid.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    supabase_url = SUPABASE_URL or os.getenv("SUPABASE_URL", "")
    if not supabase_url:
        return None

    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{supabase_url}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": os.getenv("SUPABASE_ANON_KEY", "") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", ""),
                },
            )

        if res.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_data = res.json()
        return user_data.get("id")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token verification failed")


async def require_auth(request: Request) -> str:
    """FastAPI dependency: requires valid Supabase auth. Returns user UUID."""
    user_id = await verify_supabase_token(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id
