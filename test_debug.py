#!/usr/bin/env python3
"""
Test script for debugging Health Insurance Claim Processor with sample PDFs
This script provides detailed logging and error tracking for end-to-end testing
"""

import os
import sys
import asyncio
import logging
import traceback
from pathlib import Path
from typing import List
import json

# Set up environment for debugging
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["DEBUG"] = "true"

# Set up comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_debug.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)

async def test_pdf_processing():
    """Test the PDF processing pipeline with comprehensive debugging"""
    
    logger.info("=" * 100)
    logger.info("🧪 STARTING PDF PROCESSING TEST")
    logger.info("=" * 100)
    
    try:
        # Import the components
        logger.info("📦 Step 1: Importing components...")
        from health_insurance_claim_processor.services.claim_processor import ClaimProcessingService
        from health_insurance_claim_processor.services.pdf_processor import PDFProcessor
        from health_insurance_claim_processor.utils.config import get_settings
        logger.info("✅ Components imported successfully")
        
        # Check settings
        logger.info("⚙️  Step 2: Checking configuration...")
        settings = get_settings()
        logger.info(f"   App Name: {settings.app_name}")
        logger.info(f"   Debug Mode: {settings.debug}")
        logger.info(f"   Log Level: {settings.log_level}")
        logger.info(f"   Ollama Model: {settings.ollama_model}")
        logger.info(f"   Max File Size: {settings.max_file_size}")
        logger.info(f"   Allowed Extensions: {settings.allowed_extensions}")
        
        # Test PDF processor initialization
        logger.info("📄 Step 3: Testing PDF Processor initialization...")
        pdf_processor = PDFProcessor()
        logger.info("✅ PDF Processor initialized successfully")
        
        # Test Claim processing service initialization
        logger.info("🏥 Step 4: Testing Claim Processing Service initialization...")
        claim_service = ClaimProcessingService()
        logger.info("✅ Claim Processing Service initialized successfully")
        
        # Look for sample PDF files
        logger.info("🔍 Step 5: Looking for sample PDF files...")
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
            return
        
        # Test with the first few PDFs found
        test_pdfs = found_pdfs[:3]  # Test with up to 3 PDFs
        logger.info(f"🎯 Step 6: Testing with {len(test_pdfs)} PDF files...")
        
        # Create mock UploadFile objects
        from fastapi import UploadFile
        import io
        
        mock_files = []
        for pdf_path in test_pdfs:
            logger.info(f"📖 Preparing {pdf_path.name} for testing...")
            
            try:
                with open(pdf_path, "rb") as f:
                    content = f.read()
                
                mock_file = UploadFile(
                    filename=pdf_path.name,
                    file=io.BytesIO(content),
                    content_type="application/pdf"
                )
                mock_files.append(mock_file)
                logger.info(f"✅ {pdf_path.name} prepared ({len(content)} bytes)")
                
            except Exception as e:
                logger.error(f"❌ Failed to prepare {pdf_path.name}: {e}")
                continue
        
        if not mock_files:
            logger.error("❌ No PDF files could be prepared for testing")
            return
        
        # Test the complete processing pipeline
        logger.info("🚀 Step 7: Testing complete processing pipeline...")
        logger.info(f"   Processing {len(mock_files)} files: {[f.filename for f in mock_files]}")
        
        try:
            result = await claim_service.process_claim(mock_files)
            
            logger.info("=" * 100)
            logger.info("🎉 PROCESSING COMPLETED SUCCESSFULLY!")
            logger.info("=" * 100)
            logger.info(f"Request ID: {result.request_id}")
            logger.info(f"Processing Time: {result.processing_time:.2f} seconds")
            logger.info(f"Documents Processed: {len(result.documents)}")
            logger.info(f"Validation Score: {result.validation.validation_score}")
            logger.info(f"Claim Decision: {result.claim_decision.status}")
            logger.info(f"Decision Reason: {result.claim_decision.reason}")
            
            # Save detailed results
            results_file = "test_results.json"
            with open(results_file, "w") as f:
                json.dump(result.model_dump(), f, indent=2, default=str)
            logger.info(f"📁 Detailed results saved to {results_file}")
            
        except Exception as e:
            logger.error("=" * 100)
            logger.error("❌ PROCESSING FAILED")
            logger.error("=" * 100)
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())
            
            # Save error details
            error_file = "test_error.log"
            with open(error_file, "w") as f:
                f.write(f"Error Type: {type(e).__name__}\n")
                f.write(f"Error Message: {str(e)}\n")
                f.write(f"Full Traceback:\n{traceback.format_exc()}")
            logger.info(f"📁 Error details saved to {error_file}")
            
            raise
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)

def main():
    """Main entry point"""
    logger.info("🧪 Health Insurance Claim Processor - Debug Test")
    logger.info("This script will test the complete processing pipeline with sample PDFs")
    logger.info("")
    
    try:
        asyncio.run(test_pdf_processing())
    except KeyboardInterrupt:
        logger.info("👋 Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
