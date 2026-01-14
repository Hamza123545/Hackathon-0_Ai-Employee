"""
Simple Facebook API Connection Test

Tests Facebook Graph API connection using credentials from .env file.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


def test_facebook_connection():
    """Test Facebook Graph API connection."""
    print("=" * 60)
    print("Facebook API Connection Test")
    print("=" * 60)
    print()

    # Get credentials from environment
    app_id = os.getenv('FACEBOOK_APP_ID', '')
    app_secret = os.getenv('FACEBOOK_APP_SECRET', '')
    page_id = os.getenv('FACEBOOK_PAGE_ID', '')
    page_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN', '')

    # Check credentials
    if not app_id or not app_secret:
        print("❌ Facebook App ID or Secret not configured")
        return False

    print(f"✅ Facebook App ID: {app_id[:8]}...")
    print(f"✅ Facebook App Secret: {'*' * 8}...")

    if not page_id:
        print("❌ Facebook Page ID not configured")
        return False

    print(f"✅ Facebook Page ID: {page_id}")

    if not page_token:
        print("❌ Facebook Page Access Token not configured")
        return False

    print(f"✅ Facebook Page Access Token: {page_token[:20]}...")
    print()

    # Test API connection
    try:
        from facebook import GraphAPI

        print("Testing Facebook Graph API connection...")
        graph = GraphAPI(access_token=page_token, version="3.1")

        # Get page details
        page_info = graph.get_object(
            id=page_id,
            fields="id,name,username,fan_count,about"
        )

        print()
        print("=" * 60)
        print("✅ SUCCESS! Connected to Facebook Graph API")
        print("=" * 60)
        print()
        print(f"Page Name: {page_info.get('name', 'N/A')}")
        print(f"Username: @{page_info.get('username', 'N/A')}")
        print(f"Followers: {page_info.get('fan_count', 'N/A')}")
        print(f"About: {page_info.get('about', 'N/A')[:50]}..." if page_info.get('about') else "About: N/A")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ FAILED: {e}")
        print("=" * 60)
        return False


if __name__ == '__main__':
    success = test_facebook_connection()
    sys.exit(0 if success else 1)
