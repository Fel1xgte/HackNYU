#!/usr/bin/env python3
"""Quick test to verify Gemini API is working"""

import os
import sys
from env_loader import load_env_file
import google.generativeai as genai

load_env_file()

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("❌ GEMINI_API_KEY not found")
    sys.exit(1)

print(f"✅ API Key loaded (length: {len(api_key)})")

try:
    client = genai.Client(api_key=api_key)
    print("✅ Gemini client created")
    
    print("🔄 Testing API call...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say 'Hello, I am working!' in 5 words or less."
    )
    
    print(f"✅ API Response: {response.text}")
    print("\n✨ Gemini API is working correctly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
