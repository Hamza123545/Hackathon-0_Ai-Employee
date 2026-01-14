"""
Simple Facebook Graph API Test using requests library

Tests Facebook Graph API connection using credentials from .env file.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


def test_facebook_api():
    """Test Facebook Graph API using requests."""
    print("=" * 60)
    print("Facebook Graph API Connection Test")
    print("=" * 60)
    print()

    # Get credentials from environment
    page_id = os.getenv('FACEBOOK_PAGE_ID', '')
    page_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN', '')

    if not page_id:
        print("❌ FACEBOOK_PAGE_ID not configured in .env")
        return False

    if not page_token:
        print("❌ FACEBOOK_PAGE_ACCESS_TOKEN not configured in .env")
        return False

    print(f"✅ Page ID: {page_id}")
    print(f"✅ Access Token: {page_token[:20]}...")
    print()

    # Test API connection
    try:
        print("Connecting to Facebook Graph API...")

        # Make API request to get basic info (works for all node types)
        url = f"https://graph.facebook.com/v24.0/{page_id}"
        params = {
            'fields': 'id,name',
            'access_token': page_token
        }

        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        page_info = response.json()

        print()
        print("=" * 60)
        print("✅ SUCCESS! Connected to Facebook Graph API")
        print("=" * 60)
        print()
        print(f"Page ID: {page_info.get('id', 'N/A')}")
        print(f"Page Name: {page_info.get('name', 'N/A')}")
        print(f"Category: {page_info.get('category', 'N/A')}")
        print(f"Followers: {page_info.get('fan_count', 'N/A')}")

        if page_info.get('about'):
            about = page_info['about']
            print(f"About: {about[:80]}..." if len(about) > 80 else f"About: {about}")

        print()
        print("✅ Facebook API is ready to use!")
        print()

        return True

    except requests.exceptions.RequestException as e:
        print()
        print("=" * 60)
        print(f"❌ Connection Error: {e}")
        print("=" * 60)
        return False
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Error: {e}")
        print("=" * 60)
        return False


if __name__ == '__main__':
    success = test_facebook_api()
    sys.exit(0 if success else 1)
