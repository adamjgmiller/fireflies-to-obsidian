#!/bin/bash
# Startup script for Fireflies to Obsidian sync service

# Function to log with timestamp
log_with_timestamp() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Check if LaunchAgent background service is running (skip check if called with --launch-agent flag)
SERVICE_NAME="com.fireflies.obsidian.sync"
if [[ "$1" != "--launch-agent" ]] && launchctl list | grep -q "$SERVICE_NAME"; then
    echo ""
    echo "⚠️  WARNING: macOS LaunchAgent background service is already running!"
    echo "   This script will create a separate process that may conflict with the background service."
    echo ""
    echo "   To manage the background service instead, use:"
    echo "   ./restart_service.sh    # Restart the background service"
    echo "   launchctl list | grep fireflies    # Check service status" 
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled. Use ./restart_service.sh to manage the background service."
        exit 0
    fi
    echo "Proceeding with direct execution..."
    echo ""
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to project directory
cd "$SCRIPT_DIR"

log_with_timestamp "Starting Fireflies to Obsidian sync service initialization"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    log_with_timestamp "ERROR: Virtual environment not found. Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment
log_with_timestamp "Activating virtual environment..."
source venv/bin/activate

# Check if required dependencies are installed
if ! python -c "import httpx" 2>/dev/null; then
    log_with_timestamp "Dependencies not installed. Installing from requirements.txt..."
    pip install -r requirements.txt
fi

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    log_with_timestamp "ERROR: config.yaml not found. Please create it from config.yaml.example"
    exit 1
fi

# Run the sync service
log_with_timestamp "Starting Fireflies to Obsidian sync service..."
log_with_timestamp "Press Ctrl+C to stop"
echo ""

# Pass arguments to the Python script (excluding --launch-agent flag)
if [[ "$1" == "--launch-agent" ]]; then
    shift  # Remove --launch-agent from arguments
fi
python -m src.main "$@"