#!/bin/bash
# STT Bot Portable Installer for Linux
# Requires: bash, python3 or python3.10/3.11

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================"
echo -e "  Installation STT Bot (Portable)"
echo -e "========================================${NC}"
echo ""

# Detect OS
OS="$(uname -s)"
ARCH="$(uname -m)"

echo -e "${CYAN}[Info]${NC} OS: $OS, Architecture: $ARCH"
echo ""

# Function to get Python version
test_python_version() {
    local python_cmd=$1
    if $python_cmd --version >/dev/null 2>&1; then
        local ver=$($python_cmd --version 2>&1 | grep -oP '\d+\.\d+')
        local major=$(echo $ver | cut -d. -f1)
        local minor=$(echo $ver | cut -d. -f2)
        if [ "$major" -eq 3 ] && { [ "$minor" -eq 10 ] || [ "$minor" -eq 11 ]; }; then
            echo "$python_cmd|$ver"
            return 0
        fi
    fi
    return 1
}

# Function to find compatible Python
find_compatible_python() {
    # Try python3.10, python3.11, python3
    for py in python3.10 python3.11 python3; do
        if command -v $py >/dev/null 2>&1; then
            local result=$(test_python_version $py)
            if [ $? -eq 0 ]; then
                local cmd=$(echo $result | cut -d| -f1)
                local ver=$(echo $result | cut -d| -f2)
                echo -e "${GREEN}Found compatible Python: $ver ($cmd)${NC}"
                echo "$cmd"
                return 0
            fi
        fi
    done

    # Check user-local installations
    for py_dir in "$HOME/.local/bin/python3.10" "$HOME/.local/bin/python3.11"; do
        if [ -f "$py_dir" ]; then
            local result=$(test_python_version $py_dir)
            if [ $? -eq 0 ]; then
                local ver=$(echo $result | cut -d| -f2)
                echo -e "${GREEN}Found compatible Python: $ver ($py_dir)${NC}"
                echo "$py_dir"
                return 0
            fi
        fi
    done

    return 1
}

# Step 1: Check Python
echo -e "${CYAN}[1/7] Checking Python...${NC}"

PYTHON_CMD=$(find_compatible_python)

if [ -z "$PYTHON_CMD" ]; then
    echo ""
    echo -e "${RED}========================================"
    echo -e "Compatible Python Not Found"
    echo -e "========================================${RED}"
    echo ""
    echo -e "${YELLOW}Required: Python 3.10.x or 3.11.x${NC}"
    echo ""
    echo "Install Python 3.10 using your package manager:"
    echo ""
    echo "  Ubuntu/Debian:"
    echo "    sudo apt update"
    echo "    sudo apt install -y software-properties-common"
    echo "    sudo add-apt-repository -y ppa:deadsnakes/ppa"
    echo "    sudo apt update"
    echo "    sudo apt install -y python3.10 python3.10-venv python3.10-dev"
    echo ""
    echo "  Fedora/RHEL/CentOS:"
    echo "    sudo dnf install python3.10"
    echo ""
    echo "  Arch Linux:"
    echo "    yay -S python310"
    echo ""
    read -p "Press Enter to exit"
    exit 1
fi

echo -e "${GREEN}Using: $PYTHON_CMD${NC}"
echo ""

# Step 2: Check FFmpeg
echo -e "${CYAN}[2/7] Checking FFmpeg...${NC}"

if command -v ffmpeg >/dev/null 2>&1; then
    echo -e "${GREEN}FFmpeg found: $(ffmpeg -version | head -1)${NC}"
else
    echo ""
    echo -e "${YELLOW}FFmpeg not found. Install using your package manager:${NC}"
    echo ""
    echo "  Ubuntu/Debian:"
    echo "    sudo apt install -y ffmpeg"
    echo ""
    echo "  Fedora/RHEL/CentOS:"
    echo "    sudo dnf install ffmpeg"
    echo ""
    echo "  Arch Linux:"
    echo "    sudo pacman -S ffmpeg"
    echo ""
    read -p "Press Enter to exit"
    exit 1
fi

echo ""

# Step 3: Create virtual environment
echo -e "${CYAN}[3/7] Creating virtual environment...${NC}"

if [ -d ".venv" ]; then
    echo "Virtual environment exists, recreating..."
    rm -rf .venv
fi

$PYTHON_CMD -m venv .venv

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Virtual environment created${NC}"
else
    echo -e "${RED}ERROR: Failed to create venv${NC}"
    exit 1
fi

echo ""

# Step 4: Activate virtual environment
echo -e "${CYAN}[4/7] Activating virtual environment...${NC}"

source .venv/bin/activate

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Virtual environment activated${NC}"
else
    echo -e "${RED}ERROR: Failed to activate venv${NC}"
    exit 1
fi

echo ""

# Step 5: Upgrade pip
echo -e "${CYAN}[5/7] Upgrading pip...${NC}"
python -m pip install --upgrade pip -q
echo -e "${GREEN}pip upgraded${NC}"
echo ""

# Step 6: Install dependencies
echo -e "${CYAN}[6/7] Installing dependencies...${NC}"
echo "This may take several minutes..."
echo ""

echo "- Installing PyTorch (~2GB)..."
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu -q

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to install PyTorch${NC}"
    exit 1
fi

echo "- Installing GigaAM and other dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to install dependencies${NC}"
    exit 1
fi

echo -e "${GREEN}Dependencies installed${NC}"
echo ""

# Step 7: Configuration
echo -e "${CYAN}[7/7] Configuration...${NC}"

mkdir -p logs temp

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}========================================"
    echo -e "Configuration Required"
    echo -e "========================================${YELLOW}"
    echo ""
    echo -e "${GREEN}Created .env from .env.example${NC}"
    echo ""
    echo "Open .env and set your TELEGRAM_BOT_TOKEN"
    echo "Get token from: @BotFather in Telegram"
    echo ""
fi

echo ""
echo -e "${GREEN}========================================"
echo -e "Installation Complete!"
echo -e "========================================${GREEN}"
echo ""
echo "To run the bot:"
echo "  1. Open .env and set TELEGRAM_BOT_TOKEN"
echo "  2. Run: ./run.sh"
echo ""
