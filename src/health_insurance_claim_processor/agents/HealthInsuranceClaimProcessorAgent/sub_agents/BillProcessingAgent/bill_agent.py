"""Bill Processing Agent for extracting structured data from medical bills"""

import os
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
    
    logger.info("💰 Creating Bill Processing Agent...")
    
    try:
        ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
        logger.debug(f"📝 Bill Processing Agent settings: ollama_model={ollama_model}")
        
        instruction = """
        You are a bill processing agent specialized in extracting structured data from medical bills and invoices.
        
        You will receive classified documents from the document classification agent. Look for documents with type "bill" 
        from the {documents} output and process them. The text content has already been extracted from PDF files.
        
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
        
        Note: Text extraction from PDFs has already been completed. Focus on data extraction and structuring.
        """
        
        logger.debug("🤖 Creating LlmAgent for Bill Processing...")
        bill_agent = LlmAgent(
            name="BillProcessingAgent",
            description="Extracts structured data from medical bills and invoices",
            instruction=instruction,
            model=LiteLlm(f"ollama/{ollama_model}"),
            output_key="bill_data",
            output_schema=BillProcessingResult
        )
        
        logger.info(f"✅ Bill Processing Agent created successfully with model: ollama/{ollama_model}")
        logger.debug(f"📄 Bill Processing Agent config: name={bill_agent.name}, output_key={bill_agent.output_key}")
        logger.debug(f"📊 Output schema: {BillProcessingResult.__name__}")
        
        return bill_agent
        
    except Exception as e:
        logger.error(f"❌ Failed to create Bill Processing Agent: {e}")
        logger.exception("Full traceback:")
        raise
