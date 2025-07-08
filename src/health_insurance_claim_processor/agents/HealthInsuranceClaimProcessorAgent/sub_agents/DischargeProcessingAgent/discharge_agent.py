"""Discharge Summary Processing Agent for extracting structured data from discharge summaries"""

import os
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DischargeData(BaseModel):
    """Schema for discharge summary data extraction"""
    patient_name: Optional[str] = Field(None, description="Name of the patient")
    admission_date: Optional[str] = Field(None, description="Date of admission (YYYY-MM-DD format)")
    discharge_date: Optional[str] = Field(None, description="Date of discharge (YYYY-MM-DD format)")
    primary_diagnosis: Optional[str] = Field(None, description="Primary diagnosis")
    secondary_diagnosis: Optional[List[str]] = Field(None, description="Secondary diagnoses")
    procedures_performed: Optional[List[str]] = Field(None, description="Medical procedures performed")
    doctor_name: Optional[str] = Field(None, description="Name of attending physician")
    hospital_name: Optional[str] = Field(None, description="Name of the hospital")
    department: Optional[str] = Field(None, description="Hospital department")
    length_of_stay: Optional[int] = Field(None, description="Length of stay in days")
    discharge_instructions: Optional[str] = Field(None, description="Discharge instructions")
    medications_prescribed: Optional[List[str]] = Field(None, description="Medications prescribed at discharge")
    follow_up_instructions: Optional[str] = Field(None, description="Follow-up care instructions")
    patient_condition: Optional[str] = Field(None, description="Patient condition at discharge")
    complications: Optional[List[str]] = Field(None, description="Any complications during stay")
    content: Optional[str] = Field(None, description="Original document content")


class DischargeProcessingResult(BaseModel):
    """Schema for discharge processing result"""
    processed_discharge_summaries: List[DischargeData] = Field(..., description="List of processed discharge summaries")
    total_summaries_processed: int = Field(..., description="Total number of discharge summaries processed")


def create_discharge_processing_agent() -> LlmAgent:
    """Create and configure the discharge processing agent"""
    
    logger.info("🏥 Creating Discharge Processing Agent...")
    
    try:
        ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
        logger.debug(f"📝 Discharge Processing Agent settings: ollama_model={ollama_model}")
        
        instruction = """
        You are a discharge summary processing agent specialized in extracting structured data from hospital discharge summaries.
        
        You will receive classified documents from the document classification agent. Look for documents with type "discharge_summary" 
        from the {documents} output and process them. The text content has already been extracted from PDF files.
        
        Your task is to analyze discharge summary documents and extract the following information:
        
        Required fields:
        - patient_name: Name of the patient
        - admission_date: Date of admission
        - discharge_date: Date of discharge
        - primary_diagnosis: Primary diagnosis
        - doctor_name: Name of attending physician
        - hospital_name: Name of the hospital
        
        Optional fields (extract if available):
        - secondary_diagnosis: Secondary diagnoses (list)
        - procedures_performed: Medical procedures performed (list)
        - department: Hospital department
        - length_of_stay: Length of stay in days
        - discharge_instructions: Discharge instructions
        - medications_prescribed: Medications prescribed at discharge (list)
        - follow_up_instructions: Follow-up care instructions
        - patient_condition: Patient condition at discharge
        - complications: Any complications during stay (list)
        
        Data extraction guidelines:
        1. Standardize dates to YYYY-MM-DD format
        2. Clean and normalize names (proper case)
        3. Extract diagnoses with proper medical terminology
        4. Separate multiple procedures, medications, and diagnoses into lists
        5. Calculate length of stay if admission and discharge dates are available
        6. If multiple discharge summaries are in one document, separate them
        
        Return structured JSON data with the extracted fields. If a field cannot be found, use null.
        Be accurate and conservative - if you're unsure about a value, mark it as null rather than guessing.
        
        Note: Text extraction from PDFs has already been completed. Focus on data extraction and structuring.
        """
        
        logger.debug("🤖 Creating LlmAgent for Discharge Processing...")
        discharge_agent = LlmAgent(
            name="DischargeProcessingAgent",
            description="Extracts structured data from hospital discharge summaries",
            instruction=instruction,
            model=LiteLlm(
                model=f"ollama/{ollama_model}",
                timeout=600,  # 10 minutes timeout
                request_timeout=600,
                api_timeout=600
            ),
            output_key="discharge_data",
            output_schema=DischargeProcessingResult
        )
        
        logger.info(f"✅ Discharge Processing Agent created successfully with model: ollama/{ollama_model}")
        logger.debug(f"📄 Discharge Processing Agent config: name={discharge_agent.name}, output_key={discharge_agent.output_key}")
        logger.debug(f"📊 Output schema: {DischargeProcessingResult.__name__}")
        
        return discharge_agent
        
    except Exception as e:
        logger.error(f"❌ Failed to create Discharge Processing Agent: {e}")
        logger.exception("Full traceback:")
        raise
