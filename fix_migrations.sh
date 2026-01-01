#!/bin/bash
# Fix migration conflicts and apply pending migrations

set -e

echo "============================================================================"
echo "Fixing Migration Conflicts"
echo "============================================================================"
echo ""

# Repair remote migrations that aren't in local
echo "Repairing migration history..."
supabase migration repair --status reverted 20251231165827 2>/dev/null || true
supabase migration repair --status reverted 20251231172444 2>/dev/null || true
supabase migration repair --status reverted 20251231215926 2>/dev/null || true

echo ""
echo "Applying pending migrations..."
supabase db push

echo ""
echo "✅ Migrations complete!"
echo ""
echo "Verify in Supabase Dashboard:"
echo "  https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr"
