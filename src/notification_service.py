"""macOS notification service for meeting sync alerts."""
import subprocess
import platform
from typing import Dict, Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class NotificationService:
    """Handle macOS notifications for synced meetings."""
    
    def __init__(self, enabled: bool = True):
        """
        Initialize notification service.
        
        Args:
            enabled: Whether notifications are enabled
        """
        self.enabled = enabled and platform.system() == 'Darwin'
        if not self.enabled and platform.system() != 'Darwin':
            logger.info("Notifications disabled: not running on macOS")
    
    def send_notification(self, title: str, message: str, subtitle: Optional[str] = None) -> bool:
        """
        Send a macOS notification using osascript.
        
        Args:
            title: Notification title
            message: Main notification message
            subtitle: Optional subtitle
            
        Returns:
            True if notification sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            # Build AppleScript command
            script_parts = [
                'display notification',
                f'"{message}"',
                f'with title "{title}"'
            ]
            
            if subtitle:
                script_parts.append(f'subtitle "{subtitle}"')
            
            script = ' '.join(script_parts)
            
            # Execute AppleScript
            subprocess.run(
                ['osascript', '-e', script],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.debug(f"Notification sent: {title}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to send notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {e}")
            return False
    
    def notify_meeting_synced(self, meeting: Dict) -> bool:
        """
        Send notification for a synced meeting.
        
        Args:
            meeting: Meeting data dictionary
            
        Returns:
            True if notification sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            # Extract meeting details
            title = meeting.get('title', 'Untitled Meeting')
            meeting_date = meeting.get('date', '')
            host = meeting.get('host_name', 'Unknown Host')
            
            # Build notification
            notification_title = "Meeting Synced to Obsidian"
            message = f"{title}"
            subtitle = f"Host: {host}"
            
            if meeting_date:
                subtitle += f" • {meeting_date}"
            
            return self.send_notification(notification_title, message, subtitle)
            
        except Exception as e:
            logger.error(f"Error creating meeting notification: {e}")
            return False
    
    def notify_sync_summary(self, processed_count: int, error_count: int = 0) -> bool:
        """
        Send summary notification after sync batch.
        
        Args:
            processed_count: Number of meetings successfully processed
            error_count: Number of meetings that failed
            
        Returns:
            True if notification sent successfully
        """
        if not self.enabled or (processed_count == 0 and error_count == 0):
            return False
        
        title = "Fireflies Sync Complete"
        
        if processed_count > 0 and error_count == 0:
            message = f"{processed_count} meeting{'s' if processed_count > 1 else ''} synced"
        elif processed_count == 0 and error_count > 0:
            message = f"{error_count} meeting{'s' if error_count > 1 else ''} failed to sync"
        else:
            message = f"{processed_count} synced, {error_count} failed"
        
        return self.send_notification(title, message)
    
    def notify_error(self, error_message: str) -> bool:
        """
        Send error notification.
        
        Args:
            error_message: Error description
            
        Returns:
            True if notification sent successfully
        """
        if not self.enabled:
            return False
        
        return self.send_notification(
            "Fireflies Sync Error",
            error_message,
            "Check logs for details"
        )


# Singleton instance
_notification_service: Optional[NotificationService] = None


def get_notification_service(enabled: bool = True) -> NotificationService:
    """
    Get or create the notification service singleton.
    
    Args:
        enabled: Whether notifications should be enabled
        
    Returns:
        NotificationService instance
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService(enabled)
    return _notification_service