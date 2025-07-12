"""PDF processing service for handling file operations and text extraction"""

import io
import logging
from typing import List, Dict, Any
from pathlib import Path

import pypdf
from fastapi import UploadFile, HTTPException

from utils.logger import logger
from utils.config import get_settings

# Set up module-level logger
module_logger = logging.getLogger(__name__)
module_logger.setLevel(logging.DEBUG)


class PDFProcessor:
    """Service for processing PDF files and extracting content"""
    
    def __init__(self):
        module_logger.info("📄 Initializing PDF Processor...")
        
        try:
            self.settings = get_settings()
            self.max_file_size = self.settings.max_file_size
            self.allowed_extensions = self.settings.allowed_extensions
            
            module_logger.debug(f"📋 PDF Processor settings:")
            module_logger.debug(f"   Max file size: {self.max_file_size} bytes")
            module_logger.debug(f"   Allowed extensions: {self.allowed_extensions}")
            
            module_logger.info("✅ PDF Processor initialized successfully")
            
        except Exception as e:
            module_logger.error(f"❌ Failed to initialize PDF Processor: {e}")
            module_logger.exception("Full traceback:")
            raise
    
    async def validate_files(self, files: List[UploadFile]) -> None:
        """Validate uploaded files"""
        module_logger.info(f"✅ Validating {len(files)} uploaded files...")
        
        if not files:
            module_logger.error("❌ No files provided for validation")
            raise HTTPException(status_code=400, detail="No files provided")
        
        for i, file in enumerate(files, 1):
            module_logger.debug(f"📄 Validating file {i}: {file.filename}")
            
            # Check file extension
            if not file.filename:
                module_logger.error(f"❌ File {i} has no filename")
                raise HTTPException(status_code=400, detail="File must have a name")
            
            file_extension = Path(file.filename).suffix.lower().replace('.', '')
            module_logger.debug(f"   Extension: {file_extension}")
            
            if file_extension not in self.allowed_extensions:
                module_logger.error(f"❌ File {file.filename} has invalid extension: {file_extension}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} has invalid extension. Allowed: {', '.join(self.allowed_extensions)}"
                )
            
            # Check file size
            if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
                module_logger.error(f"❌ File {file.filename} exceeds size limit: {file.size} > {self.max_file_size}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} exceeds maximum size of {self.max_file_size} bytes"
                )
            
            module_logger.debug(f"   ✅ File {file.filename} validation passed")
        
        module_logger.info(f"✅ All {len(files)} files validated successfully")
    
    async def extract_text_from_pdf(self, file: UploadFile) -> str:
        """Extract text content from a PDF file using pypdf"""
        module_logger.info(f"📖 Extracting text from PDF: {file.filename}")
        
        try:
            # Read file content
            module_logger.debug("📖 Reading file content...")
            content = await file.read()
            module_logger.debug(f"   File size: {len(content)} bytes")
            
            # Reset file pointer for potential future reads
            await file.seek(0)
            module_logger.debug("   File pointer reset")
            
            # Create PDF reader from bytes
            module_logger.debug("📄 Creating PDF reader...")
            pdf_reader = pypdf.PdfReader(io.BytesIO(content))
            module_logger.debug(f"   PDF pages detected: {len(pdf_reader.pages)}")
            
            # Extract text from all pages
            extracted_text = ""
            successful_pages = 0
            failed_pages = 0
            
            module_logger.debug("🔍 Extracting text from pages...")
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        extracted_text += f"\\n--- Page {page_num + 1} ---\\n"
                        extracted_text += page_text + "\\n"
                        successful_pages += 1
                        module_logger.debug(f"   ✅ Page {page_num + 1}: {len(page_text)} characters extracted")
                    else:
                        module_logger.warning(f"   ⚠️ Page {page_num + 1}: No text found")
                        
                except Exception as e:
                    failed_pages += 1
                    module_logger.warning(f"   ❌ Page {page_num + 1}: Extraction failed - {e}")
                    extracted_text += f"\\n--- Page {page_num + 1} (extraction failed) ---\\n"
            
            if not extracted_text.strip():
                module_logger.warning(f"⚠️ No text extracted from {file.filename}")
                return f"[No readable text found in {file.filename}]"
            
            module_logger.info(f"✅ Text extraction completed: {file.filename}")
            module_logger.debug(f"   📊 Stats: {successful_pages} successful, {failed_pages} failed pages")
            module_logger.debug(f"   📝 Total characters: {len(extracted_text)}")
            
            return extracted_text
            
        except Exception as e:
            module_logger.error(f"❌ Error extracting text from {file.filename}: {e}")
            module_logger.exception("Full traceback:")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to extract text from {file.filename}: {str(e)}"
            )
    
    async def process_files(self, files: List[UploadFile]) -> List[Dict[str, Any]]:
        """Process multiple PDF files and extract their content"""
        module_logger.info(f"📁 Processing {len(files)} PDF files...")
        
        # Validate files first
        await self.validate_files(files)
        module_logger.info("✅ File validation completed")
        
        processed_files = []
        
        for i, file in enumerate(files, 1):
            module_logger.info(f"📄 Processing file {i}/{len(files)}: {file.filename}")
            
            try:
                # Extract text content
                module_logger.debug(f"   🔍 Extracting text from {file.filename}...")
                text_content = await self.extract_text_from_pdf(file)
                
                # Create file info
                file_info = {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "text_content": text_content,
                    "character_count": len(text_content),
                    "status": "success"
                }
                
                processed_files.append(file_info)
                module_logger.info(f"   ✅ Successfully processed: {file.filename} ({len(text_content)} chars)")
                
            except HTTPException:
                # Re-raise HTTP exceptions
                module_logger.error(f"   ❌ HTTP exception while processing {file.filename}")
                raise
            except Exception as e:
                module_logger.error(f"   ❌ Unexpected error processing {file.filename}: {e}")
                module_logger.exception("   Full traceback:")
                
                # Add failed file info
                file_info = {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "text_content": "",
                    "character_count": 0,
                    "status": "failed",
                    "error": str(e)
                }
                processed_files.append(file_info)
                module_logger.warning(f"   ⚠️ Added failed file info for {file.filename}")
        
        # Check if any files were successfully processed
        successful_files = [f for f in processed_files if f["status"] == "success"]
        failed_files = [f for f in processed_files if f["status"] == "failed"]
        
        module_logger.info(f"📊 Processing summary:")
        module_logger.info(f"   ✅ Successful: {len(successful_files)}")
        module_logger.info(f"   ❌ Failed: {len(failed_files)}")
        
        if not successful_files:
            module_logger.error("❌ No files were successfully processed")
            raise HTTPException(
                status_code=500, 
                detail="Failed to process any of the provided files"
            )
        
        if failed_files:
            for failed_file in failed_files:
                module_logger.warning(f"   ⚠️ Failed: {failed_file['filename']} - {failed_file.get('error', 'Unknown error')}")
        
        module_logger.info(f"🎉 File processing completed: {len(successful_files)}/{len(files)} files successful")
        return processed_files
