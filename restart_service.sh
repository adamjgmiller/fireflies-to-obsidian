#!/bin/bash
# Restart script for Fireflies to Obsidian LaunchAgent service

PLIST_PATH="$HOME/Library/LaunchAgents/com.fireflies.obsidian.sync.plist"
SERVICE_NAME="com.fireflies.obsidian.sync"

# Function to log with timestamp
log_timestamp() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_timestamp "Restarting Fireflies to Obsidian background service..."

# Check if service is currently running
if launchctl list | grep -q "$SERVICE_NAME"; then
    log_timestamp "Stopping service..."
    launchctl unload "$PLIST_PATH"
    if [ $? -eq 0 ]; then
        log_timestamp "Service stopped successfully"
    else
        log_timestamp "ERROR: Failed to stop service"
        exit 1
    fi
else
    log_timestamp "Service is not currently running"
fi

# Start the service
log_timestamp "Starting service..."
launchctl load "$PLIST_PATH"
if [ $? -eq 0 ]; then
    log_timestamp "Service started successfully"
    
    # Wait a moment and check if it's running
    sleep 2
    if launchctl list | grep -q "$SERVICE_NAME"; then
        PID=$(launchctl list | grep "$SERVICE_NAME" | awk '{print $1}')
        log_timestamp "Service is running with PID: $PID"
    else
        log_timestamp "WARNING: Service may not have started properly"
    fi
else
    log_timestamp "ERROR: Failed to start service"
    exit 1
fi

log_timestamp "Restart complete"