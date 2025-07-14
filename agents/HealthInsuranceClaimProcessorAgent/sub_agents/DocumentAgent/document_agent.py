"""Document Classification Agent for categorizing and separating extracted documents"""

import os
from utils.config import get_ollama_url
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DocumentData(BaseModel):
    """Schema for individual document data after classification"""
    type: str = Field(..., description="Document type classification")
    content: str = Field(..., description="Comprehensive summary preserving ALL key information including patient details, amounts, dates, doctors, procedures, medications, and identifiers")
    filename: Optional[str] = Field(None, description="Original filename if available")
    confidence: float = Field(..., description="Confidence score for classification (0-1)")


class DocumentClassificationSummary(BaseModel):
    """Schema for classification summary"""
    total_documents: int = Field(..., description="Total number of documents processed")
    document_types_found: List[str] = Field(..., description="List of document types found")


class DocumentClassificationResult(BaseModel):
    """Schema for document classification result"""
    documents: List[DocumentData] = Field(..., description="List of classified documents")
    summary: DocumentClassificationSummary = Field(..., description="Summary of classification")


def create_document_classification_agent() -> LlmAgent:
    """Create and configure the document classification agent"""
    
    logger.info("📋 Creating Document Classification Agent...")
    
    try:
        ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
        ollama_url = get_ollama_url()
        logger.debug(f"📝 Document Classification Agent settings: ollama_model={ollama_model}, ollama_url={ollama_url}")
        
        instruction = """
        You are a document classification and separation agent specialized in processing medical insurance documents.
        
        You will receive pre-extracted text content from multiple PDF files that have already been processed 
        by a PDF text extraction service. Your ONLY task is to:
        
        1. ANALYZE all the extracted text content from the files
        2. SEPARATE different document types that might be mixed together
        3. CLASSIFY each document into one of these categories:
           - "bill": Medical bills, invoices, statements with charges and amounts
           - "discharge_summary": Hospital discharge summaries, treatment summaries with admission/discharge info
           - "id_card": Insurance ID cards, membership cards with policy details
           - "correspondence": Letters, emails, claim correspondence
           - "prescription": Prescription documents, medication lists from doctors
           - "lab_report": Laboratory reports, test results with values
           - "other": Documents that don't fit the above categories
        
        4. PRESERVE key information in content field - include ALL important details like:
           - Patient names, IDs, policy numbers
           - Amounts, charges, dates
           - Doctor names, hospital names
           - Medications, procedures, diagnoses
           - Any reference numbers or important identifiers
        
        Classification criteria:
        - Bills: Look for amounts, itemized charges, hospital/clinic letterhead, invoice numbers, billing dates
        - Discharge summaries: Look for admission/discharge dates, diagnosis, treatment details, doctor signatures
        - ID cards: Look for member ID, policy numbers, insurance company logos, coverage details
        - Correspondence: Look for formal letter format, addresses, reference numbers
        - Prescriptions: Look for medication names, dosages, doctor prescriptions
        - Lab reports: Look for test results, reference ranges, laboratory letterhead
        
        CRITICAL REQUIREMENTS:
        - The "content" field must contain a COMPREHENSIVE summary preserving ALL key information
        - DO NOT truncate or abbreviate critical details
        - Include patient info, amounts, dates, doctors, procedures, medications in full
        - Focus on accurate document type identification with high confidence scores
        - If unsure about classification, use "other" category
        
        Return a structured JSON with all documents classified, with COMPLETE content preservation.
        """
        
        logger.debug("🤖 Creating LlmAgent for Document Classification...")
        classification_agent = LlmAgent(
            name="DocumentAgent",
            description="Classifies, separates, and groups medical documents from extracted text",
            instruction=instruction,
            model=LiteLlm(
                model=f"ollama/{ollama_model}",
                base_url=ollama_url,
                timeout=600,  # 10 minutes timeout
                request_timeout=600,
                api_timeout=600
            ),
            output_key="documents",
            output_schema=DocumentClassificationResult,
            disallow_transfer_to_parent=True,
            disallow_transfer_to_peers=True
        )
        
        logger.info(f"✅ Document Classification Agent created successfully with model: ollama/{ollama_model}")
        logger.debug(f"📄 Document Classification Agent config: name={classification_agent.name}, output_key={classification_agent.output_key}")
        logger.debug(f"📊 Output schema: {DocumentClassificationResult.__name__}")
        
        return classification_agent
        
    except Exception as e:
        logger.error(f"❌ Failed to create Document Classification Agent: {e}")
        logger.exception("Full traceback:")
        raise
