"""Main FastAPI application for Health Insurance Claim Processor"""

import os
import sys
from contextlib import asynccontextmanager
from typing import List
from datetime import datetime

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add the src directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from health_insurance_claim_processor.models.response import ClaimProcessResponse, ErrorResponse
from health_insurance_claim_processor.services.claim_processor import ClaimProcessingService
from health_insurance_claim_processor.utils.config import get_settings
from health_insurance_claim_processor.utils.logger import logger


# Global service instance
claim_service: ClaimProcessingService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    global claim_service
    
    # Startup
    logger.info("Starting Health Insurance Claim Processor application")
    try:
        claim_service = ClaimProcessingService()
        logger.info("Claim processing service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize claim processing service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Health Insurance Claim Processor application")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="An agentic backend pipeline that processes medical insurance claim documents using AI tools",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure as needed for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


# Create app instance
app = create_app()


def get_claim_service() -> ClaimProcessingService:
    """Dependency to get claim processing service"""
    if claim_service is None:
        raise HTTPException(status_code=500, detail="Claim processing service not initialized")
    return claim_service


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check"""
    return {
        "message": "Health Insurance Claim Processor API",
        "status": "healthy",
        "version": get_settings().app_version
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-07-04T00:00:00Z",
        "service": "health-insurance-claim-processor"
    }


@app.post(
    "/process-claim",
    response_model=ClaimProcessResponse,
    tags=["Claim Processing"],
    summary="Process Insurance Claim Documents",
    description="Upload multiple PDF documents (bills, discharge summaries, etc.) to process an insurance claim"
)
async def process_claim(
    files: List[UploadFile] = File(..., description="PDF files to process"),
    service: ClaimProcessingService = Depends(get_claim_service)
) -> ClaimProcessResponse:
    """
    Process medical insurance claim documents.
    
    This endpoint accepts multiple PDF files and processes them through an AI-powered pipeline:
    1. Extract text from PDF documents
    2. Classify document types (bill, discharge summary, etc.)
    3. Process documents with specialized AI agents
    4. Validate data consistency
    5. Make final claim decision (approve/reject/pending)
    
    **Supported document types:**
    - Medical bills and invoices
    - Hospital discharge summaries
    - Insurance ID cards
    - Claim correspondence
    - Prescription documents
    - Laboratory reports
    
    **File requirements:**
    - Format: PDF only
    - Maximum size: 10MB per file
    - Multiple files supported
    """
    try:
        logger.info(f"Processing claim with {len(files)} files: {[f.filename for f in files]}")
        
        # Process the claim
        result = await service.process_claim(files)
        
        logger.info(f"Successfully processed claim {result.request_id}")
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing claim: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions"""
    error_response = ErrorResponse(
        error=exc.__class__.__name__,
        message=exc.detail,
        timestamp=datetime.utcnow()
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    error_response = ErrorResponse(
        error=exc.__class__.__name__,
        message="Internal server error",
        timestamp=datetime.utcnow()
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump()
    )


def main():
    """Main entry point for running the application"""
    settings = get_settings()
    
    uvicorn.run(
        "health_insurance_claim_processor.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
