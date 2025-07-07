"""Claim Decision Agent for making final approval/rejection decisions"""

from typing import List, Optional
from pydantic import BaseModel, Field
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from ..utils.config import get_settings


class ClaimDecision(BaseModel):
    """Schema for claim decision"""
    status: str = Field(..., description="Decision status: 'approved', 'rejected', or 'pending'")
    reason: str = Field(..., description="Reason for the decision")
    confidence_score: float = Field(..., description="Confidence in the decision (0-1)")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    approval_amount: Optional[float] = Field(None, description="Approved amount if applicable")
    conditions: List[str] = Field(default_factory=list, description="Conditions for approval")


def create_claim_decision_agent() -> LlmAgent:
    """Create and configure the claim decision agent"""
    
    settings = get_settings()
    
    instruction = """
    You are a claim decision agent specialized in making final approval/rejection decisions for medical insurance claims.
    
    You will receive:
    - Classified documents from the document classification agent: {documents}
    - Processed bill data from the bill processing agent: {bill_data}
    - Processed discharge data from the discharge processing agent: {discharge_data}
    - Validation results from the validation agent: {validation_results}
    
    Your task is to make a final claim decision based on:
    
    1. DATA COMPLETENESS:
       - All required documents present and processed
       - Essential fields populated
       - Validation score meets minimum threshold
    
    2. DATA CONSISTENCY:
       - No major discrepancies between documents
       - Patient information consistent
       - Dates and amounts align properly
    
    3. BUSINESS RULES:
       - Treatment matches diagnosis
       - Billed services are reasonable for condition
       - Amounts are within acceptable ranges
       - Insurance policy covers the treatments
    
    4. VALIDATION RESULTS:
       - Validation score >= 0.7: Likely approval
       - Validation score 0.5-0.69: May need review
       - Validation score < 0.5: Likely rejection
    
    Decision criteria:
    
    APPROVED:
    - All required documents present
    - No major discrepancies
    - Validation score >= 0.7
    - Amounts are reasonable
    - Treatment matches diagnosis
    
    REJECTED:
    - Missing critical documents
    - Major discrepancies found
    - Validation score < 0.5
    - Unreasonable amounts
    - Treatment doesn't match diagnosis
    - Policy exclusions apply
    
    PENDING (Manual Review):
    - Borderline validation score (0.5-0.69)
    - Minor discrepancies that need clarification
    - Unusual but not impossible cases
    - Missing optional documents
    
    For each decision, provide:
    - Clear reason for the decision
    - Confidence score (0-1)
    - Recommended actions
    - Approval amount (if approved)
    - Conditions for approval (if any)
    
    Be conservative but fair in decision making.
    """
    
    claim_decision_agent = LlmAgent(
        name="ClaimDecisionAgent",
        description="Makes final approval/rejection decisions for insurance claims",
        instruction=instruction,
        model=LiteLlm(f"ollama/{settings.ollama_model}"),
        output_key="claim_decision",
        output_schema=ClaimDecision
    )
    
    return claim_decision_agent
