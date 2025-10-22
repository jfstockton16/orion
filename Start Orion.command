#!/bin/bash
###############################################################################
# Orion Arbitrage Engine - Desktop Launcher
#
# Double-click this file to start Orion!
# (First time: you may need to right-click → Open to allow execution)
###############################################################################

# Determine the actual project directory
# This finds where the script is located (should be in ~/Desktop/orion/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project directory
cd "$SCRIPT_DIR"

# Run the startup script
./scripts/start_orion.sh

# Keep the Terminal window open after script ends
echo ""
echo "Press any key to close this window..."
read -n 1
