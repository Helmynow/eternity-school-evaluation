#!/bin/bash
# Run script for Eternity School Evaluation System

# Set database URL
export DATABASE_URL="postgresql://postgres:oRyY5M5S5op6ARqi@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres"

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run ./setup_db.sh first"
    exit 1
fi

source venv/bin/activate

# Run the Flask app
cd backend
python app.py

