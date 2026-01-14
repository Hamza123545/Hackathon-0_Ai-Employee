"""
Test Groq API Integration

Verifies that Groq API is properly configured and working.
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


def test_groq_api():
    """Test Groq API connection and basic functionality."""
    print("=" * 60)
    print("Groq API Integration Test")
    print("=" * 60)
    print()

    # Check API key
    api_key = os.getenv('GROQ_API_KEY', '')
    model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

    if not api_key:
        print("❌ GROQ_API_KEY not configured in .env")
        return False

    print(f"✅ API Key: {api_key[:20]}...")
    print(f"✅ Model: {model}")
    print()

    try:
        from groq import Groq

        print("Testing Groq API connection...")
        client = Groq(api_key=api_key)

        # Test simple completion
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful business analyst assistant."
                },
                {
                    "role": "user",
                    "content": "Analyze this sample business data and provide 2 key insights: Revenue: $50,000, Expenses: $35,000, Net Profit: $15,000"
                }
            ],
            temperature=0.5,
            max_tokens=500
        )

        result = response.choices[0].message.content

        print()
        print("=" * 60)
        print("✅ SUCCESS! Groq API is working")
        print("=" * 60)
        print()
        print("Sample AI Response:")
        print("-" * 60)
        print(result)
        print("-" * 60)
        print()
        print(f"Tokens used: {response.usage.total_tokens}")
        print(f"  Prompt tokens: {response.usage.prompt_tokens}")
        print(f"  Completion tokens: {response.usage.completion_tokens}")
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
    success = test_groq_api()
    sys.exit(0 if success else 1)
