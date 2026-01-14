"""
Debug Facebook Access Token and Check Configuration

Inspects the access token to understand what it represents.
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


def debug_token():
    """Debug the access token to see what it represents."""
    print("=" * 60)
    print("Facebook Access Token Debug")
    print("=" * 60)
    print()

    # Get credentials
    app_id = os.getenv('FACEBOOK_APP_ID', '')
    page_id = os.getenv('FACEBOOK_PAGE_ID', '')
    page_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN', '')

    if not page_token:
        print("❌ FACEBOOK_PAGE_ACCESS_TOKEN not configured")
        return False

    print(f"✅ App ID: {app_id}")
    print(f"✅ Page ID: {page_id}")
    print(f"✅ Access Token: {page_token[:20]}...")
    print()

    try:
        # Method 1: Check what "me" represents with this token
        print("Method 1: Checking what 'me' represents...")
        me_url = "https://graph.facebook.com/v24.0/me"
        me_params = {
            'fields': 'id,name',
            'access_token': page_token
        }

        me_response = requests.get(me_url, params=me_params)

        if me_response.status_code == 200:
            me_data = me_response.json()
            print(f"  Token represents: {me_data.get('name', 'N/A')}")
            print(f"  ID: {me_data.get('id', 'N/A')}")
            print()
        else:
            print(f"  Error: {me_response.text}")
            print()

        # Method 2: Try to get Instagram account from the configured Page ID
        if page_id:
            print(f"Method 2: Checking Page ID {page_id} for Instagram...")

            # First, check what type of object this ID is
            type_url = f"https://graph.facebook.com/v24.0/{page_id}"
            type_params = {
                'fields': 'id,name',
                'access_token': page_token
            }

            type_response = requests.get(type_url, params=type_params)

            if type_response.status_code == 200:
                type_data = type_response.json()
                print(f"  Object Name: {type_data.get('name', 'N/A')}")
                print(f"  Object ID: {type_data.get('id', 'N/A')}")

                # Try to get Instagram account
                ig_url = f"https://graph.facebook.com/v24.0/{page_id}"
                ig_params = {
                    'fields': 'instagram_business_account',
                    'access_token': page_token
                }

                ig_response = requests.get(ig_url, params=ig_params)

                if ig_response.status_code == 200:
                    ig_data = ig_response.json()
                    if 'instagram_business_account' in ig_data:
                        instagram_id = ig_data['instagram_business_account']['id']
                        print(f"  ✅ Instagram Account Found: {instagram_id}")

                        # Get Instagram details
                        ig_detail_url = f"https://graph.facebook.com/v24.0/{instagram_id}"
                        ig_detail_params = {
                            'fields': 'id,username,name,followers_count,media_count',
                            'access_token': page_token
                        }

                        ig_detail_response = requests.get(ig_detail_url, params=ig_detail_params)

                        if ig_detail_response.status_code == 200:
                            ig_detail = ig_detail_response.json()
                            print()
                            print("=" * 60)
                            print("✅ Instagram Business Account Details")
                            print("=" * 60)
                            print(f"Instagram ID: {ig_detail.get('id', 'N/A')}")
                            print(f"Username: @{ig_detail.get('username', 'N/A')}")
                            print(f"Name: {ig_detail.get('name', 'N/A')}")
                            print(f"Followers: {ig_detail.get('followers_count', 'N/A')}")
                            print(f"Posts: {ig_detail.get('media_count', 'N/A')}")
                            print()
                            print(f"Add to .env:")
                            print(f"INSTAGRAM_ACCOUNT_ID={instagram_id}")
                            print()
                            return True
                        else:
                            print(f"  Could not get Instagram details: {ig_detail_response.text}")
                    else:
                        print(f"  ❌ No Instagram Account linked to this Page")
                        print()
                        print("  To link Instagram:")
                        print("  1. Make sure you have an Instagram Business Account")
                        print("  2. Go to Instagram Settings → Account → Linked Accounts")
                        print("  3. Link to your Facebook Page")
                else:
                    print(f"  Error checking Instagram: {ig_response.text}")
            else:
                print(f"  Error: {type_response.text}")

        print()
        return False

    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    result = debug_token()
    sys.exit(0 if result else 1)
