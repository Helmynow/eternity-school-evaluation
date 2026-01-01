"""
Vercel serverless function entry point for FastAPI
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.fastapi_app import app

# Export app for Vercel
handler = app
