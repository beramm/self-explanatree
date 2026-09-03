#!/bin/bash
# Installation script for supervisor configuration files
# This script will update paths and install supervisor configs

set -e  # Exit on error

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the absolute path of this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
SUPERVISOR_CONF_DIR="/etc/supervisor/conf.d"

echo -e "${YELLOW}AI-Pohon Supervisor Installation Script${NC}"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: This script must be run as root${NC}"
    echo "Please run: sudo $0"
    exit 1
fi

# Check if supervisor is installed
if ! command -v supervisorctl &> /dev/null; then
    echo -e "${RED}Error: Supervisor is not installed${NC}"
    echo "Please install it first: sudo apt-get install supervisor"
    exit 1
fi

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_PYTHON${NC}"
    echo "Please create the virtual environment first"
    exit 1
fi

echo -e "${GREEN}Creating supervisor configuration files...${NC}"

# Create client.conf
cat > "$PROJECT_DIR/sup-client.conf.tmp" << EOF
[program:ai-pohon-client]
command=$VENV_PYTHON -u $PROJECT_DIR/client-silero.py
directory=$PROJECT_DIR
autostart=true
autorestart=true
stderr_logfile=/var/log/ai-pohon-client.err.log
stdout_logfile=/var/log/ai-pohon-client.out.log
stdout_logfile_maxbytes=0
stderr_logfile_maxbytes=0
environment=PYTHONUNBUFFERED=1
user=pi
EOF

# Create bt-control.conf
cat > "$PROJECT_DIR/sup-bt-control.conf.tmp" << EOF
[program:ai-pohon-bt-control]
command=$VENV_PYTHON -u $PROJECT_DIR/bt-control.py
directory=$PROJECT_DIR
autostart=true
autorestart=true
stderr_logfile=/var/log/ai-pohon-bt-control.err.log
stdout_logfile=/var/log/ai-pohon-bt-control.out.log
stdout_logfile_maxbytes=0
stderr_logfile_maxbytes=0
environment=PYTHONUNBUFFERED=1
user=pi
EOF

echo -e "${GREEN}Copying configuration files to $SUPERVISOR_CONF_DIR...${NC}"

# Copy the config files
cp "$PROJECT_DIR/sup-client.conf.tmp" "$SUPERVISOR_CONF_DIR/ai-pohon-client.conf"
cp "$PROJECT_DIR/sup-bt-control.conf.tmp" "$SUPERVISOR_CONF_DIR/ai-pohon-bt-control.conf"

# Clean up temporary files
rm "$PROJECT_DIR/sup-client.conf.tmp"
rm "$PROJECT_DIR/sup-bt-control.conf.tmp"

echo -e "${GREEN}Updating supervisor...${NC}"

# Reread and update supervisor
supervisorctl reread
supervisorctl update

echo ""
echo -e "${GREEN}Installation completed successfully!${NC}"
echo ""
echo "Available commands:"
echo "  sudo supervisorctl status                    - Check status"
echo "  sudo supervisorctl start ai-pohon-client     - Start client"
echo "  sudo supervisorctl start ai-pohon-bt-control - Start bluetooth control"
echo "  sudo supervisorctl stop ai-pohon-client      - Stop client"
echo "  sudo supervisorctl stop ai-pohon-bt-control  - Stop bluetooth control"
echo "  sudo supervisorctl restart ai-pohon-client   - Restart client"
echo "  sudo supervisorctl tail -f ai-pohon-client   - View logs"
echo ""
