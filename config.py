"""
Configuration module for loading API keys and settings.
Use this in your research assistant code to access API keys.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Validate that keys are set
def validate_config():
    """Check if all required API keys are configured."""
    missing = []
    
    if not OPENROUTER_API_KEY or OPENROUTER_API_KEY == "your_openrouter_key_here":
        missing.append("OPENROUTER_API_KEY")
    
    if not TAVILY_API_KEY or TAVILY_API_KEY == "your_tavily_key_here":
        missing.append("TAVILY_API_KEY")
    
    if missing:
        raise ValueError(
            f"Missing or unconfigured API keys: {', '.join(missing)}\n"
            "Please add your API keys to the .env file. See README.md for instructions."
        )
    
    return True

# Example usage in your code:
# from config import OPENROUTER_API_KEY, TAVILY_API_KEY, validate_config
# 
# validate_config()  # Check keys are set
# # Now use OPENROUTER_API_KEY and TAVILY_API_KEY in your code
