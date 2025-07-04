#!/usr/bin/env python3
"""
Health Insurance Claim Processor - Simple startup script
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Setup the development environment"""
    print("🏥 Health Insurance Claim Processor - Setup")
    
    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        print("📋 Creating .env file from template...")
        env_example = Path(".env.example")
        if env_example.exists():
            env_file.write_text(env_example.read_text())
            print("✅ .env file created. Please update your GOOGLE_API_KEY!")
        else:
            print("❌ .env.example not found")
            return False
    
    # Install dependencies
    print("📦 Installing dependencies with uv...")
    try:
        subprocess.run(["uv", "sync"], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False
    except FileNotFoundError:
        print("❌ uv not found. Please install uv first: pip install uv")
        return False
    
    return True

def run_development_server():
    """Run the development server"""
    print("🚀 Starting development server...")
    try:
        subprocess.run([
            "uv", "run", "fastapi", "dev", 
            "src/health_insurance_claim_processor/main.py",
            "--port", "8000"
        ], check=True)
    except subprocess.CalledProcessError:
        print("❌ Failed to start development server")
        return False
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
        return True

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_environment()
    else:
        if setup_environment():
            run_development_server()

if __name__ == "__main__":
    main()
