#!/bin/bash
# Termux Initialization Script
# Place in ~/.bashrc or ~/.profile to auto-run on shell start

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Only run once per session
if [ -z "$BRAIN_INIT_DONE" ]; then
    export BRAIN_INIT_DONE=1

    # Show welcome screen if we're in the repo directory
    if [ -f "agent/startup/welcome.sh" ]; then
        bash agent/startup/welcome.sh
    fi
fi
