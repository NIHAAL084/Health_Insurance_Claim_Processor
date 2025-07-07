"""Document Classification Agent for categorizing and separating extracted documents"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from ..utils.config import get_settings


class DocumentData(BaseModel):
    """Schema for individual document data"""
    type: str = Field(..., description="Document type")
    content: str = Field(..., description="Full text content of the document")
    filename: Optional[str] = Field(None, description="Original filename if available")
    confidence: float = Field(..., description="Confidence score for classification (0-1)")
    extracted_fields: Dict[str, Any] = Field(default_factory=dict, description="Key fields extracted based on document type")


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
    
    settings = get_settings()
    
    instruction = """
    You are a document classification and separation agent specialized in processing medical insurance documents.
    
    You will receive extracted text from multiple files. Your task is to:
    
    1. ANALYZE all the extracted text content from the files
    2. SEPARATE different document types that might be mixed together
    3. CLASSIFY each document into one of these categories:
       - "bill": Medical bills, invoices, statements
       - "discharge_summary": Hospital discharge summaries, treatment summaries
       - "id_card": Insurance ID cards, membership cards
       - "correspondence": Letters, emails, claim correspondence
       - "prescription": Prescription documents, medication lists
       - "lab_report": Laboratory reports, test results
       - "other": Documents that don't fit the above categories
    
    4. GROUP documents of the same type together
    5. EXTRACT key information for each document type
    
    Analysis criteria:
    - Bills: Look for amounts, itemized charges, hospital/clinic letterhead, invoice numbers, billing dates
    - Discharge summaries: Look for admission/discharge dates, diagnosis, treatment details, doctor signatures
    - ID cards: Look for member ID, policy numbers, insurance company logos, coverage details
    - Correspondence: Look for formal letter format, addresses, reference numbers
    - Prescriptions: Look for medication names, dosages, doctor prescriptions
    - Lab reports: Look for test results, reference ranges, laboratory letterhead
    
    For each document, extract relevant information based on its type:
    - Bills: hospital_name, total_amount, date_of_service, patient_name, bill_number
    - Discharge summaries: patient_name, diagnosis, admission_date, discharge_date, doctor_name
    - Others: Extract relevant fields based on document type
    
    Return a structured JSON with all documents classified, separated, and grouped by type.
    """
    
    classification_agent = LlmAgent(
        name="DocumentClassificationAgent",
        description="Classifies, separates, and groups medical documents from extracted text",
        instruction=instruction,
        model=LiteLlm(f"ollama/{settings.ollama_model}"),
        output_key="documents",
        output_schema=DocumentClassificationResult
    )
    
    return classification_agent
