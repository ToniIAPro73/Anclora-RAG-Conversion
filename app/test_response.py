#!/usr/bin/env python3

# Test script to check the response function signature
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from common.langchain_module import response
    print("✅ Successfully imported response function")
    print(f"Function signature: {response.__code__.co_varnames}")
    print(f"Function parameters: {response.__code__.co_argcount}")

    # Test calling the function
    try:
        result = response("test query", "en")
        print("✅ Function call successful")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Function call failed: {e}")

except ImportError as e:
    print(f"❌ Import failed: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")