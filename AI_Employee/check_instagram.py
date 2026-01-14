"""
Check Instagram Business Account Configuration

Checks if Facebook Page has a linked Instagram Business Account.
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


def check_instagram_account():
    """Check if Instagram Business Account is linked to Facebook Page."""
    print("=" * 60)
    print("Instagram Business Account Check")
    print("=" * 60)
    print()

    # Get credentials from environment
    page_id = os.getenv('FACEBOOK_PAGE_ID', '')
    page_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN', '')

    if not page_id or not page_token:
        print("❌ Facebook credentials not configured")
        return False

    print(f"✅ Facebook Page ID: {page_id}")
    print()

    try:
        print("Checking for linked Instagram Business Account...")

        # Query Facebook Page for Instagram Business Account
        url = f"https://graph.facebook.com/v18.0/{page_id}"
        params = {
            'fields': 'instagram_business_account',
            'access_token': page_token
        }

        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        data = response.json()

        if 'instagram_business_account' in data:
            instagram_account_id = data['instagram_business_account']['id']

            print()
            print("=" * 60)
            print("✅ Instagram Business Account Found!")
            print("=" * 60)
            print()
            print(f"Instagram Account ID: {instagram_account_id}")
            print()

            # Get Instagram account details
            print("Fetching Instagram account details...")
            ig_url = f"https://graph.facebook.com/v18.0/{instagram_account_id}"
            ig_params = {
                'fields': 'id,username,name,profile_picture_url,followers_count,follows_count,media_count',
                'access_token': page_token
            }

            ig_response = requests.get(ig_url, params=ig_params)

            if ig_response.status_code == 200:
                ig_data = ig_response.json()
                print()
                print(f"Username: @{ig_data.get('username', 'N/A')}")
                print(f"Name: {ig_data.get('name', 'N/A')}")
                print(f"Followers: {ig_data.get('followers_count', 'N/A')}")
                print(f"Following: {ig_data.get('follows_count', 'N/A')}")
                print(f"Posts: {ig_data.get('media_count', 'N/A')}")
                print()
                print("✅ Instagram API is ready to use!")
                print()
                print(f"Add this to your .env file:")
                print(f"INSTAGRAM_ACCOUNT_ID={instagram_account_id}")
                print()
                return instagram_account_id
            else:
                print(f"⚠️  Could not fetch Instagram details: {ig_response.text}")
                return instagram_account_id

        else:
            print()
            print("=" * 60)
            print("❌ No Instagram Business Account Linked")
            print("=" * 60)
            print()
            print("To link an Instagram Business Account:")
            print("1. Convert your Instagram to a Business Account")
            print("2. Go to Instagram Settings → Account → Linked Accounts")
            print("3. Link to your Facebook Page: Hamza Swati")
            print()
            return False

    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    result = check_instagram_account()
    sys.exit(0 if result else 1)
