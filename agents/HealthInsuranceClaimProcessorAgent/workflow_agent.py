"""Main workflow agent that orchestrates the entire claim processing pipeline"""

import logging
from google.adk.agents import SequentialAgent, ParallelAgent

from .sub_agents.DocumentAgent.document_agent import create_document_classification_agent
from .sub_agents.BillProcessingAgent.bill_agent import create_bill_processing_agent
from .sub_agents.DischargeProcessingAgent.discharge_agent import create_discharge_processing_agent
from .sub_agents.ClaimDataAgent.claim_data_agent import create_claim_data_agent
from .sub_agents.ValidationAgent.validation_agent import create_validation_agent
from .sub_agents.ClaimDecisionAgent.claim_decision_agent import create_claim_decision_agent

# Set up module-level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_health_insurance_claim_processor_agent() -> SequentialAgent:
    """Create the main orchestrating agent for the health insurance claim processing pipeline"""
    
    logger.info("🏗️ Starting creation of Health Insurance Claim Processor Agent...")
    
    try:
        # Create individual agents with debug logging
        logger.debug(" Creating Document Classification Agent...")
        document_classification_agent = create_document_classification_agent()
        logger.info(f"✅ Document Classification Agent created: {document_classification_agent.name}")
        
        logger.debug("💰 Creating Bill Processing Agent...")
        bill_processing_agent = create_bill_processing_agent()
        logger.info(f"✅ Bill Processing Agent created: {bill_processing_agent.name}")
        
        logger.debug("🏥 Creating Discharge Processing Agent...")
        discharge_processing_agent = create_discharge_processing_agent()
        logger.info(f"✅ Discharge Processing Agent created: {discharge_processing_agent.name}")
        
        logger.debug("📋 Creating Claim Data Processing Agent...")
        claim_data_agent = create_claim_data_agent()
        logger.info(f"✅ Claim Data Processing Agent created: {claim_data_agent.name}")
        
        logger.debug("✅ Creating Validation Agent...")
        validation_agent = create_validation_agent()
        logger.info(f"✅ Validation Agent created: {validation_agent.name}")
        
        logger.debug("🎯 Creating Claim Decision Agent...")
        claim_decision_agent = create_claim_decision_agent()
        logger.info(f"✅ Claim Decision Agent created: {claim_decision_agent.name}")
        
        # Create parallel processing agent for document-specific processing
        logger.debug("⚡ Creating Parallel Processing Agent...")
        parallel_process_agent = ParallelAgent(
            name="ParallelDocumentProcessingAgent",
            description="Processes different document types in parallel using specialized agents",
            sub_agents=[bill_processing_agent, discharge_processing_agent, claim_data_agent]
        )
        logger.info(f"✅ Parallel Processing Agent created with {len(parallel_process_agent.sub_agents)} sub-agents")
        
        # Create the main sequential workflow (OCR removed - text extraction handled by PDF processor)
        logger.debug("🔄 Creating Main Sequential Workflow...")
        health_insurance_claim_processor_agent = SequentialAgent(
            name="HealthInsuranceClaimProcessorAgent",
            description="Main agent that orchestrates the complete claim processing workflow",
            sub_agents=[
                document_classification_agent, # Classify document types from extracted text
                parallel_process_agent,       # Process documents in parallel
                validation_agent,             # Validate consistency
                claim_decision_agent          # Make final decision
            ]
        )
        
        logger.info(f"✅ Main Sequential Workflow created with {len(health_insurance_claim_processor_agent.sub_agents)} sub-agents:")
        for i, agent in enumerate(health_insurance_claim_processor_agent.sub_agents, 1):
            logger.info(f"   {i}. {agent.name} - {agent.description}")
        
        logger.info("🎉 Health Insurance Claim Processor Agent created successfully!")
        return health_insurance_claim_processor_agent
        
    except Exception as e:
        logger.error(f"❌ Failed to create Health Insurance Claim Processor Agent: {e}")
        logger.exception("Full traceback:")
        raise
