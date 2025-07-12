"""Claim Data Processing Agent for extracting structured data from ID cards, correspondence, prescriptions, and other documents"""

import os
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ClaimData(BaseModel):
    """Schema for claim-related document data extraction"""
    # General fields
    patient_name: Optional[str] = Field(None, description="Name of the patient/member")
    document_type: str = Field(..., description="Type of document (id_card, correspondence, prescription, lab_report, other)")
    
    # ID Card specific fields
    policy_number: Optional[str] = Field(None, description="Insurance policy number")
    member_id: Optional[str] = Field(None, description="Member identification number")
    insurance_company: Optional[str] = Field(None, description="Name of insurance company")
    coverage_type: Optional[str] = Field(None, description="Type of coverage (individual, family, etc.)")
    effective_date: Optional[str] = Field(None, description="Policy effective date")
    expiration_date: Optional[str] = Field(None, description="Policy expiration date")
    group_number: Optional[str] = Field(None, description="Group number for employer coverage")
    
    # Correspondence specific fields
    correspondence_date: Optional[str] = Field(None, description="Date of correspondence")
    reference_number: Optional[str] = Field(None, description="Reference or claim number")
    sender: Optional[str] = Field(None, description="Sender of correspondence")
    recipient: Optional[str] = Field(None, description="Recipient of correspondence")
    subject: Optional[str] = Field(None, description="Subject of correspondence")
    
    # Prescription specific fields
    prescribing_doctor: Optional[str] = Field(None, description="Doctor who prescribed medication")
    medications: Optional[List[str]] = Field(None, description="List of prescribed medications with dosages (drugs, pills, injections) - NOT procedures")
    pharmacy_name: Optional[str] = Field(None, description="Name of pharmacy")
    prescription_date: Optional[str] = Field(None, description="Date prescription was written")
    
    # Lab Report specific fields
    test_date: Optional[str] = Field(None, description="Date tests were performed")
    lab_name: Optional[str] = Field(None, description="Name of laboratory")
    test_results: Optional[List[str]] = Field(None, description="List of test results")
    ordering_physician: Optional[str] = Field(None, description="Doctor who ordered tests")
    
    # Common fields
    content: Optional[str] = Field(None, description="Original document content")


class ClaimDataProcessingResult(BaseModel):
    """Schema for claim data processing result"""
    processed_documents: List[ClaimData] = Field(..., description="List of processed documents")
    total_documents_processed: int = Field(..., description="Total number of documents processed")


def create_claim_data_agent() -> LlmAgent:
    """Create and configure the claim data processing agent"""
    
    logger.info("📋 Creating Claim Data Processing Agent...")
    
    try:
        ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
        logger.debug(f"📝 Claim Data Agent settings: ollama_model={ollama_model}")
        
        instruction = """
        You are a claim data processing agent specialized in extracting structured information from 
        insurance-related documents including ID cards, correspondence, prescriptions, lab reports, and other documents.
        
        You will receive classified documents from DocumentAgent in the {documents} output. Your task is to:
        
        1. FIRST, identify and process ONLY documents with types: "id_card", "correspondence", "prescription", "lab_report", "other"
        2. IGNORE documents with types "bill" or "discharge_summary" - those are handled by other specialized agents
        3. If NO relevant documents are found, return an empty list with total_documents_processed: 0
        
        For each relevant document, extract structured data based on its type:
        
        For ID CARDS (document_type == "id_card"):
        - Policy number, member ID, insurance company name
        - Coverage type, effective/expiration dates, group number
        - Patient/member name
        
        For CORRESPONDENCE (document_type == "correspondence"):
        - Date, reference numbers, sender/recipient
        - Subject, key content summary
        - Any claim-related information
        
        For PRESCRIPTIONS (document_type == "prescription"):
        - Prescribing doctor, list of medications with dosages
        - Pharmacy name, prescription date
        - Patient name
        - DO NOT include medical procedures - only medications
        
        For LAB REPORTS (document_type == "lab_report"):
        - Test date, laboratory name
        - Test results with values and reference ranges
        - Ordering physician
        - Patient name
        
        For OTHER documents (document_type == "other"):
        - Extract any relevant patient, insurance, or claim information
        - Identify document purpose and key details
        
        DOCUMENT TYPE VALIDATION:
        - ONLY process documents with the specified types listed above
        - Bills and discharge summaries should be IGNORED by this agent
        - Return empty results if no relevant documents are present
        
        MEDICATION vs PROCEDURE DISTINCTION:
        - Medications: drugs, pills, injections, prescriptions
        - Procedures: surgeries, treatments, therapies, consultations
        - Keep these categories separate and accurate
        
        Return structured JSON with extracted data for each relevant document.
        Focus on accuracy and completeness. If information is not clearly present, leave the field as null.
        """
        
        logger.debug("🤖 Creating LlmAgent for Claim Data Processing...")
        claim_data_agent = LlmAgent(
            name="ClaimDataAgent",
            description="Extracts structured data from ID cards, correspondence, prescriptions, lab reports, and other documents",
            instruction=instruction,
            model=LiteLlm(
                model=f"ollama/{ollama_model}",
                timeout=600,  # 10 minutes timeout
                request_timeout=600,
                api_timeout=600
            ),
            output_key="claim_data",
            output_schema=ClaimDataProcessingResult
        )
        
        logger.info(f"✅ Claim Data Processing Agent created successfully with model: ollama/{ollama_model}")
        logger.debug(f"📄 Claim Data Agent config: name={claim_data_agent.name}, output_key={claim_data_agent.output_key}")
        logger.debug(f"📊 Output schema: {ClaimDataProcessingResult.__name__}")
        
        return claim_data_agent
        
    except Exception as e:
        logger.error(f"❌ Failed to create Claim Data Processing Agent: {e}")
        logger.exception("Full traceback:")
        raise
