"""
LinkedIn OAuth Token Exchange

Exchanges authorization code for access token.
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


def exchange_code_for_token(auth_code):
    """Exchange authorization code for access token."""
    print("=" * 60)
    print("LinkedIn Token Exchange")
    print("=" * 60)
    print()

    # Get credentials
    client_id = os.getenv('LINKEDIN_CLIENT_ID', '')
    client_secret = os.getenv('LINKEDIN_CLIENT_SECRET', '')
    redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI', 'http://localhost:8080/linkedin/callback')

    print(f"✅ Client ID: {client_id}")
    print(f"✅ Authorization Code: {auth_code[:30]}...")
    print()

    try:
        print("Exchanging authorization code for access token...")

        # Exchange code for token
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

        # Update .env file
        print("Updating .env file with access token...")

        env_file = Path(__file__).parent / '.env'
        with open(env_file, 'r', encoding='utf-8') as f:
            env_content = f.read()

        # Add or update LINKEDIN_ACCESS_TOKEN
        if 'LINKEDIN_ACCESS_TOKEN=' in env_content:
            # Replace existing token
            lines = env_content.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith('LINKEDIN_ACCESS_TOKEN='):
                    new_lines.append(f"LINKEDIN_ACCESS_TOKEN={token_data['access_token']}")
                else:
                    new_lines.append(line)
            env_content = '\n'.join(new_lines)
        else:
            # Add new token after LINKEDIN_REDIRECT_URI
            lines = env_content.split('\n')
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if line.startswith('LINKEDIN_REDIRECT_URI='):
                    new_lines.append(f"LINKEDIN_ACCESS_TOKEN={token_data['access_token']}")
            env_content = '\n'.join(new_lines)

        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)

        print()
        print("=" * 60)
        print("✅ LinkedIn Setup Complete!")
        print("=" * 60)
        print()
        print("LinkedIn is now fully configured and ready to use!")
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
    # Extract code from command line argument
    if len(sys.argv) < 2:
        print("Usage: python linkedin_token_exchange.py <authorization_code>")
        sys.exit(1)

    auth_code = sys.argv[1]
    success = exchange_code_for_token(auth_code)
    sys.exit(0 if success else 1)
