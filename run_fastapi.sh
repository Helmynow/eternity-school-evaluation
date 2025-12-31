#!/bin/bash
# Run FastAPI server for Eternity School Evaluation System

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run FastAPI with uvicorn
uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000 --reload

