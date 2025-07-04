"""Response models for the Health Insurance Claim Processor API"""

from datetime import datetime
from typing import List, Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class DocumentData(BaseModel):
    """Structured data extracted from a document"""
    
    type: str = Field(..., description="Type of document (bill, discharge_summary, id_card, correspondence)")
    content: str = Field(..., description="Extracted text content from the document")
    
    # Common fields that might be extracted
    hospital_name: Optional[str] = Field(None, description="Name of the hospital or medical facility")
    patient_name: Optional[str] = Field(None, description="Name of the patient")
    date_of_service: Optional[str] = Field(None, description="Date of medical service")
    
    # Bill-specific fields
    total_amount: Optional[float] = Field(None, description="Total amount billed")
    insurance_amount: Optional[float] = Field(None, description="Amount covered by insurance")
    patient_amount: Optional[float] = Field(None, description="Amount to be paid by patient")
    bill_number: Optional[str] = Field(None, description="Bill or invoice number")
    
    # Discharge summary specific fields
    diagnosis: Optional[str] = Field(None, description="Primary diagnosis")
    admission_date: Optional[str] = Field(None, description="Date of admission")
    discharge_date: Optional[str] = Field(None, description="Date of discharge")
    treatment_summary: Optional[str] = Field(None, description="Summary of treatment provided")
    doctor_name: Optional[str] = Field(None, description="Name of attending physician")
    
    # ID card specific fields
    policy_number: Optional[str] = Field(None, description="Insurance policy number")
    member_id: Optional[str] = Field(None, description="Member identification number")
    insurance_company: Optional[str] = Field(None, description="Name of insurance company")
    coverage_type: Optional[str] = Field(None, description="Type of coverage")
    
    # Additional extracted fields
    extracted_data: Optional[dict] = Field(None, description="Additional extracted data specific to document type")


class ValidationResult(BaseModel):
    """Result of document validation"""
    
    missing_documents: List[str] = Field(
        default_factory=list, 
        description="List of missing required document types"
    )
    discrepancies: List[str] = Field(
        default_factory=list, 
        description="List of data discrepancies found across documents"
    )
    validation_score: Optional[float] = Field(
        None, 
        description="Overall validation score (0-1)"
    )


class ClaimDecision(BaseModel):
    """Final claim processing decision"""
    
    status: Literal["approved", "rejected", "pending"] = Field(
        ..., 
        description="Final decision status"
    )
    reason: str = Field(
        ..., 
        description="Detailed reason for the decision"
    )
    confidence_score: Optional[float] = Field(
        None, 
        description="Confidence score for the decision (0-1)"
    )
    recommended_actions: Optional[List[str]] = Field(
        None, 
        description="Recommended actions for pending or rejected claims"
    )


class ClaimProcessResponse(BaseModel):
    """Response model for successful claim processing"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "req_123456789",
                "processing_time": 15.7,
                "timestamp": "2024-01-15T10:30:00Z",
                "documents": [
                    {
                        "type": "bill",
                        "hospital_name": "ABC Hospital",
                        "total_amount": 12500,
                        "date_of_service": "2024-04-10",
                        "content": "text from the bill document",
                        "bill_number": "INV-2024-001",
                        "patient_name": "John Doe"
                    },
                    {
                        "type": "discharge_summary",
                        "patient_name": "John Doe",
                        "diagnosis": "Fracture",
                        "admission_date": "2024-04-01",
                        "discharge_date": "2024-04-10",
                        "content": "text from the discharge summary document",
                        "hospital_name": "ABC Hospital",
                        "doctor_name": "Dr. Smith"
                    }
                ],
                "validation": {
                    "missing_documents": [],
                    "discrepancies": [],
                    "validation_score": 0.95
                },
                "claim_decision": {
                    "status": "approved",
                    "reason": "All required documents present and data is consistent",
                    "confidence_score": 0.92
                }
            }
        }
    )
    
    request_id: str = Field(..., description="Unique identifier for this processing request")
    processing_time: float = Field(..., description="Time taken to process the claim in seconds")
    timestamp: datetime = Field(..., description="Timestamp when processing completed")
    
    documents: List[DocumentData] = Field(
        ..., 
        description="List of processed documents with extracted data"
    )
    validation: ValidationResult = Field(
        ..., 
        description="Validation results for the submitted documents"
    )
    claim_decision: ClaimDecision = Field(
        ..., 
        description="Final claim decision with reasoning"
    )


class ErrorResponse(BaseModel):
    """Error response model"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "message": "Invalid file format. Only PDF files are allowed.",
                "request_id": "req_123456789",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Detailed error message")
    request_id: Optional[str] = Field(None, description="Request ID if available")
    timestamp: datetime = Field(..., description="Timestamp when error occurred")
