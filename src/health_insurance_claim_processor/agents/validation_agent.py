"""Validation Agent for checking data consistency and completeness"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from ..utils.config import get_settings


def create_validation_agent() -> LlmAgent:
    """Create and configure the validation agent"""
    
    settings = get_settings()
    
    instruction = """
    You are a validation agent specialized in checking the consistency and completeness of medical insurance claim data.
    
    Your task is to analyze the extracted and processed data from all documents and perform the following validations:
    
    1. COMPLETENESS CHECK:
       - Verify all required document types are present (typically need at least bill and discharge summary)
       - Check if essential fields are populated in each document
       - Identify missing critical information
    
    2. CONSISTENCY CHECK:
       - Patient name consistency across all documents
       - Date consistency (admission date < discharge date < bill date)
       - Hospital/facility name consistency
       - Amount calculations (total = insurance + patient amounts)
       - Diagnosis consistency between bill and discharge summary
    
    3. DATA QUALITY CHECK:
       - Validate date formats and logical date sequences
       - Check for reasonable amount ranges
       - Verify medical terminology spelling and format
       - Flag potential OCR errors or misreadings
    
    4. BUSINESS RULES VALIDATION:
       - Check if services billed match treatment provided
       - Verify insurance coverage aligns with treatments
       - Flag unusually high amounts that might need review
       - Check for complete procedure coding if present
    
    5. DISCREPANCY DETECTION:
       - Patient information mismatches
       - Date inconsistencies
       - Amount discrepancies
       - Treatment vs billing misalignments
       - Missing critical documents for claim type
    
    Validation outputs:
    - missing_documents: List of missing required document types
    - discrepancies: List of specific data inconsistencies found
    - validation_score: Overall score (0-1) representing data quality
    - recommendations: Suggestions for resolving issues
    
    Scoring guidelines:
    - 0.9-1.0: Excellent - All data consistent, complete, no issues
    - 0.7-0.89: Good - Minor issues, mostly complete
    - 0.5-0.69: Fair - Some issues, may need clarification
    - 0.3-0.49: Poor - Significant issues, likely need additional documents
    - 0.0-0.29: Critical - Major issues, cannot process claim
    
    Return a structured validation report with findings and recommendations.
    """
    
    validation_agent = LlmAgent(
        name="ValidationAgent",
        description="Validates data consistency and completeness across all processed documents",
        instruction=instruction,
        model=LiteLlm(f"ollama/{settings.ollama_model}"),
        output_key="validation_results"
    )
    
    return validation_agent
    
    return validation_agent
