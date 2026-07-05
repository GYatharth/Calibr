"""
Day 20: Rate limiting via slowapi.

Protects the API from abuse — especially important for endpoints
that call external APIs (Groq) or do heavy computation (embeddings).

Limits:
- POST /score: 10 requests/minute per IP (prevents scoring spam)
- POST /batch/score: 5 requests/minute per IP
- POST /auth/login: 10 requests/minute per IP (brute force prevention)
- General: 100 requests/minute per IP across all endpoints
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Limiter uses the client's IP address as the key
limiter = Limiter(key_func=get_remote_address)