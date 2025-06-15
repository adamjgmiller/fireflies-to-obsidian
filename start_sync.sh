#!/bin/bash
# Startup script for Fireflies to Obsidian sync service

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to project directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if required dependencies are installed
if ! python -c "import httpx" 2>/dev/null; then
    echo "Dependencies not installed. Installing from requirements.txt..."
    pip install -r requirements.txt
fi

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "Error: config.yaml not found. Please create it from config.yaml.example"
    exit 1
fi

# Run the sync service
echo "Starting Fireflies to Obsidian sync service..."
echo "Press Ctrl+C to stop"
echo ""

# Pass all arguments to the Python script
python -m src.main "$@"