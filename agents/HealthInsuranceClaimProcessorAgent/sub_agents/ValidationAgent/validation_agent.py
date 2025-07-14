"""Validation Agent for checking data consistency and completeness"""

import os
from utils.config import get_ollama_url
import logging
from typing import List
from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ValidationResult(BaseModel):
    """Schema for validation result"""
    missing_documents: List[str] = Field(default_factory=list, description="List of missing document types")
    discrepancies: List[str] = Field(default_factory=list, description="List of data discrepancies found")
    validation_score: float = Field(..., description="Overall validation score (0-1)")
    data_quality_issues: List[str] = Field(default_factory=list, description="List of data quality issues including medication/procedure misclassification")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    agent_compliance_issues: List[str] = Field(default_factory=list, description="Issues with agents processing inappropriate document types")


def create_validation_agent() -> LlmAgent:
    """Create and configure the validation agent"""
    
    logger.info("✅ Creating Validation Agent...")
    
    try:
        ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
        ollama_url = get_ollama_url()
        logger.debug(f"📝 Validation Agent settings: ollama_model={ollama_model}, ollama_url={ollama_url}")
        
        instruction = """
        You are a validation agent specialized in checking data consistency and completeness for medical insurance claims.
        
        You will receive:
        - Classified documents from DocumentAgent: {documents}
        - Processed bill data from BillAgent: {bill_data}
        - Processed discharge data from DischargeAgent: {discharge_data}
        - Processed claim data from ClaimDataAgent: {claim_data}
        
        Your task is to validate the data and identify:
        
        1. MISSING DOCUMENTS:
           - Check if essential documents are present (bill, discharge summary)
           - Identify missing document types that are typically required
           - Flag incomplete document sets
        
        2. DATA DISCREPANCIES:
           - Patient name consistency across documents
           - Date consistency (admission, discharge, service dates)
           - Hospital name consistency
           - Doctor name consistency
           - Amount discrepancies between documents
           - Insurance information consistency
        
        3. DATA QUALITY ISSUES:
           - Missing required fields in bills (total amount, patient name, etc.)
           - Missing required fields in discharge summaries (diagnosis, dates, etc.)
           - Invalid date formats
           - Suspicious amounts or values
           - Incomplete information
           - Proper separation of medications vs medical procedures
        
        4. BUSINESS LOGIC VALIDATION:
           - Service dates should be between admission and discharge dates
           - Total amounts should be reasonable
           - Length of stay should match date differences
           - Insurance claim numbers should be consistent
           - Medications should be listed separately from procedures
           - Procedures should align with diagnoses
        
        CRITICAL VALIDATION POINTS:
        - Medications (drugs, pills, injections) should NOT be classified as procedures
        - Medical procedures (surgeries, treatments, therapies) should NOT be in medication lists
        - Each agent should only process their designated document types
        
        Validation criteria:
        - Critical issues: Missing essential documents, major discrepancies, medication/procedure confusion
        - Warning issues: Minor inconsistencies, missing optional fields
        - Info issues: Recommendations for data improvement
        
        Calculate a validation score (0-1) based on:
        - 1.0: All documents present, no discrepancies, proper categorization
        - 0.8-0.9: Minor issues or missing optional data
        - 0.5-0.7: Some discrepancies or missing important data
        - 0.0-0.4: Major issues, missing critical documents, classification errors
        
        Return structured validation results with specific issues and recommendations.
        """
        
        logger.debug("🤖 Creating LlmAgent for Validation...")
        validation_agent = LlmAgent(
            name="ValidationAgent",
            description="Validates data consistency and completeness across processed documents",
            instruction=instruction,
            model=LiteLlm(
                model=f"ollama/{ollama_model}",
                base_url=ollama_url,
                timeout=600,  # 10 minutes timeout
                request_timeout=600,
                api_timeout=600
            ),
            output_key="validation_results",
            output_schema=ValidationResult,
            disallow_transfer_to_parent=True,
            disallow_transfer_to_peers=True
        )
        
        logger.info(f"✅ Validation Agent created successfully with model: ollama/{ollama_model}")
        logger.debug(f"📄 Validation Agent config: name={validation_agent.name}, output_key={validation_agent.output_key}")
        logger.debug(f"📊 Output schema: {ValidationResult.__name__}")
        
        return validation_agent
        
    except Exception as e:
        logger.error(f"❌ Failed to create Validation Agent: {e}")
        logger.exception("Full traceback:")
        raise
