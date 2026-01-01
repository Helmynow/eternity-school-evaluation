#!/bin/bash
# Run Supabase database migrations

set -e

echo "============================================================================"
echo "Running Supabase Database Migrations"
echo "============================================================================"
echo ""

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found!"
    echo ""
    echo "Install it with:"
    echo "  npm install -g supabase"
    echo "  or"
    echo "  brew install supabase/tap/supabase"
    exit 1
fi

# Check if logged in
if ! supabase projects list &> /dev/null; then
    echo "⚠️  Not logged in to Supabase"
    echo "Running: supabase login"
    supabase login
fi

# Check if project is linked
if [ ! -f ".supabase/config.toml" ]; then
    echo "⚠️  Project not linked"
    echo "Linking to project: ywcfqlyhesnikclesgpr"
    supabase link --project-ref ywcfqlyhesnikclesgpr
fi

# Push migrations
echo "Pushing migrations to Supabase..."
cd supabase
supabase db push

echo ""
echo "✅ Migrations completed successfully!"
echo ""
echo "Verify in Supabase Dashboard:"
echo "  https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr"
