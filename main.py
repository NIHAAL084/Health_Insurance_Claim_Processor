"""Main FastAPI application for Health Insurance Claim Processor"""

import os
import sys
from contextlib import asynccontextmanager
from typing import List, Any
from datetime import datetime, timezone
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pathlib

# Import from new root-level structure
from services.claim_processor import ClaimProcessingService
from utils.config import get_settings
from utils.logger import logger


# Global service instance
claim_service: ClaimProcessingService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    global claim_service
    
    # Startup
    logger.info("🚀 Starting Health Insurance Claim Processor application")
    logger.info("=" * 60)
    logger.info("🏥 HEALTH INSURANCE CLAIM PROCESSOR")
    logger.info("=" * 60)
    
    try:
        logger.info("🔧 Initializing claim processing service...")
        
        # Set environment variables for agents to use
        settings = get_settings()
        os.environ["OLLAMA_MODEL"] = settings.ollama_model
        logger.info(f"🔧 Set OLLAMA_MODEL environment variable: {settings.ollama_model}")
        
        claim_service = ClaimProcessingService()
        logger.info("✅ Claim processing service initialized successfully")
        
        # Log configuration
        logger.info("📋 Application Configuration:")
        logger.info(f"   📱 App Name: {settings.app_name}")
        logger.info(f"   🔢 Version: {settings.app_version}")
        logger.info(f"   🌐 Host: {settings.host}:{settings.port}")
        logger.info(f"   🐛 Debug Mode: {settings.debug}")
        logger.info(f"   📊 Log Level: {settings.log_level}")
        logger.info(f"   🤖 Ollama Model: {settings.ollama_model}")
        logger.info(f"   📁 Max File Size: {settings.max_file_size} bytes")
        logger.info(f"   📄 Allowed Extensions: {settings.allowed_extensions}")
        
        logger.info("🎉 Application startup completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize claim processing service: {e}")
        logger.exception("Full startup traceback:")
        raise
    
    yield
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("🛑 Shutting down Health Insurance Claim Processor application")
    logger.info("👋 Goodbye!")
    logger.info("=" * 60)


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
    
    # Mount the frontend directory to serve static files
    frontend_path = pathlib.Path(__file__).parent / "frontend"
    app.mount("/frontend", StaticFiles(directory=frontend_path, html=True), name="frontend")

    return app


# Create app instance
app = create_app()


def get_claim_service() -> ClaimProcessingService:
    """Dependency to get claim processing service"""
    if claim_service is None:
        raise HTTPException(status_code=500, detail="Claim processing service not initialized")
    return claim_service


@app.get("/", tags=["Health"], include_in_schema=False)
def serve_frontend():
    """Serve the frontend index.html at the root URL"""
    frontend_path = pathlib.Path(__file__).parent / "frontend"
    return FileResponse(frontend_path / "index.html")


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
    tags=["Claim Processing"],
    summary="Process Insurance Claim Documents",
    description="Upload multiple PDF documents (bills, discharge summaries, etc.) to process an insurance claim"
)
async def process_claim(
    files: List[UploadFile] = File(..., description="PDF files to process"),
    service: ClaimProcessingService = Depends(get_claim_service)
) -> dict[str, Any]:
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
    request_start = datetime.utcnow()
    request_id = None
    
    try:
        logger.info("=" * 80)
        logger.info("🏥 NEW CLAIM PROCESSING REQUEST")
        logger.info("=" * 80)
        logger.info(f"📁 Received {len(files)} files: {[f.filename for f in files]}")
        logger.info(f"⏰ Request started at: {request_start.isoformat()}")
        
        # Log file details
        for i, file in enumerate(files, 1):
            logger.info(f"📄 File {i}: {file.filename}")
            logger.info(f"   📦 Content Type: {file.content_type}")
            if hasattr(file, 'size') and file.size:
                logger.info(f"   📏 Size: {file.size} bytes")
        
        logger.info("🚀 Starting claim processing...")
        
        # Process the claim
        result = await service.process_claim(files)
        logger.info("=" * 80)
        logger.info("🎉 CLAIM PROCESSING COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        # Optionally, parse and log request_id, duration, etc. from result if needed
        return result
        
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions as-is
        processing_duration = (datetime.utcnow() - request_start).total_seconds()
        logger.error("=" * 80)
        logger.error("❌ CLAIM PROCESSING FAILED (HTTP ERROR)")
        logger.error("=" * 80)
        logger.error(f"🆔 Request ID: {request_id or 'Unknown'}")
        logger.error(f"⏱️ Duration: {processing_duration:.2f} seconds")
        logger.error(f"🚨 HTTP Error: {http_exc.status_code} - {http_exc.detail}")
        logger.error("=" * 80)
        raise
        
    except Exception as e:
        processing_duration = (datetime.utcnow() - request_start).total_seconds()
        logger.error("=" * 80)
        logger.error("❌ CLAIM PROCESSING FAILED (UNEXPECTED ERROR)")
        logger.error("=" * 80)
        logger.error(f"🆔 Request ID: {request_id or 'Unknown'}")
        logger.error(f"⏱️ Duration: {processing_duration:.2f} seconds")
        logger.error(f"🚨 Error: {str(e)}")
        logger.exception("Full traceback:")
        logger.error("=" * 80)
        
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


from fastapi import Request

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    error_response = {
        "request_id": getattr(request.state, 'request_id', 'unknown'),
        "error": exc.__class__.__name__,
        "message": exc.detail,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    error_response = {
        "request_id": getattr(request.state, 'request_id', 'unknown'),
        "error": exc.__class__.__name__,
        "message": "Internal server error",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    return JSONResponse(
        status_code=500,
        content=error_response
    )


def main():
    """Main entry point for running the application"""
    settings = get_settings()
    
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
