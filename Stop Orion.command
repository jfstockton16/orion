#!/bin/bash
###############################################################################
# Orion Arbitrage Engine - Stop Launcher
#
# Double-click this file to stop Orion!
###############################################################################

# Determine the actual project directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project directory
cd "$SCRIPT_DIR"

# Run the stop script
./scripts/stop_orion.sh

# Keep the Terminal window open so user can see the result
echo ""
echo "Press any key to close this window..."
read -n 1
