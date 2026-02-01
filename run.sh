#!/bin/bash
# STT Bot Runner for Linux

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

# Check venv
if [ ! -d ".venv" ]; then
    echo -e "${RED}ERROR: Virtual environment not found!${NC}"
    echo ""
    echo "Run ./install.sh first"
    exit 1
fi

# Check .env
if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo ""
    echo "Create .env from .env.example and set TELEGRAM_BOT_TOKEN"
    cp .env.example .env
    echo ""
    echo ".env created. Open it and set your token."
    exit 1
fi

# Activate venv
source .venv/bin/activate

echo -e "${CYAN}========================================"
echo -e "  Starting STT Bot"
echo -e "========================================${CYAN}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run bot
python -m bot.main
