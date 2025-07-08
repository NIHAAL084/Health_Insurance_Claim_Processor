#!/usr/bin/env python3
"""
Test script to verify the Health Insurance Claim Processor backend setup
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent / "src"))

async def test_backend():
    """Test the backend service without ADK Web"""
    
    print("🧪 Testing Health Insurance Claim Processor Backend")
    print("=" * 60)
    
    # Step 1: Set environment variable
    print("🔧 Setting up environment...")
    os.environ["OLLAMA_MODEL"] = "llama3.2:3b"
    print(f"✅ Set OLLAMA_MODEL: {os.environ.get('OLLAMA_MODEL')}")
    
    # Step 2: Test service import
    print("\n📦 Testing service imports...")
    try:
        from health_insurance_claim_processor.services.claim_processor import ClaimProcessingService
        print("✅ Successfully imported ClaimProcessingService")
    except Exception as e:
        print(f"❌ Failed to import ClaimProcessingService: {e}")
        return False
    
    # Step 3: Test service creation
    print("\n🏗️ Testing service creation...")
    try:
        service = ClaimProcessingService()
        print("✅ Successfully created ClaimProcessingService")
        print(f"   Main agent: {service.main_agent.name}")
        print(f"   Agent type: {type(service.main_agent).__name__}")
    except Exception as e:
        print(f"❌ Failed to create ClaimProcessingService: {e}")
        return False
    
    # Step 4: Test main app
    print("\n🌐 Testing FastAPI app creation...")
    try:
        from health_insurance_claim_processor.main import create_app
        app = create_app()
        print("✅ Successfully created FastAPI app")
        print(f"   Title: {app.title}")
        print(f"   Version: {app.version}")
    except Exception as e:
        print(f"❌ Failed to create FastAPI app: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All backend tests passed!")
    print("🚀 Backend is ready for testing!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    asyncio.run(test_backend())
