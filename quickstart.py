#!/usr/bin/env python3
"""
Quick Start Script for Health Insurance Claim Processor Testing

This script provides a simple way to test the application with sample PDFs.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    """Main entry point for quick testing"""
    
    print("🏥 Health Insurance Claim Processor - Quick Test")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    if not Path("src/health_insurance_claim_processor").exists():
        print("❌ Error: Please run this script from the project root directory")
        print("   Expected to find: src/health_insurance_claim_processor/")
        sys.exit(1)
    
    # Check for sample PDFs
    samples_dir = Path("samples")
    if not samples_dir.exists():
        print("📁 Creating samples directory...")
        samples_dir.mkdir()
        print("✅ Samples directory created")
    
    pdf_files = list(samples_dir.glob("*.pdf"))
    if not pdf_files:
        print("📋 No PDF files found in samples/ directory")
        print("   Please add some PDF files to samples/ and run again")
        print("   Examples: medical bills, discharge summaries, insurance cards")
        print()
        print("🎯 You can also try the debug scripts directly:")
        print("   python debug_run.py     # Start server with debugging")
        print("   python test_debug.py    # Run end-to-end tests")
        print("   python api_test.py      # Test API endpoints")
        return
    
    print(f"📄 Found {len(pdf_files)} PDF files in samples/:")
    for pdf in pdf_files:
        print(f"   - {pdf.name}")
    print()
    
    # Ask user what they want to do
    print("🤔 What would you like to do?")
    print("   1. Test PDF processing (direct)")
    print("   2. Start server and test API")
    print("   3. Just start debug server")
    print("   4. Show debug summary")
    print()
    
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice == "1":
        print("🚀 Running direct PDF processing test...")
        subprocess.run([sys.executable, "test_debug.py"])
    
    elif choice == "2":
        print("🌐 Starting server and testing API...")
        print("   Note: This will start the server in the background")
        print("         Press Ctrl+C to stop")
        
        # Start server in background
        server_process = subprocess.Popen([sys.executable, "debug_run.py"])
        
        try:
            # Wait a bit for server to start
            print("⏱️  Waiting for server to start...")
            time.sleep(5)
            
            # Test API
            print("📡 Testing API endpoints...")
            subprocess.run([sys.executable, "api_test.py"])
            
        except KeyboardInterrupt:
            print("\n👋 Stopping server...")
        finally:
            server_process.terminate()
            server_process.wait()
    
    elif choice == "3":
        print("🚀 Starting debug server...")
        subprocess.run([sys.executable, "debug_run.py"])
    
    elif choice == "4":
        print("📊 Debug summary:")
        subprocess.run([sys.executable, "debug_summary.py"])
    
    else:
        print("❌ Invalid choice. Please run again and select 1-4.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
