"""Request models for the Health Insurance Claim Processor API"""

from typing import List
from pydantic import BaseModel, Field
from fastapi import UploadFile


class ClaimProcessRequest(BaseModel):
    """Request model for claim processing"""
    
    files: List[UploadFile] = Field(
        ..., 
        description="List of PDF files to process (bills, discharge summaries, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "files": ["bill.pdf", "discharge_summary.pdf", "id_card.pdf"]
            }
        }
