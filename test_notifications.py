#!/usr/bin/env python3
"""
Test script for macOS notifications with better debugging
"""
import subprocess
import sys
import platform

def test_basic_notification():
    """Test basic AppleScript notification"""
    print("Testing basic AppleScript notification...")
    try:
        script = '''
        display notification "🔔 Test notification from Python!" ¬
            with title "Fireflies Test" ¬
            subtitle "Direct AppleScript call"
        '''
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_with_delay():
    """Test notification with a delay to see if timing matters"""
    print("\nTesting with 3-second delay...")
    try:
        script = '''
        delay 3
        display notification "🕐 Delayed notification!" ¬
            with title "Fireflies Delayed Test" ¬
            sound name "Glass"
        '''
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=15
        )
        print(f"Return code: {result.returncode}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Exception: {e}")
        return False

def check_notification_settings():
    """Check notification-related settings"""
    print("\nChecking system info...")
    print(f"Platform: {platform.system()} {platform.release()}")
    
    # Check if we can access notification center
    try:
        result = subprocess.run(
            ['osascript', '-e', 'tell application "NotificationCenter" to activate'],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"NotificationCenter accessible: {result.returncode == 0}")
    except:
        print("NotificationCenter not accessible")

def main():
    print("🔔 macOS Notification Test Script")
    print("=" * 40)
    
    if platform.system() != 'Darwin':
        print("❌ This script only works on macOS")
        return
    
    check_notification_settings()
    
    print("\n1. Testing basic notification...")
    success1 = test_basic_notification()
    
    print("\n2. Testing delayed notification...")
    success2 = test_with_delay()
    
    print("\n" + "=" * 40)
    print("📊 Results:")
    print(f"Basic notification: {'✅ Success' if success1 else '❌ Failed'}")
    print(f"Delayed notification: {'✅ Success' if success2 else '❌ Failed'}")
    
    if not (success1 or success2):
        print("\n🚨 No notifications worked! Possible issues:")
        print("1. Check System Settings > Notifications & Focus")
        print("2. Look for 'Terminal' or 'Python' in the app list")
        print("3. Make sure 'Allow Notifications' is enabled")
        print("4. Check if Do Not Disturb is enabled")
        print("5. Try running this script from different terminals (Terminal.app vs iTerm)")
    else:
        print("\n✅ At least one notification method worked!")

if __name__ == "__main__":
    main() 