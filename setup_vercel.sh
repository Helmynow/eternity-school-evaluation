#!/bin/bash
# Setup script for Vercel deployment with Supabase

set -e

echo "============================================================================"
echo "Vercel + Supabase Setup Script"
echo "============================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cat > .env << 'EOF'
# Database Configuration
# Get from Supabase Dashboard → Project Settings → Database
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.ywcfqlyhesnikclesgpr.supabase.co:5432/postgres

# Email Configuration (Resend SMTP)
SMTP_SERVER=smtp.resend.com
SMTP_PORT=465
SMTP_USER=resend
SMTP_PASSWORD=re_6dFf5Vue_73jUTecAhnqZaonoGEPaGax2
FROM_EMAIL=noreply@eternityschoolegypt.com
EMAIL_ENABLED=true

# Supabase Configuration
SUPABASE_URL=https://ywcfqlyhesnikclesgpr.supabase.co
SUPABASE_ANON_KEY=[YOUR-SUPABASE-ANON-KEY]
SUPABASE_SERVICE_ROLE_KEY=[YOUR-SUPABASE-SERVICE-ROLE-KEY]

# Application Configuration
ENVIRONMENT=production
ENABLE_DOCS=false

# Optional
SENTRY_DSN=
REQUIRE_API_KEY=false
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
EOF
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo -e "${YELLOW}⚠️  Please update .env with your actual credentials!${NC}"
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo -e "${YELLOW}Supabase CLI not found. Installing...${NC}"
    echo "Choose installation method:"
    echo "1. npm (recommended): npm install -g supabase"
    echo "2. Homebrew (macOS): brew install supabase/tap/supabase"
    echo ""
    read -p "Press Enter after installing Supabase CLI, or Ctrl+C to skip..."
fi

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}Vercel CLI not found. Installing...${NC}"
    npm install -g vercel
    echo -e "${GREEN}✅ Vercel CLI installed${NC}"
fi

echo ""
echo "============================================================================"
echo "Setup Complete!"
echo "============================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Update .env file with your credentials:"
echo "   - DATABASE_URL (from Supabase Dashboard)"
echo "   - SUPABASE_ANON_KEY (from Supabase Dashboard)"
echo "   - SUPABASE_SERVICE_ROLE_KEY (from Supabase Dashboard)"
echo ""
echo "2. Run database migrations:"
echo "   supabase link --project-ref ywcfqlyhesnikclesgpr"
echo "   supabase db push"
echo ""
echo "3. Deploy to Vercel:"
echo "   vercel login"
echo "   vercel --prod"
echo ""
echo "4. Set environment variables in Vercel Dashboard:"
echo "   - Go to your project → Settings → Environment Variables"
echo "   - Add all variables from .env file"
echo ""
echo "For detailed instructions, see VERCEL_DEPLOYMENT.md"
echo ""
