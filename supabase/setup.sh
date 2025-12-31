#!/bin/bash
# Supabase Setup Script for Eternity School Evaluation System

set -e

echo "============================================================================"
echo "SUPABASE BACKEND SETUP"
echo "============================================================================"
echo ""

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found!"
    echo ""
    echo "Please install Supabase CLI:"
    echo "  macOS: brew install supabase/tap/supabase"
    echo "  npm:   npm install -g supabase"
    echo ""
    exit 1
fi

echo "✓ Supabase CLI found"
echo ""

# Check if logged in
if ! supabase projects list &> /dev/null; then
    echo "⚠️  Not logged in to Supabase"
    echo "Please run: supabase login"
    echo ""
    read -p "Do you want to login now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        supabase login
    else
        echo "Exiting. Please login and run this script again."
        exit 1
    fi
fi

echo "✓ Logged in to Supabase"
echo ""

# Link to project
PROJECT_REF="ywcfqlyhesnikclesgpr"
echo "Linking to project: $PROJECT_REF"
supabase link --project-ref $PROJECT_REF || {
    echo "⚠️  Project already linked or link failed"
    echo "Continuing..."
}
echo ""

# Apply migrations
echo "Applying database migrations..."
echo ""

MIGRATION_FILES=(
    "migrations/20240101000000_initial_schema.sql"
    "migrations/20240101000001_create_views.sql"
    "migrations/20240101000002_create_functions.sql"
    "migrations/20240101000003_row_level_security.sql"
)

for migration in "${MIGRATION_FILES[@]}"; do
    if [ -f "$migration" ]; then
        echo "  → Applying $migration"
        supabase db push --file "$migration" || {
            echo "  ⚠️  Migration may have already been applied"
        }
    else
        echo "  ⚠️  Migration file not found: $migration"
    fi
done

echo ""
echo "============================================================================"
echo "SETUP COMPLETE!"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "  1. Open Supabase Studio: supabase studio"
echo "  2. Verify tables: Check that all tables are created"
echo "  3. (Optional) Seed data: Run seed.sql manually"
echo "  4. Test connection: Use your application"
echo ""
echo "Database URL:"
echo "  postgresql://postgres:oRyY5M5S5op6ARqi@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres"
echo ""

