#!/bin/bash
# Setup script for Eternity School Evaluation System

# Set database URL
export DATABASE_URL="postgresql://postgres:oRyY5M5S5op6ARqi@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres"

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
echo "  python backend/app.py"
echo ""
echo "Or use the run script: ./run.sh"

