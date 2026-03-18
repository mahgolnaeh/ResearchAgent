"""
Simple test script to verify your environment variables are set up correctly.
Run this after adding your API keys to the .env file.
"""

import os
from dotenv import load_dotenv

def test_setup():
    """Test if environment variables are loaded correctly."""
    
    # Load environment variables from .env file
    load_dotenv()
    
    print("=" * 50)
    print("Testing Environment Variable Setup")
    print("=" * 50)
    
    # Check OpenRouter key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key and openrouter_key != "your_openrouter_key_here":
        print("✓ OpenRouter API Key: Loaded successfully")
        print(f"  Key preview: {openrouter_key[:15]}...")
    else:
        print("✗ OpenRouter API Key: NOT SET or still using placeholder")
        print("  Please add your key to the .env file")
    
    print()
    
    # Check Tavily key
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key and tavily_key != "your_tavily_key_here":
        print("✓ Tavily API Key: Loaded successfully")
        print(f"  Key preview: {tavily_key[:15]}...")
    else:
        print("✗ Tavily API Key: NOT SET or still using placeholder")
        print("  Please add your key to the .env file")
    
    print()
    print("=" * 50)
    
    # Final check
    if (openrouter_key and openrouter_key != "your_openrouter_key_here" and
        tavily_key and tavily_key != "your_tavily_key_here"):
        print("✓ All API keys are configured correctly!")
        return True
    else:
        print("✗ Please configure your API keys in the .env file")
        return False

if __name__ == "__main__":
    test_setup()
