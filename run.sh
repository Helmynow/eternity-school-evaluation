#!/bin/bash
# Run FastAPI server for Eternity School Evaluation System

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run ./setup_db.sh first"
    exit 1
fi

source venv/bin/activate

# Run FastAPI with uvicorn
uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000 --reload
