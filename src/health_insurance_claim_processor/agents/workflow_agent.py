"""Main workflow agent that orchestrates the entire claim processing pipeline"""

from google.adk.agents import SequentialAgent, ParallelAgent, LlmAgent

from .ocr_agent import create_ocr_agent
from .document_agent import create_document_classification_agent
from .bill_agent import create_bill_processing_agent
from .discharge_agent import create_discharge_processing_agent
from .validation_agent import create_validation_agent
from .claim_decision_agent import create_claim_decision_agent


def create_health_insurance_claim_processor_agent() -> SequentialAgent:
    """Create the main orchestrating agent for the health insurance claim processing pipeline"""
    
    # Create individual agents
    ocr_agent = create_ocr_agent()
    document_classification_agent = create_document_classification_agent()
    bill_processing_agent = create_bill_processing_agent()
    discharge_processing_agent = create_discharge_processing_agent()
    validation_agent = create_validation_agent()
    claim_decision_agent = create_claim_decision_agent()
    
    # Create parallel processing agent for document-specific processing
    parallel_process_agent = ParallelAgent(
        name="ParallelDocumentProcessingAgent",
        description="Processes different document types in parallel using specialized agents",
        sub_agents=[bill_processing_agent, discharge_processing_agent]
    )
    
    # Create the main sequential workflow
    health_insurance_claim_processor_agent = SequentialAgent(
        name="HealthInsuranceClaimProcessorAgent",
        description="Main agent that orchestrates the complete claim processing workflow",
        sub_agents=[
            ocr_agent,                    # Extract text from PDFs
            document_classification_agent, # Classify document types
            parallel_process_agent,       # Process documents in parallel
            validation_agent,             # Validate consistency
            claim_decision_agent          # Make final decision
        ]
    )
    
    return health_insurance_claim_processor_agent
