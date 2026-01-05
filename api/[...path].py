"""Vercel Serverless entrypoint.

This catch-all function ensures requests like `/api/v2/...` are handled by the FastAPI app.

Vercel file-system routing:
- `api/[...path].py` matches `/api/*`
"""

from backend.fastapi_app import app  # noqa: F401
