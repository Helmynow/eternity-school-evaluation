#!/bin/bash
# Run Supabase database migrations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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

# Verify this is a Supabase project (expects ./supabase/config.toml)
if [ ! -f "supabase/config.toml" ]; then
    echo "❌ supabase/config.toml not found!"
    echo "Run this script from the Eternity School Evaluation project root."
    exit 1
fi

PROJECT_REF="${SUPABASE_PROJECT_REF:-ywcfqlyhesnikclesgpr}"

# Link (CLI v2 stores linked ref in supabase/.temp/project-ref).
LINKED=false
if [ -f "supabase/.temp/project-ref" ]; then
  LINKED=true
elif [ -f ".supabase/config.toml" ]; then
  LINKED=true
fi

if [ "$LINKED" != "true" ]; then
    echo "⚠️  Project not linked"
    echo "Linking to project: ${PROJECT_REF}"
    supabase link --project-ref "${PROJECT_REF}"
fi

# Push migrations
echo "Pushing migrations to Supabase..."
supabase db push --yes

echo ""
echo "✅ Migrations completed successfully!"
echo ""
echo "Verify in Supabase Dashboard:"
echo "  https://supabase.com/dashboard/project/${PROJECT_REF}"
