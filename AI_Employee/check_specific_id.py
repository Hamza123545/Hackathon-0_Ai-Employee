"""
Check Specific Facebook/Instagram ID

Tests what a specific ID represents in the Facebook Graph API.
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


def check_id(test_id):
    """Check what a specific ID represents."""
    print("=" * 60)
    print(f"Checking ID: {test_id}")
    print("=" * 60)
    print()

    # Get access token
    page_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN', '')

    if not page_token:
        print("❌ FACEBOOK_PAGE_ACCESS_TOKEN not configured")
        return False

    print(f"✅ Access Token: {page_token[:20]}...")
    print()

    try:
        # Try to get basic info about this ID
        print("Fetching object information...")
        url = f"https://graph.facebook.com/v18.0/{test_id}"
        params = {
            'fields': 'id,name',
            'access_token': page_token
        }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            print()
            print("=" * 60)
            print("✅ Object Found!")
            print("=" * 60)
            print(f"ID: {data.get('id', 'N/A')}")
            print(f"Name: {data.get('name', 'N/A')}")
            print()

            # Try to get Instagram-specific fields
            print("Checking if this is an Instagram account...")
            ig_url = f"https://graph.facebook.com/v18.0/{test_id}"
            ig_params = {
                'fields': 'id,username,name,followers_count,follows_count,media_count',
                'access_token': page_token
            }

            ig_response = requests.get(ig_url, params=ig_params)

            if ig_response.status_code == 200:
                ig_data = ig_response.json()
                print()
                print("Instagram Account Details:")
                print(f"  Username: @{ig_data.get('username', 'N/A')}")
                print(f"  Name: {ig_data.get('name', 'N/A')}")
                print(f"  Followers: {ig_data.get('followers_count', 'N/A')}")
                print(f"  Following: {ig_data.get('follows_count', 'N/A')}")
                print(f"  Posts: {ig_data.get('media_count', 'N/A')}")
                print()
                print(f"Add to .env:")
                print(f"INSTAGRAM_ACCOUNT_ID={test_id}")
                print()
                return True
            else:
                print(f"Not an Instagram account or missing permissions")
                print(f"Response: {ig_response.text[:200]}")

            # Check if it has Instagram linked
            print("Checking if this is a Page with Instagram linked...")
            ig_check_url = f"https://graph.facebook.com/v18.0/{test_id}"
            ig_check_params = {
                'fields': 'instagram_business_account',
                'access_token': page_token
            }

            ig_check_response = requests.get(ig_check_url, params=ig_check_params)

            if ig_check_response.status_code == 200:
                ig_check_data = ig_check_response.json()
                if 'instagram_business_account' in ig_check_data:
                    instagram_id = ig_check_data['instagram_business_account']['id']
                    print(f"✅ Instagram Account Linked: {instagram_id}")
                    print()
                    print(f"Update .env with:")
                    print(f"FACEBOOK_PAGE_ID={test_id}")
                    print(f"INSTAGRAM_ACCOUNT_ID={instagram_id}")
                    print()
                    return True
                else:
                    print("❌ No Instagram account linked to this Page")
            else:
                print(f"Could not check for Instagram: {ig_check_response.text[:100]}")

            return True

        else:
            print()
            print("=" * 60)
            print(f"❌ Error: {response.status_code}")
            print("=" * 60)
            print(f"Response: {response.text}")
            print()
            return False

    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import sys

    # Get ID from command line or use default
    test_id = sys.argv[1] if len(sys.argv) > 1 else "61586572020009"

    result = check_id(test_id)
    sys.exit(0 if result else 1)
