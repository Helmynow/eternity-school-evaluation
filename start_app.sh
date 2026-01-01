#!/bin/bash
# Start the FastAPI application

set -e

echo "============================================================================"
echo "Starting Eternity School Evaluation System"
echo "============================================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Please create .env file with required environment variables"
    echo "See VERCEL_DEPLOYMENT.md for details"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r backend/requirements.txt
fi

# Check DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  WARNING: DATABASE_URL not set in .env"
    echo "The application may not be able to connect to the database"
    echo ""
fi

# Start the application
echo ""
echo "Starting FastAPI server..."
echo "API will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd backend
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload
