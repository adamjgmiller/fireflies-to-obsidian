#!/bin/bash
# Fireflies to Obsidian Sync Service Management Script

PLIST_NAME="com.fireflies.obsidian.sync"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$1" in
    start)
        echo "Starting Fireflies sync service..."
        launchctl load "$PLIST_PATH"
        echo "Service started. Check status with: $0 status"
        ;;
    stop)
        echo "Stopping Fireflies sync service..."
        launchctl unload "$PLIST_PATH"
        echo "Service stopped."
        ;;
    restart)
        echo "Restarting Fireflies sync service..."
        launchctl unload "$PLIST_PATH" 2>/dev/null
        sleep 2
        launchctl load "$PLIST_PATH"
        echo "Service restarted."
        ;;
    status)
        echo "Checking service status..."
        if launchctl list | grep -q "$PLIST_NAME"; then
            PID=$(launchctl list | grep "$PLIST_NAME" | awk '{print $1}')
            echo "✅ Service is running (PID: $PID)"
            echo ""
            echo "Recent logs:"
            echo "📄 Output log:"
            tail -5 "$PROJECT_DIR/logs/launch_agent.out.log" 2>/dev/null || echo "No output log found"
            echo ""
            echo "🔄 Main app log:"
            tail -5 "$PROJECT_DIR/logs/fireflies_sync.log" 2>/dev/null || echo "No main log found"
        else
            echo "❌ Service is not running"
        fi
        ;;
    logs)
        echo "Showing live logs (Ctrl+C to exit):"
        tail -f "$PROJECT_DIR/logs/fireflies_sync.log"
        ;;
    install)
        echo "Installing launch agent..."
        cp "$PROJECT_DIR/com.fireflies.obsidian.sync.plist" "$PLIST_PATH"
        echo "Launch agent installed. Use '$0 start' to start the service."
        ;;
    uninstall)
        echo "Uninstalling launch agent..."
        launchctl unload "$PLIST_PATH" 2>/dev/null
        rm -f "$PLIST_PATH"
        echo "Launch agent uninstalled."
        ;;
    test-notification)
        echo "Testing notifications..."
        cd "$PROJECT_DIR"
        source venv/bin/activate
        python -c "
from src.notification_service import NotificationService
notif = NotificationService(enabled=True)
result = notif.send_notification(
    'Fireflies Service Test', 
    'Your sync service is working! 🎉',
    'Auto-startup is configured'
)
print(f'✅ Test notification sent: {result}')
"
        ;;
    sync-now)
        echo "Triggering manual sync..."
        # First check if service is running
        if ! launchctl list | grep -q "$PLIST_NAME"; then
            echo "❌ Service is not running! Start it first with: $0 start"
            exit 1
        fi
        
        # Call the sync_now.sh script
        if [ -f "$PROJECT_DIR/sync_now.sh" ]; then
            "$PROJECT_DIR/sync_now.sh"
        else
            echo "❌ sync_now.sh script not found!"
            exit 1
        fi
        ;;
    *)
        echo "Fireflies to Obsidian Sync Service Manager"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|sync-now|install|uninstall|test-notification}"
        echo ""
        echo "Commands:"
        echo "  start              Start the sync service"
        echo "  stop               Stop the sync service"
        echo "  restart            Restart the sync service"
        echo "  status             Check if service is running"
        echo "  logs               Show live logs"
        echo "  sync-now           Trigger immediate sync (service must be running)"
        echo "  install            Install the launch agent"
        echo "  uninstall          Remove the launch agent"
        echo "  test-notification  Test the notification system"
        echo ""
        ;;
esac 