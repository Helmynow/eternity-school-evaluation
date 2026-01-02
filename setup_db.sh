#!/bin/bash
# Setup script for Eternity School Evaluation System

# Set database URL from environment variable or .env file
# IMPORTANT: Never commit database credentials to version control
# Set DATABASE_URL in your .env file or export it before running this script
if [ -z "$DATABASE_URL" ]; then
    if [ -f .env ]; then
        # Load DATABASE_URL from .env file
        export $(grep -v '^#' .env | grep DATABASE_URL | xargs)
    fi
    
    if [ -z "$DATABASE_URL" ]; then
        echo "❌ ERROR: DATABASE_URL not set!"
        echo ""
        echo "Please set DATABASE_URL in one of these ways:"
        echo "  1. Export it: export DATABASE_URL='postgresql://user:pass@host:port/db'"
        echo "  2. Add it to .env file: DATABASE_URL='postgresql://user:pass@host:port/db'"
        echo "  3. Use Supabase connection string from your project settings"
        echo ""
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create tables
echo "Creating database tables..."
python3 -c "from backend.database import Database; db = Database(); db.create_tables(); print('Tables created successfully!')"

echo ""
echo "Setup complete!"
echo ""
echo "To activate the virtual environment and run the server:"
echo "  source venv/bin/activate"
echo "  uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "Or use the run script: ./run.sh"
