#!/bin/bash
###############################################################################
# Orion Arbitrage Engine - Stop Script
#
# This script cleanly stops both the arbitrage engine and dashboard.
###############################################################################

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
echo "  💰 ORION ARBITRAGE ENGINE - SHUTDOWN"
echo "=========================================================================="
echo -e "${NC}"

PID_FILE="$PROJECT_DIR/tmp/orion.pid"
DASHBOARD_PID_FILE="$PROJECT_DIR/tmp/dashboard.pid"

STOPPED_SOMETHING=false

# Stop the engine
if [ -f "$PID_FILE" ]; then
    ENGINE_PID=$(cat "$PID_FILE")

    if ps -p "$ENGINE_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping Orion Engine (PID: $ENGINE_PID)...${NC}"
        kill "$ENGINE_PID"

        # Wait up to 10 seconds for graceful shutdown
        for i in {1..10}; do
            if ! ps -p "$ENGINE_PID" > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if ps -p "$ENGINE_PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}Force stopping engine...${NC}"
            kill -9 "$ENGINE_PID" 2>/dev/null || true
        fi

        echo -e "${GREEN}✓ Engine stopped${NC}"
        STOPPED_SOMETHING=true
    else
        echo -e "${YELLOW}Engine not running (stale PID file)${NC}"
    fi

    rm "$PID_FILE"
else
    echo -e "${YELLOW}Engine PID file not found${NC}"
fi

# Stop the dashboard
if [ -f "$DASHBOARD_PID_FILE" ]; then
    DASHBOARD_PID=$(cat "$DASHBOARD_PID_FILE")

    if ps -p "$DASHBOARD_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping Dashboard (PID: $DASHBOARD_PID)...${NC}"
        kill "$DASHBOARD_PID"

        # Wait up to 5 seconds for graceful shutdown
        for i in {1..5}; do
            if ! ps -p "$DASHBOARD_PID" > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done

        # Force kill if still running
        if ps -p "$DASHBOARD_PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}Force stopping dashboard...${NC}"
            kill -9 "$DASHBOARD_PID" 2>/dev/null || true
        fi

        echo -e "${GREEN}✓ Dashboard stopped${NC}"
        STOPPED_SOMETHING=true
    else
        echo -e "${YELLOW}Dashboard not running (stale PID file)${NC}"
    fi

    rm "$DASHBOARD_PID_FILE"
else
    echo -e "${YELLOW}Dashboard PID file not found${NC}"
fi

# Also kill any remaining python processes that might be running
# (safety measure for any orphaned processes)
echo ""
echo -e "${YELLOW}Checking for any remaining Orion processes...${NC}"

# Kill main.py processes
pkill -f "python main.py" 2>/dev/null && echo -e "${GREEN}✓ Stopped orphaned engine processes${NC}" || true

# Kill streamlit dashboard processes
pkill -f "streamlit run dashboard.py" 2>/dev/null && echo -e "${GREEN}✓ Stopped orphaned dashboard processes${NC}" || true

echo ""
if [ "$STOPPED_SOMETHING" = true ]; then
    echo -e "${GREEN}"
    echo "=========================================================================="
    echo "  ✓ ORION HAS BEEN STOPPED"
    echo "=========================================================================="
    echo -e "${NC}"
else
    echo -e "${YELLOW}"
    echo "=========================================================================="
    echo "  Orion was not running"
    echo "=========================================================================="
    echo -e "${NC}"
fi

echo ""
echo "To start Orion again:"
echo "  Run: ./scripts/start_orion.sh"
echo "  Or double-click: Start Orion.command (on your Desktop)"
echo ""
