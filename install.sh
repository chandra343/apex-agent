#!/usr/bin/env bash
# ==============================================================================
# Project Apex: Universal POSIX One-Command Installer
# Supports: Ubuntu, Debian, Arch Linux, Fedora, CentOS, macOS
# ==============================================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BLUE}${BOLD}====================================================${NC}"
echo -e "${BLUE}${BOLD}      PROJECT APEX: SOVEREIGN HYBRID AI AGENT       ${NC}"
echo -e "${BLUE}${BOLD}====================================================${NC}"
echo -e "${GREEN}Starting installation...${NC}\n"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 1. Detect Python
PYTHON_BIN=""
for cmd in python3.14 python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON_BIN="$cmd"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo -e "${RED}Error: Python >= 3.10 is required but was not found in PATH.${NC}"
    exit 1
fi

echo -e "Using Python: ${BOLD}$("$PYTHON_BIN" --version)${NC} ($PYTHON_BIN)"

# 2. Virtual Environment Setup
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "Creating Python virtual environment in ${BOLD}$VENV_DIR${NC}..."
    "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo -e "Upgrading pip & installing dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install -e "$SCRIPT_DIR" --quiet

# 3. Create global binary wrapper
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
WRAPPER="$BIN_DIR/apex"

cat << 'EOF' > "$WRAPPER"
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Resolve actual project directory
PROJECT_ROOT="__PROJECT_ROOT__"
exec "$PROJECT_ROOT/.venv/bin/python3" -m apex.gateways.cli "$@"
EOF

# Replace placeholder with actual directory
sed -i "s|__PROJECT_ROOT__|$SCRIPT_DIR|g" "$WRAPPER" 2>/dev/null || sed -i '' "s|__PROJECT_ROOT__|$SCRIPT_DIR|g" "$WRAPPER"
chmod +x "$WRAPPER"

# 4. PATH Check
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${YELLOW}Warning: $BIN_DIR is not in your current PATH.${NC}"
    echo -e "Add this line to your ~/.bashrc or ~/.zshrc:"
    echo -e "  ${BOLD}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
fi

# 5. Create default configuration template if not exists
CONFIG_DIR="$HOME/.apex"
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/apex.json" ] && [ -f "$SCRIPT_DIR/apex.json.example" ]; then
    cp "$SCRIPT_DIR/apex.json.example" "$CONFIG_DIR/apex.json"
    echo -e "Created default configuration template in ${BOLD}$CONFIG_DIR/apex.json${NC}"
fi

echo -e "\n${GREEN}${BOLD}✔ Installation Successful!${NC}"
echo -e "You can now run:"
echo -e "  ${BOLD}apex setup${NC}        -> Run the 6-stage interactive setup wizard"
echo -e "  ${BOLD}apex${NC}              -> Launch Pi-style interactive terminal TUI"
echo -e "  ${BOLD}apex gateway start${NC}-> Launch the 24/7 background messaging daemon"
