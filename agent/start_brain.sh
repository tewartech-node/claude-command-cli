#!/bin/bash

# Start The Brain: Your Autonomous AI
# Usage: ./agent/start_brain.sh <gmail_password> [optional: monthly_budget]

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧠 Starting The Brain${NC}"
echo ""

# Check for gmail password
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: Gmail app password required${NC}"
    echo "Usage: ./agent/start_brain.sh '<your-app-password>' [monthly_budget]"
    echo ""
    echo "How to get Gmail app password:"
    echo "  1. Go to: https://myaccount.google.com/security"
    echo "  2. Enable 2-Step Verification"
    echo "  3. Go to App Passwords"
    echo "  4. Select: Mail + Windows Computer"
    echo "  5. Copy the 16-character password"
    echo ""
    exit 1
fi

GMAIL_PASSWORD="$1"
MONTHLY_BUDGET="${2:-0.0}"

echo -e "${GREEN}✅ Configuration:${NC}"
echo "   Gmail: warnet.dev01@gmail.com"
echo "   Password: ****** (hidden)"
echo "   Monthly Budget: \$$MONTHLY_BUDGET"
echo "   CLI Path: ./cli/go/bin/claude"
echo ""

# Check if CLI exists
if [ ! -f "./cli/go/bin/claude" ]; then
    echo -e "${RED}⚠️  Warning: CLI not found at ./cli/go/bin/claude${NC}"
    echo "   Building CLI..."
    cd cli/go
    go build -o bin/claude ./cmd/claude
    cd ../..
    echo -e "${GREEN}✅ CLI built${NC}"
fi

# Set environment variables
export GMAIL_PASSWORD="$GMAIL_PASSWORD"
export MONTHLY_BUDGET="$MONTHLY_BUDGET"
export CLI_PATH="./cli/go/bin/claude"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All checks passed${NC}"
echo ""
echo -e "${BLUE}🚀 Launching Brain...${NC}"
echo ""

# Run the agent as a module
cd "$(dirname "$0")/.."
python3 -m agent.core.agent
