#!/bin/bash
###############################################################################
# Orion Arbitrage Engine - Startup Script
#
# This script starts both the arbitrage engine and the Streamlit dashboard.
# After initial setup, users can simply run this script to start everything.
###############################################################################

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "=========================================================================="
echo "  💰 ORION ARBITRAGE ENGINE - STARTUP"
echo "=========================================================================="
echo -e "${NC}"

# Change to project directory
cd "$PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}ERROR: Virtual environment not found!${NC}"
    echo "Please run the initial setup first (see SETUP_FOR_DUMMIES.md)"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo "Please complete the initial setup first (see SETUP_FOR_DUMMIES.md)"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Create logs directory if it doesn't exist
mkdir -p logs

# Check configuration
if [ ! -f "config/config.yaml" ]; then
    echo -e "${RED}ERROR: Configuration file not found!${NC}"
    echo "Expected: config/config.yaml"
    exit 1
fi

# Display current configuration
echo -e "${BLUE}Checking configuration...${NC}"
AUTO_EXECUTE=$(grep "auto_execute:" config/config.yaml | awk '{print $2}')

if [ "$AUTO_EXECUTE" == "true" ]; then
    echo -e "${RED}"
    echo "=========================================================================="
    echo "  ⚠️  WARNING: AUTO-EXECUTE IS ENABLED!"
    echo "  This will execute REAL TRADES with REAL MONEY!"
    echo "=========================================================================="
    echo -e "${NC}"
    echo "Press Ctrl+C in the next 5 seconds to cancel..."
    sleep 5
else
    echo -e "${GREEN}Mode: Alert-Only (auto_execute: false)${NC}"
    echo "The engine will detect opportunities but NOT execute trades."
fi

# Create PID file directory
mkdir -p "$PROJECT_DIR/tmp"
PID_FILE="$PROJECT_DIR/tmp/orion.pid"
DASHBOARD_PID_FILE="$PROJECT_DIR/tmp/dashboard.pid"

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}Orion engine is already running (PID: $OLD_PID)${NC}"
        echo "To stop it first, run: ./scripts/stop_orion.sh"
        exit 1
    else
        # Stale PID file, remove it
        rm "$PID_FILE"
    fi
fi

echo ""
echo -e "${GREEN}Starting Orion Arbitrage Engine...${NC}"

# Start the arbitrage engine in the background
nohup python main.py > logs/engine_console.log 2>&1 &
ENGINE_PID=$!
echo $ENGINE_PID > "$PID_FILE"

echo -e "${GREEN}✓ Engine started (PID: $ENGINE_PID)${NC}"
echo "  Logs: logs/arbitrage.log"
echo "  Console output: logs/engine_console.log"

# Wait a moment for engine to initialize
sleep 2

# Start the Streamlit dashboard in the background
echo ""
echo -e "${GREEN}Starting Streamlit Dashboard...${NC}"

nohup streamlit run dashboard.py --server.headless true --server.port 8501 > logs/dashboard_console.log 2>&1 &
DASHBOARD_PID=$!
echo $DASHBOARD_PID > "$DASHBOARD_PID_FILE"

echo -e "${GREEN}✓ Dashboard started (PID: $DASHBOARD_PID)${NC}"
echo "  Access at: http://localhost:8501"
echo "  Console output: logs/dashboard_console.log"

# Wait for dashboard to start
echo ""
echo -e "${YELLOW}Waiting for dashboard to start...${NC}"
sleep 5

# Try to open the dashboard in the default browser
if command -v open > /dev/null 2>&1; then
    echo -e "${GREEN}Opening dashboard in your browser...${NC}"
    open http://localhost:8501
fi

echo ""
echo -e "${GREEN}"
echo "=========================================================================="
echo "  ✓ ORION IS NOW RUNNING!"
echo "=========================================================================="
echo -e "${NC}"
echo "  Engine PID:    $ENGINE_PID"
echo "  Dashboard PID: $DASHBOARD_PID"
echo ""
echo "  Dashboard:     http://localhost:8501"
echo ""
echo "  To view logs:"
echo "    Engine:      tail -f logs/arbitrage.log"
echo "    Dashboard:   tail -f logs/dashboard_console.log"
echo ""
echo "  To stop everything:"
echo "    Run: ./scripts/stop_orion.sh"
echo "    Or double-click: Stop Orion.command (on your Desktop)"
echo ""
echo -e "${YELLOW}  Keep this window open or minimize it. Do NOT close it.${NC}"
echo "=========================================================================="
echo ""

# Keep script running to show it's active (optional)
# This allows users to press Ctrl+C to stop everything
trap "echo ''; echo 'Stopping Orion...'; ./scripts/stop_orion.sh; exit 0" INT TERM

# Wait indefinitely (script stays alive)
echo "Press Ctrl+C to stop Orion..."
wait
