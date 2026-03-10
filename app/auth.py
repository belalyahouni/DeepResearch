"""API key authentication dependency.

Protects all endpoints (except /health and /docs) with a simple API key
sent via the X-API-Key header. The valid key is read from the API_KEY
environment variable.
"""

import os
import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str:
    """Validate the API key from the X-API-Key header.

    Raises 401 if the key is missing or invalid.
    Uses timing-safe comparison to prevent timing attacks.
    """
    expected = os.getenv("API_KEY")
    if not expected:
        raise HTTPException(
            status_code=500,
            detail="API_KEY not configured on the server",
        )

    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="Missing API key — include an X-API-Key header",
        )

    if not secrets.compare_digest(api_key, expected):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return api_key
