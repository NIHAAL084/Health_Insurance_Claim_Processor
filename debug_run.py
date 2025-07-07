#!/usr/bin/env python3
"""
Debug runner for Health Insurance Claim Processor
Sets up maximum debugging verbosity for troubleshooting
"""

import os
import sys
import logging
from pathlib import Path

# Set environment variables for maximum debugging
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["DEBUG"] = "true"

# Set up early logging to capture startup issues
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)

def debug_startup():
    """Debug startup procedure"""
    logger.info("=" * 80)
    logger.info("🐛 DEBUG MODE - Health Insurance Claim Processor")
    logger.info("=" * 80)
    
    # Check environment
    logger.info("🔍 Environment Check:")
    logger.info(f"   Python version: {sys.version}")
    logger.info(f"   Working directory: {os.getcwd()}")
    
    # Check required files
    required_files = [".env", "pyproject.toml", "src/health_insurance_claim_processor/main.py"]
    for file in required_files:
        if Path(file).exists():
            logger.info(f"   ✅ {file} exists")
        else:
            logger.error(f"   ❌ {file} missing")
    
    # Check environment variables
    logger.info("🔑 Environment Variables:")
    env_vars = ["GOOGLE_API_KEY", "OLLAMA_MODEL", "LOG_LEVEL", "DEBUG"]
    for var in env_vars:
        value = os.environ.get(var, "NOT SET")
        if var == "GOOGLE_API_KEY":
            display_value = "***SET***" if value != "NOT SET" else "NOT SET"
        else:
            display_value = value
        logger.info(f"   {var}: {display_value}")
    
    logger.info("=" * 80)

def main():
    """Main entry point for debug mode"""
    debug_startup()
    
    try:
        logger.info("🚀 Starting FastAPI application in debug mode...")
        
        # Import and run the main application
        from health_insurance_claim_processor.main import main as app_main
        app_main()
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)

if __name__ == "__main__":
    main()
