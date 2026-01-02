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
echo "  → Pushing all migrations to remote database..."
echo "  (This will apply all pending migrations from the migrations/ folder)"
echo ""

# Use supabase db push to apply all migrations
# This command automatically detects and applies pending migrations
supabase db push --yes || {
    echo ""
    echo "  ⚠️  Migration push failed or migrations already applied"
    echo "  If tables already exist, you may need to:"
    echo "    1. Drop existing tables manually, OR"
    echo "    2. Mark migrations as applied: supabase migration repair"
    echo ""
}

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
echo "Database Connection:"
echo "  Get your database URL from Supabase Dashboard:"
echo "  Project Settings → Database → Connection string"
echo ""
echo "  Then set it in your .env file:"
echo "  DATABASE_URL='postgresql://postgres:[YOUR-PASSWORD]@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres'"
echo ""
echo "  ⚠️  SECURITY: Never commit database credentials to version control!"
echo ""

