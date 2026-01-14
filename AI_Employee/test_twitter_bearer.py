"""
Test Twitter Bearer Token Connection

Tests Twitter API connection using bearer token.
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


def test_twitter_bearer_token():
    """Test Twitter API with bearer token."""
    print("=" * 60)
    print("Twitter Bearer Token Connection Test")
    print("=" * 60)
    print()

    # Get bearer token
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN', '')

    if not bearer_token:
        print("❌ TWITTER_BEARER_TOKEN not configured in .env")
        return False

    print(f"✅ Bearer Token: {bearer_token[:30]}...")
    print()

    try:
        import tweepy

        print("Testing Twitter API connection...")
        client = tweepy.Client(bearer_token=bearer_token)

        # Test 1: Search recent tweets (public endpoint)
        print()
        print("Test 1: Searching recent tweets...")
        tweets = client.search_recent_tweets(
            query="python",
            max_results=10,
            tweet_fields=["created_at", "public_metrics"]
        )

        if tweets.data:
            print(f"✅ Successfully retrieved {len(tweets.data)} tweets")
            print()
            print("Sample tweet:")
            sample = tweets.data[0]
            print(f"  Text: {sample.text[:80]}...")
            if hasattr(sample, 'public_metrics'):
                print(f"  Likes: {sample.public_metrics.get('like_count', 0)}")
                print(f"  Retweets: {sample.public_metrics.get('retweet_count', 0)}")
        else:
            print("⚠️  No tweets found")

        print()
        print("=" * 60)
        print("✅ SUCCESS! Twitter API is working")
        print("=" * 60)
        print()
        print("Bearer Token Type: App-only authentication")
        print("Access Level: Read-only (public data)")
        print()
        print("Note: This token provides read-only access to public data.")
        print("For posting tweets, you'll need user context authentication.")
        print()

        return True

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_twitter_bearer_token()
    sys.exit(0 if success else 1)
