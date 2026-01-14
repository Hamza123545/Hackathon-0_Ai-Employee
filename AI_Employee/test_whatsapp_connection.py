"""
Test WhatsApp Watcher

Quick test to verify WhatsApp session is working.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from watchers.whatsapp_watcher import WhatsAppWatcher
from utils.config import Config

def test_whatsapp():
    """Test WhatsApp watcher connection."""
    print("=" * 60)
    print("Testing WhatsApp Watcher")
    print("=" * 60)
    print()

    config = Config()

    try:
        # Create watcher in headless mode
        watcher = WhatsAppWatcher(config, headless=True)

        print("✅ WhatsApp watcher initialized")
        print(f"✅ Session file: {watcher.session_file}")
        print()

        # Test connection by checking for updates
        print("Checking for new messages...")
        messages = watcher.check_for_updates()

        print()
        print("=" * 60)
        print("✅ WhatsApp Connection Test Successful!")
        print("=" * 60)
        print()
        print(f"Found {len(messages)} unread message(s)")

        if messages:
            print()
            print("Recent messages:")
            for msg in messages[:3]:  # Show first 3
                print(f"  • {msg['contact_name']}: {msg['message_preview'][:50]}...")

        # Cleanup
        watcher.stop()

        return True

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Error: {e}")
        print("=" * 60)
        return False

if __name__ == '__main__':
    success = test_whatsapp()
    sys.exit(0 if success else 1)
