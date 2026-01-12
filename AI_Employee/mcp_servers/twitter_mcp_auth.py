"""
Twitter OAuth 2.0 PKCE Authentication Setup (Gold Tier)

Handles OAuth 2.0 PKCE (Proof Key for Code Exchange) flow for Twitter API v2 integration.
Stores tokens securely in OS credential manager using keyring.
"""

import json
import os
import webbrowser
from typing import Optional

import keyring
import tweepy

# Keyring service name
KEYRING_SERVICE = "twitter-mcp"


class TwitterAuthManager:
    """Manages Twitter OAuth 2.0 PKCE authentication and token storage."""
    
    def __init__(
        self,
        client_id: str,
        redirect_uri: str = "http://localhost:8000/oauth/twitter/callback",
        client_secret: Optional[str] = None
    ):
        """
        Initialize Twitter Auth Manager.
        
        Args:
            client_id: Twitter application client ID
            redirect_uri: OAuth redirect URI (must match Twitter app settings)
            client_secret: Optional client secret (for confidential clients)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.oauth_handler = tweepy.OAuth2UserHandler(
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=["tweet.read", "tweet.write", "users.read", "offline.access"],
            client_secret=client_secret
        )
    
    def get_authorization_url(self) -> str:
        """
        Get authorization URL for OAuth PKCE flow.
        
        Returns:
            Authorization URL string
        """
        return self.oauth_handler.get_authorization_url()
    
    def fetch_token(self, authorization_response: str) -> dict:
        """
        Exchange authorization code for access token.
        
        Args:
            authorization_response: Full redirect URL with authorization code
        
        Returns:
            Token dictionary with access_token, refresh_token, expires_in, etc.
        """
        # Extract code from callback URL
        from urllib.parse import parse_qs, urlparse
        parsed = urlparse(authorization_response)
        params = parse_qs(parsed.query)
        code = params.get('code', [None])[0]
        
        if not code:
            raise ValueError("Authorization code not found in callback URL")
        
        # Fetch token
        token = self.oauth_handler.fetch_token(code=code)
        
        # Store token in keyring
        self._store_token(token)
        
        return token
    
    def refresh_token(self) -> dict:
        """
        Refresh access token using refresh token.
        
        Returns:
            New token dictionary
        """
        token_data = self._get_token()
        if not token_data or 'refresh_token' not in token_data:
            raise ValueError("No refresh token available. Re-authentication required.")
        
        # Refresh token (tweepy handles this automatically)
        # Note: Refresh token rotates on each refresh
        new_token = self.oauth_handler.refresh_token(
            refresh_token=token_data['refresh_token']
        )
        
        # Store updated token
        self._store_token(new_token)
        
        return new_token
    
    def get_access_token(self) -> Optional[str]:
        """
        Get current access token from keyring.
        
        Returns:
            Access token string or None if not found
        """
        token_data = self._get_token()
        if token_data:
            return token_data.get('access_token')
        return None
    
    def get_client(self) -> tweepy.Client:
        """
        Get tweepy Client instance with current access token.
        
        Returns:
            tweepy.Client instance
        """
        access_token = self.get_access_token()
        if not access_token:
            raise RuntimeError("Not authenticated with Twitter. Run auth setup first.")
        
        return tweepy.Client(access_token=access_token)
    
    def _store_token(self, token: dict) -> None:
        """Store token in OS credential manager."""
        try:
            token_json = json.dumps(token)
            keyring.set_password(KEYRING_SERVICE, "oauth_token", token_json)
        except Exception as e:
            raise RuntimeError(f"Failed to store token in keyring: {e}")
    
    def _get_token(self) -> Optional[dict]:
        """Retrieve token from OS credential manager."""
        try:
            token_json = keyring.get_password(KEYRING_SERVICE, "oauth_token")
            if token_json:
                return json.loads(token_json)
        except Exception as e:
            print(f"Warning: Failed to retrieve token from keyring: {e}")
        return None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (has valid token)."""
        return self.get_access_token() is not None
    
    def revoke_token(self) -> None:
        """Revoke and delete stored token."""
        try:
            keyring.delete_password(KEYRING_SERVICE, "oauth_token")
        except keyring.errors.PasswordDeleteError:
            pass


def setup_twitter_oauth(
    client_id: Optional[str] = None,
    redirect_uri: str = "http://localhost:8000/oauth/twitter/callback",
    client_secret: Optional[str] = None
) -> TwitterAuthManager:
    """
    Interactive OAuth setup for Twitter.
    
    Args:
        client_id: Twitter client ID (from env or user input)
        redirect_uri: OAuth redirect URI
        client_secret: Optional client secret (for confidential clients)
    
    Returns:
        TwitterAuthManager instance with authenticated token
    """
    # Get credentials from environment or prompt
    if not client_id:
        client_id = os.getenv('TWITTER_CLIENT_ID', '')
        if not client_id:
            client_id = input("Enter Twitter Client ID: ").strip()
    
    if not client_secret:
        client_secret = os.getenv('TWITTER_CLIENT_SECRET', '')
        if not client_secret:
            # Client secret is optional for public clients
            client_secret_input = input("Enter Twitter Client Secret (optional, press Enter to skip): ").strip()
            client_secret = client_secret_input if client_secret_input else None
    
    auth_manager = TwitterAuthManager(client_id, redirect_uri, client_secret)
    
    # Check if already authenticated
    if auth_manager.is_authenticated():
        print("✅ Already authenticated with Twitter")
        return auth_manager
    
    # Start OAuth flow
    print("Starting Twitter OAuth 2.0 PKCE flow...")
    authorization_url = auth_manager.get_authorization_url()
    
    print(f"\nPlease visit this URL to authorize:\n{authorization_url}\n")
    print("Opening browser...")
    webbrowser.open(authorization_url)
    
    # Get callback URL from user
    callback_url = input(
        "\nAfter authorizing, paste the full callback URL here: "
    ).strip()
    
    # Exchange code for token
    token = auth_manager.fetch_token(callback_url)
    
    print("✅ Successfully authenticated with Twitter!")
    print(f"Token expires in: {token.get('expires_in', 'unknown')} seconds")
    if 'refresh_token' in token:
        print("✅ Refresh token obtained (valid for 6 months)")
    
    return auth_manager


if __name__ == '__main__':
    """Run OAuth setup interactively."""
    setup_twitter_oauth()

