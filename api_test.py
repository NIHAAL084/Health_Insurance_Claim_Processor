#!/usr/bin/env python3
"""
API Test script for Health Insurance Claim Processor
Tests the FastAPI endpoints with sample PDFs via HTTP requests
"""

import os
import sys
import asyncio
import logging
import traceback
from pathlib import Path
import json
import httpx
from typing import List

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('api_test.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)

class APITester:
    """Test the Health Insurance Claim Processor API"""
    
    def __init__(self, base_url: str = "http://localhost:8003"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        
    async def test_health_check(self) -> bool:
        """Test the health check endpoint"""
        logger.info("🏥 Testing health check endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            logger.info(f"   Status Code: {response.status_code}")
            logger.info(f"   Response: {response.json()}")
            
            if response.status_code == 200:
                logger.info("✅ Health check passed")
                return True
            else:
                logger.error(f"❌ Health check failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    async def test_root_endpoint(self) -> bool:
        """Test the root endpoint"""
        logger.info("🏠 Testing root endpoint...")
        
        try:
            response = await self.client.get(f"{self.base_url}/")
            logger.info(f"   Status Code: {response.status_code}")
            logger.info(f"   Response: {response.json()}")
            
            if response.status_code == 200:
                logger.info("✅ Root endpoint test passed")
                return True
            else:
                logger.error(f"❌ Root endpoint failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Root endpoint test failed: {e}")
            return False
    
    async def test_claim_processing(self, pdf_files: List[Path]) -> bool:
        """Test the claim processing endpoint with PDF files"""
        logger.info(f"📄 Testing claim processing with {len(pdf_files)} files...")
        
        try:
            # Prepare files for upload
            files = []
            for pdf_path in pdf_files:
                logger.info(f"   📖 Preparing {pdf_path.name}...")
                
                try:
                    with open(pdf_path, "rb") as f:
                        content = f.read()
                    
                    files.append(
                        ("files", (pdf_path.name, content, "application/pdf"))
                    )
                    logger.info(f"   ✅ {pdf_path.name} prepared ({len(content)} bytes)")
                    
                except Exception as e:
                    logger.error(f"   ❌ Failed to prepare {pdf_path.name}: {e}")
                    continue
            
            if not files:
                logger.error("❌ No files could be prepared for testing")
                return False
            
            # Send request to process claim
            logger.info("🚀 Sending claim processing request...")
            response = await self.client.post(
                f"{self.base_url}/process-claim",
                files=files
            )
            
            logger.info(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Claim processing completed successfully")
                result = response.json()
                
                # Log key results
                logger.info(f"   Request ID: {result.get('request_id')}")
                logger.info(f"   Processing Time: {result.get('processing_time'):.2f} seconds")
                logger.info(f"   Documents Processed: {len(result.get('documents', []))}")
                logger.info(f"   Validation Score: {result.get('validation', {}).get('validation_score')}")
                logger.info(f"   Claim Decision: {result.get('claim_decision', {}).get('status')}")
                logger.info(f"   Decision Reason: {result.get('claim_decision', {}).get('reason')}")
                
                # Save detailed results
                results_file = "api_test_results.json"
                with open(results_file, "w") as f:
                    json.dump(result, f, indent=2)
                logger.info(f"📁 Detailed results saved to {results_file}")
                
                return True
            else:
                logger.error(f"❌ Claim processing failed with status {response.status_code}")
                logger.error(f"   Error response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Claim processing test failed: {e}")
            logger.exception("Full traceback:")
            return False
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

async def find_sample_pdfs() -> List[Path]:
    """Find sample PDF files for testing"""
    logger.info("🔍 Looking for sample PDF files...")
    
    sample_dirs = [
        "./samples",
        "./test_files", 
        "./pdfs",
        Path.home() / "Documents" / "test_pdfs",
        Path.home() / "Downloads"
    ]
    
    found_pdfs = []
    for sample_dir in sample_dirs:
        if Path(sample_dir).exists():
            pdfs = list(Path(sample_dir).glob("*.pdf"))
            if pdfs:
                found_pdfs.extend(pdfs)
                logger.info(f"   Found {len(pdfs)} PDF files in {sample_dir}")
                for pdf in pdfs:
                    logger.info(f"     - {pdf.name}")
    
    if not found_pdfs:
        logger.warning("⚠️  No sample PDF files found in common locations")
        logger.info("📋 To test with your own PDFs, please:")
        logger.info("   1. Create a 'samples' directory in the project root")
        logger.info("   2. Place your PDF files there")
        logger.info("   3. Run this test script again")
    
    return found_pdfs[:3]  # Return up to 3 PDFs for testing

async def main():
    """Main entry point"""
    logger.info("=" * 100)
    logger.info("🧪 Health Insurance Claim Processor - API Test")
    logger.info("=" * 100)
    logger.info("This script will test the FastAPI endpoints with sample PDFs")
    logger.info("")
    
    # Check if server is running
    logger.info("🔍 Checking if server is running on http://localhost:8003...")
    logger.info("   Make sure to start the server first with:")
    logger.info("   python debug_run.py")
    logger.info("   or")
    logger.info("   python run.py")
    logger.info("")
    
    tester = APITester()
    
    try:
        # Test health check
        health_ok = await tester.test_health_check()
        if not health_ok:
            logger.error("❌ Health check failed. Is the server running?")
            return
        
        # Test root endpoint
        root_ok = await tester.test_root_endpoint()
        if not root_ok:
            logger.error("❌ Root endpoint test failed")
            return
        
        # Find sample PDFs
        sample_pdfs = await find_sample_pdfs()
        if not sample_pdfs:
            logger.warning("⚠️  No PDF files found for testing")
            return
        
        # Test claim processing
        claim_ok = await tester.test_claim_processing(sample_pdfs)
        if claim_ok:
            logger.info("=" * 100)
            logger.info("🎉 ALL TESTS PASSED!")
            logger.info("=" * 100)
        else:
            logger.error("=" * 100)
            logger.error("❌ CLAIM PROCESSING TEST FAILED")
            logger.error("=" * 100)
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        logger.exception("Full traceback:")
        
    finally:
        await tester.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1)
