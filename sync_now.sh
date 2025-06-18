#!/bin/bash

# Fireflies to Obsidian - Manual Sync Trigger
# Sends SIGUSR1 signal to the running service to trigger immediate sync

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# LaunchAgent label
SERVICE_LABEL="com.fireflies.obsidian.sync"

# Function to print status messages
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if service is running
echo "Checking service status..."
SERVICE_INFO=$(launchctl list | grep "$SERVICE_LABEL")

if [ -z "$SERVICE_INFO" ]; then
    print_error "Service is not running!"
    echo "Start the service with: ./manage_service.sh start"
    exit 1
fi

# Extract PID from launchctl output (first column)
PID=$(echo "$SERVICE_INFO" | awk '{print $1}')

if [ "$PID" = "-" ]; then
    print_error "Service is registered but not running!"
    echo "The service may have crashed. Try restarting with: ./manage_service.sh restart"
    exit 1
fi

# Check if PID is valid
if ! ps -p "$PID" > /dev/null 2>&1; then
    print_error "Service PID $PID is not valid!"
    echo "Try restarting the service: ./manage_service.sh restart"
    exit 1
fi

# Check if a sync might already be in progress
# Look for recent sync log entries (within last 10 seconds)
LOG_FILE="logs/fireflies_sync.log"
if [ -f "$LOG_FILE" ]; then
    RECENT_SYNC=$(tail -n 20 "$LOG_FILE" | grep -E "Processing.*meetings|Successfully processed meeting" | tail -1)
    if [ -n "$RECENT_SYNC" ]; then
        # Extract timestamp and check if recent
        TIMESTAMP=$(echo "$RECENT_SYNC" | awk '{print $1 " " $2}')
        if [ -n "$TIMESTAMP" ]; then
            # Convert to seconds since epoch
            if command -v gdate > /dev/null 2>&1; then
                # GNU date (from coreutils)
                LOG_TIME=$(gdate -d "$TIMESTAMP" +%s 2>/dev/null)
                CURRENT_TIME=$(gdate +%s)
            else
                # macOS date
                LOG_TIME=$(date -j -f "%Y-%m-%d %H:%M:%S" "$TIMESTAMP" +%s 2>/dev/null)
                CURRENT_TIME=$(date +%s)
            fi
            
            if [ -n "$LOG_TIME" ] && [ -n "$CURRENT_TIME" ]; then
                TIME_DIFF=$((CURRENT_TIME - LOG_TIME))
                if [ "$TIME_DIFF" -lt 10 ]; then
                    print_warning "A sync appears to be in progress (last activity ${TIME_DIFF}s ago)"
                    echo "Sending signal anyway..."
                fi
            fi
        fi
    fi
fi

# Send SIGUSR1 signal
print_status "Sending sync signal to PID $PID..."
if kill -USR1 "$PID" 2>/dev/null; then
    print_status "Signal sent successfully!"
    echo ""
    echo "The service will process meetings immediately."
    echo "Check the logs for sync progress:"
    echo "  tail -f logs/fireflies_sync.log"
else
    print_error "Failed to send signal to PID $PID"
    echo "You may need to run this script with appropriate permissions."
    exit 1
fi