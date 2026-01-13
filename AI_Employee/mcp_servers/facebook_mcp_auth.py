"""
Facebook OAuth 2.0 Authentication Setup (Gold Tier)

Handles OAuth 2.0 authorization code flow for Facebook Pages API integration.
Stores tokens securely in OS credential manager using keyring.
"""

import json
import os
import webbrowser
from typing import Optional

import keyring
from facebook import GraphAPI

# Keyring service name
KEYRING_SERVICE = "facebook-mcp"


class FacebookAuthManager:
    """Manages Facebook OAuth 2.0 authentication and token storage."""
    
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        redirect_uri: str = "http://localhost:8000/oauth/facebook/callback"
    ):
        """
        Initialize Facebook Auth Manager.
        
        Args:
            app_id: Facebook application ID
            app_secret: Facebook application secret
            redirect_uri: OAuth redirect URI (must match Facebook app settings)
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.graph_api = GraphAPI(
            app_id=app_id,
            app_secret=app_secret,
            oauth_flow=True,
            redirect_uri=redirect_uri,
            scope=[
                "pages_show_list",
                "pages_read_engagement",
                "pages_manage_posts",
                "pages_read_user_content"
            ]
        )
    
    def get_authorization_url(self) -> tuple[str, str]:
        """
        Get authorization URL for OAuth flow.
        
        Returns:
            Tuple of (authorization_url, state)
        """
        return self.graph_api.get_authorization_url()
    
    def fetch_user_token(self, authorization_response: str) -> dict:
        """
        Exchange authorization code for user access token.
        
        Args:
            authorization_response: Full redirect URL with authorization code
        
        Returns:
            Token dictionary with access_token, expires_in, etc.
        """
        token_data = self.graph_api.exchange_user_access_token(
            response=authorization_response
        )
        
        # Exchange for long-lived user token (60 days)
        long_token = self.graph_api.exchange_long_lived_user_access_token(
            access_token=token_data['access_token']
        )
        
        # Store token in keyring
        self._store_token(long_token)
        
        return long_token
    
    def get_page_access_token(self, page_id: str) -> Optional[str]:
        """
        Exchange user token for page access token (never expires).
        
        Args:
            page_id: Facebook Page ID
        
        Returns:
            Page access token or None if not found
        """
        token_data = self._get_token()
        if not token_data:
            return None
        
        try:
            # Create GraphAPI with user token
            api = GraphAPI(
                app_id=self.app_id,
                app_secret=self.app_secret,
                access_token=token_data['access_token']
            )
            
            # Exchange for page token
            page_token = api.exchange_page_access_token(page_id=page_id)
            
            # Store page token
            page_tokens = self._get_page_tokens()
            page_tokens[page_id] = page_token
            self._store_page_tokens(page_tokens)
            
            return page_token
        except Exception as e:
            print(f"Error getting page access token: {e}")
            return None
    
    def get_access_token(self, page_id: Optional[str] = None) -> Optional[str]:
        """
        Get current access token from keyring.
        
        Args:
            page_id: If provided, return page access token; otherwise user token
        
        Returns:
            Access token string or None if not found
        """
        if page_id:
            page_tokens = self._get_page_tokens()
            return page_tokens.get(page_id)
        else:
            token_data = self._get_token()
            if token_data:
                return token_data.get('access_token')
            return None
    
    def _store_token(self, token: dict) -> None:
        """Store token in OS credential manager."""
        try:
            token_json = json.dumps(token)
            keyring.set_password(KEYRING_SERVICE, "user_token", token_json)
        except Exception as e:
            raise RuntimeError(f"Failed to store token in keyring: {e}")
    
    def _get_token(self) -> Optional[dict]:
        """Retrieve token from OS credential manager."""
        try:
            token_json = keyring.get_password(KEYRING_SERVICE, "user_token")
            if token_json:
                return json.loads(token_json)
        except Exception as e:
            print(f"Warning: Failed to retrieve token from keyring: {e}")
        return None
    
    def _store_page_tokens(self, page_tokens: dict[str, str]) -> None:
        """Store page tokens in keyring."""
        try:
            tokens_json = json.dumps(page_tokens)
            keyring.set_password(KEYRING_SERVICE, "page_tokens", tokens_json)
        except Exception as e:
            raise RuntimeError(f"Failed to store page tokens in keyring: {e}")
    
    def _get_page_tokens(self) -> dict[str, str]:
        """Retrieve page tokens from keyring."""
        try:
            tokens_json = keyring.get_password(KEYRING_SERVICE, "page_tokens")
            if tokens_json:
                return json.loads(tokens_json)
        except Exception:
            pass
        return {}
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (has valid token)."""
        return self.get_access_token() is not None
    
    def revoke_token(self) -> None:
        """Revoke and delete stored tokens."""
        try:
            keyring.delete_password(KEYRING_SERVICE, "user_token")
            keyring.delete_password(KEYRING_SERVICE, "page_tokens")
        except keyring.errors.PasswordDeleteError:
            pass


def setup_facebook_oauth(
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
    redirect_uri: str = "http://localhost:8000/oauth/facebook/callback"
) -> FacebookAuthManager:
    """
    Interactive OAuth setup for Facebook.
    
    Args:
        app_id: Facebook app ID (from env or user input)
        app_secret: Facebook app secret (from env or user input)
        redirect_uri: OAuth redirect URI
    
    Returns:
        FacebookAuthManager instance with authenticated token
    """
    # Get credentials from environment or prompt
    if not app_id:
        app_id = os.getenv('FACEBOOK_APP_ID', '')
        if not app_id:
            app_id = input("Enter Facebook App ID: ").strip()
    
    if not app_secret:
        app_secret = os.getenv('FACEBOOK_APP_SECRET', '')
        if not app_secret:
            app_secret = input("Enter Facebook App Secret: ").strip()
    
    auth_manager = FacebookAuthManager(app_id, app_secret, redirect_uri)
    
    # Check if already authenticated
    if auth_manager.is_authenticated():
        print("✅ Already authenticated with Facebook")
        return auth_manager
    
    # Start OAuth flow
    print("Starting Facebook OAuth 2.0 flow...")
    authorization_url, state = auth_manager.get_authorization_url()
    
    print(f"\nPlease visit this URL to authorize:\n{authorization_url}\n")
    print("Opening browser...")
    webbrowser.open(authorization_url)
    
    # Get callback URL from user
    callback_url = input(
        "\nAfter authorizing, paste the full callback URL here: "
    ).strip()
    
    # Exchange code for token
    token = auth_manager.fetch_user_token(callback_url)
    
    print("✅ Successfully authenticated with Facebook!")
    print(f"Token expires in: {token.get('expires_in', 'unknown')} seconds")
    print("\nNext step: Exchange user token for page access token using get_page_access_token()")
    
    return auth_manager


if __name__ == '__main__':
    """Run OAuth setup interactively."""
    setup_facebook_oauth()

