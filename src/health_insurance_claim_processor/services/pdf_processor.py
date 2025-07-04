"""PDF processing service for handling file operations and text extraction"""

import io
from typing import List, Dict, Any
from pathlib import Path

import pypdf
from fastapi import UploadFile, HTTPException

from ..utils.logger import logger
from ..utils.config import get_settings


class PDFProcessor:
    """Service for processing PDF files and extracting content"""
    
    def __init__(self):
        self.settings = get_settings()
        self.max_file_size = self.settings.max_file_size
        self.allowed_extensions = self.settings.allowed_extensions
    
    async def validate_files(self, files: List[UploadFile]) -> None:
        """Validate uploaded files"""
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        for file in files:
            # Check file extension
            if not file.filename:
                raise HTTPException(status_code=400, detail="File must have a name")
            
            file_extension = Path(file.filename).suffix.lower().replace('.', '')
            if file_extension not in self.allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} has invalid extension. Allowed: {', '.join(self.allowed_extensions)}"
                )
            
            # Check file size
            if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} exceeds maximum size of {self.max_file_size} bytes"
                )
    
    async def extract_text_from_pdf(self, file: UploadFile) -> str:
        """Extract text content from a PDF file using pypdf"""
        try:
            # Read file content
            content = await file.read()
            
            # Reset file pointer for potential future reads
            await file.seek(0)
            
            # Create PDF reader from bytes
            pdf_reader = pypdf.PdfReader(io.BytesIO(content))
            
            # Extract text from all pages
            extracted_text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        extracted_text += f"\\n--- Page {page_num + 1} ---\\n"
                        extracted_text += page_text + "\\n"
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1} of {file.filename}: {e}")
                    extracted_text += f"\\n--- Page {page_num + 1} (extraction failed) ---\\n"
            
            if not extracted_text.strip():
                logger.warning(f"No text extracted from {file.filename}")
                return f"[No readable text found in {file.filename}]"
            
            logger.info(f"Successfully extracted text from {file.filename} ({len(extracted_text)} characters)")
            return extracted_text
            
        except Exception as e:
            logger.error(f"Error extracting text from {file.filename}: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to extract text from {file.filename}: {str(e)}"
            )
    
    async def process_files(self, files: List[UploadFile]) -> List[Dict[str, Any]]:
        """Process multiple PDF files and extract their content"""
        # Validate files first
        await self.validate_files(files)
        
        processed_files = []
        
        for file in files:
            try:
                # Extract text content
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
                logger.info(f"Successfully processed file: {file.filename}")
                
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(f"Unexpected error processing {file.filename}: {e}")
                
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
        
        # Check if any files were successfully processed
        successful_files = [f for f in processed_files if f["status"] == "success"]
        if not successful_files:
            raise HTTPException(
                status_code=500, 
                detail="Failed to process any of the provided files"
            )
        
        logger.info(f"Processed {len(successful_files)} out of {len(files)} files successfully")
        return processed_files
