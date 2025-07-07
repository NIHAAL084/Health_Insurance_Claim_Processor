"""Validation Agent for checking data consistency and completeness"""

from typing import List, Optional
from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from ..utils.config import get_settings


class ValidationResult(BaseModel):
    """Schema for validation result"""
    missing_documents: List[str] = Field(default_factory=list, description="List of missing document types")
    discrepancies: List[str] = Field(default_factory=list, description="List of data discrepancies found")
    validation_score: float = Field(..., description="Overall validation score (0-1)")
    data_quality_issues: List[str] = Field(default_factory=list, description="List of data quality issues")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")


def create_validation_agent() -> LlmAgent:
    """Create and configure the validation agent"""
    
    settings = get_settings()
    
    instruction = """
    You are a validation agent specialized in checking data consistency and completeness for medical insurance claims.
    
    You will receive:
    - Classified documents from the document classification agent: {documents}
    - Processed bill data from the bill processing agent: {bill_data}
    - Processed discharge data from the discharge processing agent: {discharge_data}
    
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
    
    4. BUSINESS LOGIC VALIDATION:
       - Service dates should be between admission and discharge dates
       - Total amounts should be reasonable
       - Length of stay should match date differences
       - Insurance claim numbers should be consistent
    
    Validation criteria:
    - Critical issues: Missing essential documents, major discrepancies
    - Warning issues: Minor inconsistencies, missing optional fields
    - Info issues: Recommendations for data improvement
    
    Calculate a validation score (0-1) based on:
    - 1.0: All documents present, no discrepancies
    - 0.8-0.9: Minor issues or missing optional data
    - 0.5-0.7: Some discrepancies or missing important data
    - 0.0-0.4: Major issues, missing critical documents
    
    Return structured validation results with specific issues and recommendations.
    """
    
    validation_agent = LlmAgent(
        name="ValidationAgent",
        description="Validates data consistency and completeness across processed documents",
        instruction=instruction,
        model=LiteLlm(f"ollama/{settings.ollama_model}"),
        output_key="validation_results",
        output_schema=ValidationResult
    )
    
    return validation_agent
