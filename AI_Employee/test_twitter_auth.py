"""
Simple Twitter OAuth 2.0 Authentication Test

Authenticates with Twitter using OAuth 2.0 PKCE flow and tests the connection.
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


def test_twitter_auth():
    """Test Twitter OAuth 2.0 authentication."""
    print("=" * 60)
    print("Twitter OAuth 2.0 Authentication Test")
    print("=" * 60)
    print()

    # Get credentials
    client_id = os.getenv('TWITTER_CLIENT_ID', '')
    client_secret = os.getenv('TWITTER_CLIENT_SECRET', '')
    redirect_uri = os.getenv('TWITTER_REDIRECT_URI', 'http://localhost:8000/oauth/twitter/callback')

    if not client_id or not client_secret:
        print("❌ Twitter credentials not configured")
        return False

    print(f"✅ Client ID: {client_id[:15]}...")
    print(f"✅ Client Secret: {'*' * 10}...")
    print(f"✅ Redirect URI: {redirect_uri}")
    print()

    try:
        import tweepy

        print("Initializing Twitter OAuth 2.0 handler...")

        # Create OAuth2UserHandler for user authentication
        oauth2_user_handler = tweepy.OAuth2UserHandler(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=["tweet.read", "tweet.write", "users.read", "offline.access"],
            client_secret=client_secret
        )

        # Get authorization URL
        auth_url = oauth2_user_handler.get_authorization_url()

        print()
        print("=" * 60)
        print("Twitter Authorization Required")
        print("=" * 60)
        print()
        print("Please follow these steps:")
        print()
        print("1. Open this URL in your browser:")
        print(f"   {auth_url}")
        print()
        print("2. Authorize the app")
        print()
        print("3. You'll be redirected to a URL like:")
        print("   http://localhost:8000/oauth/twitter/callback?state=...&code=...")
        print()
        print("4. Copy the ENTIRE redirect URL and paste it below")
        print()

        # Get the redirect response from user
        redirect_response = input("Paste the redirect URL here: ").strip()

        if not redirect_response:
            print("❌ No redirect URL provided")
            return False

        print()
        print("Exchanging authorization code for access token...")

        # Fetch the access token
        access_token = oauth2_user_handler.fetch_token(redirect_response)

        print()
        print("=" * 60)
        print("✅ Authentication Successful!")
        print("=" * 60)
        print()
        print(f"Access Token: {access_token.get('access_token', '')[:20]}...")
        print(f"Token Type: {access_token.get('token_type', 'N/A')}")
        print(f"Expires In: {access_token.get('expires_in', 'N/A')} seconds")
        print()

        # Test the connection
        print("Testing Twitter API connection...")
        client = tweepy.Client(
            bearer_token=access_token['access_token']
        )

        # Get authenticated user
        me = client.get_me(user_fields=["id", "name", "username", "public_metrics"])

        if me.data:
            user = me.data
            print()
            print("=" * 60)
            print("✅ Connected to Twitter API!")
            print("=" * 60)
            print()
            print(f"Username: @{user.username}")
            print(f"Name: {user.name}")
            print(f"User ID: {user.id}")

            if hasattr(user, 'public_metrics'):
                metrics = user.public_metrics
                print(f"Followers: {metrics.get('followers_count', 'N/A')}")
                print(f"Following: {metrics.get('following_count', 'N/A')}")
                print(f"Tweets: {metrics.get('tweet_count', 'N/A')}")

            print()
            print("💾 Save this access token to your .env file:")
            print(f"TWITTER_BEARER_TOKEN={access_token['access_token']}")
            print()

            return True
        else:
            print("❌ Failed to get user data")
            return False

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_twitter_auth()
    sys.exit(0 if success else 1)
