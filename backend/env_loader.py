"""
Environment Variable Loader for Confucius Lecture Summarizer

This module provides secure and reliable environment variable loading from .env files.
It implements automatic search across multiple directory levels and provides
comprehensive validation for required API keys.

Key Features:
    - Automatic .env file discovery across directory hierarchy
    - Secure API key loading and validation
    - Support for quoted values and comments
    - Non-destructive loading (preserves existing environment variables)

Functions:
    load_env_file: Load and parse .env file into environment variables
    get_api_key: Retrieve and validate API keys from environment

Usage:
    from env_loader import load_env_file, get_api_key
    
    load_env_file()  # Auto-discovers .env file
    api_key = get_api_key("ELEVENLABS_API_KEY", required=True)
"""

import os
import sys
from pathlib import Path
from typing import Optional


def load_env_file(env_path: Optional[str] = None) -> bool:
    """
    Load environment variables from .env file with automatic discovery.
    
    Searches for .env files in the following order:
    1. Provided env_path (if specified)
    2. Current directory
    3. Parent directory (backend)
    4. Project root directory
    
    Args:
        env_path (str, optional): Explicit path to .env file. If None, performs auto-discovery.
    
    Returns:
        bool: True if .env file was successfully loaded, False otherwise
    
    Notes:
        - Existing environment variables are not overwritten
        - Supports KEY=VALUE format with optional quotes
        - Ignores empty lines and comments (starting with #)
    """
    if env_path is None:
        # Auto-discover .env file
        current_dir = Path(__file__).parent
        search_paths = [
            current_dir / ".env",                    # slides/
            current_dir.parent / ".env",             # backend/
            current_dir.parent.parent / ".env",      # project root/
        ]
        
        env_path = None
        for path in search_paths:
            if path.exists():
                env_path = path
                break
        
        if env_path is None:
            return False
    else:
        env_path = Path(env_path)
        if not env_path.exists():
            return False
    
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                
                # Parse KEY=VALUE pairs
                if "=" not in line:
                    print(f"⚠️  Warning: Invalid format in .env at line {line_num}: {line}", file=sys.stderr)
                    continue
                
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present (both single and double)
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                # Only set if not already in environment (respect existing values)
                if key and not os.environ.get(key):
                    os.environ[key] = value
        
        return True
    
    except Exception as e:
        print(f"⚠️  Warning: Error loading .env file: {e}", file=sys.stderr)
        return False


def get_api_key(key_name: str, required: bool = True) -> Optional[str]:
    """
    Retrieve and validate an API key from environment variables.
    
    Args:
        key_name (str): Name of the environment variable containing the API key
        required (bool): If True, exits program if key is not found. Defaults to True.
    
    Returns:
        str: API key value if found, None if not required and not found
    
    Raises:
        SystemExit: If required=True and key is not found
    
    Notes:
        - Automatically attempts to load .env file if key not found in environment
        - Validates that the key is not empty
    """
    # Attempt to load from .env if not already in environment
    if not os.environ.get(key_name):
        load_env_file()
    
    api_key = os.environ.get(key_name)
    
    if not api_key or api_key.strip() == "":
        if required:
            print(f"❌ Error: {key_name} not found in environment", file=sys.stderr)
            print(f"   Please set {key_name} in .env file or environment variables", file=sys.stderr)
            print(f"   Example: {key_name}=your-api-key-here", file=sys.stderr)
            sys.exit(1)
        return None
    
    return api_key.strip()


# Auto-load .env file when this module is imported
load_env_file()
