"""Shared rate limiter instance.

Imported by routers that need per-IP rate limiting.
Uses in-memory storage (suitable for single-process dev/demo deployment).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
