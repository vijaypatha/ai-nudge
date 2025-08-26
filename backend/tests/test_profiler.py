#!/usr/bin/env python3
"""
Test script to debug the profiler
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_core.agents.profiler import extract_preferences_from_text

async def test_profiler():
    print("Testing profiler...")
    
    test_text = "Client wants house with 5000 sqft and needs a home office"
    
    try:
        result = await extract_preferences_from_text(test_text, "real_estate")
        print(f"Profiler result: {result}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_profiler())
    print(f"Final result: {result}") 