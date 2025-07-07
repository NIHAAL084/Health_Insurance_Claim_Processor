"""Bill Processing Agent for extracting structured data from medical bills"""

from typing import List, Optional
from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from ..utils.config import get_settings


class BillData(BaseModel):
    """Schema for bill data extraction"""
    hospital_name: Optional[str] = Field(None, description="Name of the hospital, clinic, or medical facility")
    total_amount: Optional[float] = Field(None, description="Total amount billed (numeric value)")
    date_of_service: Optional[str] = Field(None, description="Date when medical services were provided (YYYY-MM-DD format)")
    patient_name: Optional[str] = Field(None, description="Name of the patient")
    bill_number: Optional[str] = Field(None, description="Invoice or bill number")
    insurance_amount: Optional[float] = Field(None, description="Amount covered by insurance")
    patient_amount: Optional[float] = Field(None, description="Amount patient needs to pay")
    service_details: Optional[List[str]] = Field(None, description="List of services provided with individual costs")
    doctor_name: Optional[str] = Field(None, description="Name of treating physician")
    department: Optional[str] = Field(None, description="Hospital department (Emergency, Surgery, etc.)")
    insurance_claim_number: Optional[str] = Field(None, description="Insurance claim reference number")
    payment_due_date: Optional[str] = Field(None, description="Date payment is due (YYYY-MM-DD format)")
    previous_balance: Optional[float] = Field(None, description="Any previous outstanding balance")
    payments_received: Optional[float] = Field(None, description="Any payments already received")
    content: Optional[str] = Field(None, description="Original document content")


class BillProcessingResult(BaseModel):
    """Schema for bill processing result"""
    processed_bills: List[BillData] = Field(..., description="List of processed bills")
    total_bills_processed: int = Field(..., description="Total number of bills processed")


def create_bill_processing_agent() -> LlmAgent:
    """Create and configure the bill processing agent"""
    
    settings = get_settings()
    
    instruction = """
    You are a bill processing agent specialized in extracting structured data from medical bills and invoices.
    
    You will receive classified documents from the document classification agent. Look for documents with type "bill" 
    from the {documents} output and process them.
    
    Your task is to analyze bill documents and extract the following information:
    
    Required fields:
    - hospital_name: Name of the hospital, clinic, or medical facility
    - total_amount: Total amount billed (numeric value)
    - date_of_service: Date when medical services were provided
    - patient_name: Name of the patient
    - bill_number: Invoice or bill number
    
    Optional fields (extract if available):
    - insurance_amount: Amount covered by insurance
    - patient_amount: Amount patient needs to pay
    - service_details: List of services provided with individual costs
    - doctor_name: Name of treating physician
    - department: Hospital department (Emergency, Surgery, etc.)
    - insurance_claim_number: Insurance claim reference number
    - payment_due_date: Date payment is due
    - previous_balance: Any previous outstanding balance
    - payments_received: Any payments already received
    
    Data extraction guidelines:
    1. Extract amounts as numeric values (remove currency symbols)
    2. Standardize dates to YYYY-MM-DD format
    3. Clean and normalize names (proper case)
    4. Validate that total_amount = insurance_amount + patient_amount (if both present)
    5. If multiple bills are in one document, separate them
    
    Return structured JSON data with the extracted fields. If a field cannot be found, use null.
    Be accurate and conservative - if you're unsure about a value, mark it as null rather than guessing.
    """
    
    bill_agent = LlmAgent(
        name="BillProcessingAgent",
        description="Extracts structured data from medical bills and invoices",
        instruction=instruction,
        model=LiteLlm(f"ollama/{settings.ollama_model}"),
        output_key="bill_data",
        output_schema=BillProcessingResult
    )
    
    return bill_agent
