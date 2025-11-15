"""
Environment Variable Loader for Confucius Lecture Summarizer

This module provides functionality to load environment variables from .env files.
It automatically searches for .env files in the current directory and parent directories,
making API key management easier and more secure.

Functions:
    load_env_file: Load environment variables from a .env file
    get_api_key: Get an API key from environment variables with validation

Usage:
    from env_loader import get_api_key
    api_key = get_api_key("ELEVENLABS_API_KEY", required=True)
"""

import os
import sys
from pathlib import Path


def load_env_file(env_path=None):
    """
    Load environment variables from .env file.
    
    Args:
        env_path (str, optional): Path to .env file. If None, searches in current and parent directories.
    
    Returns:
        bool: True if .env file was found and loaded, False otherwise
    """
    if env_path is None:
        # Search for .env file in current directory and parent directories
        current_dir = Path(__file__).parent
        
        # Check slides directory
        env_file = current_dir / ".env"
        if not env_file.exists():
            # Check backend directory
            env_file = current_dir.parent / ".env"
        
        if not env_file.exists():
            # Check project root
            env_file = current_dir.parent.parent / ".env"
        
        if not env_file.exists():
            return False
        
        env_path = env_file
    else:
        env_path = Path(env_path)
        if not env_path.exists():
            return False
    
    # Load .env file
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                
                # Parse KEY=VALUE
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    # Set environment variable (don't override existing ones)
                    if key and not os.environ.get(key):
                        os.environ[key] = value
        
        return True
    
    except Exception as e:
        print(f"Warning: Error loading .env file: {e}")
        return False


def get_api_key(key_name, required=True):
    """
    Get an API key from environment variables.
    
    Args:
        key_name (str): Name of the environment variable
        required (bool): If True, exit if key is not found
    
    Returns:
        str: API key value, or None if not required and not found
    """
    # Try to load from .env if not already set
    if not os.environ.get(key_name):
        load_env_file()
    
    api_key = os.environ.get(key_name)
    
    if not api_key and required:
        print(f"\n❌ ERROR: {key_name} not found!")
        print("\nPlease set it in one of these ways:")
        print(f"\n1. Create a .env file in the backend/ directory:")
        print(f"   {key_name}=your-api-key-here")
        print(f"\n2. Set it as an environment variable:")
        print(f"   export {key_name}='your-api-key-here'")
        print()
        return None
    
    return api_key


# Auto-load .env file when this module is imported
load_env_file()
load_env_file()
