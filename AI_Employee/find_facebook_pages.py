"""
Find Facebook Pages Associated with Access Token

Lists all Facebook Pages you manage to find the correct Page ID.
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


def find_facebook_pages():
    """Find all Facebook Pages associated with the access token."""
    print("=" * 60)
    print("Find Your Facebook Pages")
    print("=" * 60)
    print()

    # Get access token from environment
    page_token = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN', '')

    if not page_token:
        print("❌ FACEBOOK_PAGE_ACCESS_TOKEN not configured")
        return False

    print(f"✅ Access Token: {page_token[:20]}...")
    print()

    try:
        print("Fetching your Facebook Pages...")
        print()

        # Get pages managed by the user
        url = "https://graph.facebook.com/v18.0/me/accounts"
        params = {
            'access_token': page_token
        }

        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False

        data = response.json()

        if 'data' not in data or len(data['data']) == 0:
            print("=" * 60)
            print("❌ No Facebook Pages Found")
            print("=" * 60)
            print()
            print("You need to create a Facebook Page first:")
            print("1. Go to https://www.facebook.com/pages/create")
            print("2. Create a Business Page")
            print("3. Then link your Instagram Business Account to it")
            print()
            return False

        pages = data['data']

        print("=" * 60)
        print(f"✅ Found {len(pages)} Facebook Page(s)")
        print("=" * 60)
        print()

        for i, page in enumerate(pages, 1):
            page_id = page.get('id', 'N/A')
            page_name = page.get('name', 'N/A')
            page_access_token = page.get('access_token', 'N/A')

            print(f"Page {i}:")
            print(f"  Name: {page_name}")
            print(f"  ID: {page_id}")
            print(f"  Access Token: {page_access_token[:30]}...")
            print()

            # Check if this page has Instagram linked
            ig_url = f"https://graph.facebook.com/v18.0/{page_id}"
            ig_params = {
                'fields': 'instagram_business_account',
                'access_token': page_access_token
            }

            ig_response = requests.get(ig_url, params=ig_params)

            if ig_response.status_code == 200:
                ig_data = ig_response.json()
                if 'instagram_business_account' in ig_data:
                    instagram_id = ig_data['instagram_business_account']['id']
                    print(f"  ✅ Instagram Linked: {instagram_id}")

                    # Get Instagram details
                    ig_detail_url = f"https://graph.facebook.com/v18.0/{instagram_id}"
                    ig_detail_params = {
                        'fields': 'username,followers_count',
                        'access_token': page_access_token
                    }
                    ig_detail_response = requests.get(ig_detail_url, params=ig_detail_params)
                    if ig_detail_response.status_code == 200:
                        ig_detail = ig_detail_response.json()
                        print(f"     Username: @{ig_detail.get('username', 'N/A')}")
                        print(f"     Followers: {ig_detail.get('followers_count', 'N/A')}")
                else:
                    print(f"  ❌ No Instagram Account Linked")
            else:
                print(f"  ⚠️  Could not check Instagram: {ig_response.text[:50]}")

            print()

        print("=" * 60)
        print("Update your .env file with the correct Page ID and Token:")
        print("=" * 60)
        print()
        print("FACEBOOK_PAGE_ID=<page_id_from_above>")
        print("FACEBOOK_PAGE_ACCESS_TOKEN=<page_access_token_from_above>")
        print("INSTAGRAM_ACCOUNT_ID=<instagram_id_if_linked>")
        print()

        return True

    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    result = find_facebook_pages()
    sys.exit(0 if result else 1)
