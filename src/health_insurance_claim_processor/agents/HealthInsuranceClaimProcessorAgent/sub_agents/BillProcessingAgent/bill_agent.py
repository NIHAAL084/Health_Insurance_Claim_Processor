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
    document_type: str = Field(default="bill", description="Document type being processed")
    hospital_name: Optional[str] = Field(None, description="Name of the hospital, clinic, or medical facility")
    total_amount: Optional[float] = Field(None, description="Total amount billed (numeric value)")
    date_of_service: Optional[str] = Field(None, description="Date when medical services were provided (YYYY-MM-DD format)")
    patient_name: Optional[str] = Field(None, description="Name of the patient")
    bill_number: Optional[str] = Field(None, description="Invoice or bill number")
    insurance_amount: Optional[float] = Field(None, description="Amount covered by insurance")
    patient_amount: Optional[float] = Field(None, description="Amount patient needs to pay")
    service_details: Optional[List[str]] = Field(None, description="List of billed services with costs (procedures, consultations, room charges) - NOT medications")
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
        
        You will receive classified documents from the document classification agent. Your task is to:
        
        1. FIRST, identify and process ONLY documents with type "bill" from the {documents} input
        2. IGNORE all other document types (discharge summaries, prescriptions, lab reports, etc.)
        3. If NO bill documents are found, return an empty list with total_bills_processed: 0
        
        For valid bill documents, extract the following information:
        
        Required fields:
        - hospital_name: Name of the hospital, clinic, or medical facility
        - total_amount: Total amount billed (numeric value)
        - date_of_service: Date when medical services were provided
        - patient_name: Name of the patient
        - bill_number: Invoice or bill number
        
        Optional fields (extract if available):
        - insurance_amount: Amount covered by insurance
        - patient_amount: Amount patient needs to pay
        - service_details: List of services provided with individual costs (procedures, consultations, room charges)
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
        6. Service details should include medical procedures, room charges, consultations - NOT medications
        
        DOCUMENT TYPE VALIDATION:
        - ONLY process documents where document_type == "bill"
        - Discharge summaries, prescriptions, lab reports should be IGNORED by this agent
        - Return empty results if no bill documents are present
        
        Return structured JSON data with the extracted fields. If a field cannot be found, use null.
        Be accurate and conservative - if you're unsure about a value, mark it as null rather than guessing.
        """
        
        logger.debug("🤖 Creating LlmAgent for Bill Processing...")
        bill_agent = LlmAgent(
            name="BillProcessingAgent",
            description="Extracts structured data from medical bills and invoices",
            instruction=instruction,
            model=LiteLlm(
                model=f"ollama/{ollama_model}",
                timeout=600,  # 10 minutes timeout
                request_timeout=600,
                api_timeout=600
            ),
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
