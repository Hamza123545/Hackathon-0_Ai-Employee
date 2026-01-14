"""
LinkedIn OAuth 2.0 Authentication Script

Authenticates with LinkedIn using OAuth 2.0 and tests the connection.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import webbrowser
from urllib.parse import urlencode
import secrets

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


def test_linkedin_auth():
    """Test LinkedIn OAuth 2.0 authentication."""
    print("=" * 60)
    print("LinkedIn OAuth 2.0 Authentication")
    print("=" * 60)
    print()

    # Get credentials
    client_id = os.getenv('LINKEDIN_CLIENT_ID', '')
    client_secret = os.getenv('LINKEDIN_CLIENT_SECRET', '')
    redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:8080/linkedin/callback')

    if not client_id or not client_secret:
        print("❌ LinkedIn credentials not configured")
        return False

    print(f"✅ Client ID: {client_id}")
    print(f"✅ Client Secret: {'*' * 20}...")
    print(f"✅ Redirect URI: {redirect_uri}")
    print()

    try:
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(16)

        # Required scopes
        scopes = [
            "openid",
            "profile",
            "email",
            "w_member_social"  # For posting on behalf of user
        ]

        # Build authorization URL
        auth_params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(scopes),
            'state': state
        }

        authorization_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(auth_params)}"

        print()
        print("=" * 60)
        print("LinkedIn Authorization Required")
        print("=" * 60)
        print()
        print("Opening browser for LinkedIn authorization...")
        print()
        print("If browser doesn't open, manually visit this URL:")
        print(authorization_url)
        print()

        # Open browser
        webbrowser.open(authorization_url)

        print("After authorizing:")
        print("1. You'll be redirected to a URL like:")
        print("   http://localhost:8080/linkedin/callback?code=...&state=...")
        print()
        print("2. Copy the ENTIRE redirect URL from your browser")
        print()

        # Get the redirect response from user
        redirect_response = input("Paste the redirect URL here: ").strip()

        if not redirect_response:
            print("❌ No redirect URL provided")
            return False

        # Extract authorization code
        if "code=" not in redirect_response:
            print("❌ Invalid redirect URL - no authorization code found")
            return False

        auth_code = redirect_response.split("code=")[1].split("&")[0]

        print()
        print("Exchanging authorization code for access token...")

        # Exchange code for token
        import requests

        token_response = requests.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': redirect_uri,
                'client_id': client_id,
                'client_secret': client_secret
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        if token_response.status_code != 200:
            print(f"❌ Token exchange failed: {token_response.status_code}")
            print(f"Response: {token_response.text}")
            return False

        token_data = token_response.json()

        print()
        print("=" * 60)
        print("✅ Authentication Successful!")
        print("=" * 60)
        print()
        print(f"Access Token: {token_data['access_token'][:30]}...")
        print(f"Expires In: {token_data.get('expires_in', 'N/A')} seconds")
        print()

        # Test the connection - Get user profile
        print("Testing LinkedIn API connection...")

        profile_response = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={
                'Authorization': f"Bearer {token_data['access_token']}",
                'Content-Type': 'application/json'
            }
        )

        if profile_response.status_code != 200:
            print(f"❌ Failed to get profile: {profile_response.status_code}")
            print(f"Response: {profile_response.text}")
            return False

        profile = profile_response.json()

        print()
        print("=" * 60)
        print("✅ Connected to LinkedIn API!")
        print("=" * 60)
        print()
        print(f"Name: {profile.get('name', 'N/A')}")
        print(f"Email: {profile.get('email', 'N/A')}")
        print(f"Sub (User ID): {profile.get('sub', 'N/A')}")
        print()
        print("💾 Save this access token to your .env file:")
        print(f"LINKEDIN_ACCESS_TOKEN={token_data['access_token']}")
        print()
        print("Note: LinkedIn access tokens expire. You may need to refresh them periodically.")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_linkedin_auth()
    sys.exit(0 if success else 1)
