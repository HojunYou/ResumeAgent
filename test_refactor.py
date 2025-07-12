#!/usr/bin/env python3
"""
test_refactor.py

Test script to verify the refactored ResumeAgent code works correctly.
"""

import asyncio
import logging
import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from resume_agent import ResumeAgent, setup_model_and_tools

async def test_setup():
    """Test the model and tools setup."""
    try:
        print("Testing model and tools setup...")
        model, tools = await setup_model_and_tools()
        print(f"✅ Model setup successful")
        print(f"✅ Tools loaded: {len(tools)} tools")
        
        # Print tool names
        tool_names = [tool.name for tool in tools]
        print(f"Available tools: {tool_names}")
        
        return model, tools
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return None, None

async def test_resume_agent():
    """Test the ResumeAgent class."""
    try:
        print("\nTesting ResumeAgent setup...")
        model, tools = await setup_model_and_tools()
        if model is None or tools is None:
            print("❌ Cannot test ResumeAgent without model and tools")
            return False
        
        agent = ResumeAgent(model, tools, "Machine Learning Engineer", "data/full_resume.pdf")
        print("✅ ResumeAgent created successfully")
        return True
    except Exception as e:
        print(f"❌ ResumeAgent test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Testing refactored ResumeAgent code...")
    
    # Test 1: Setup
    success1 = await test_setup()
    
    # Test 2: ResumeAgent
    success2 = await test_resume_agent()
    
    if success1 and success2:
        print("\n✅ All tests passed! The refactored code is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main()) 