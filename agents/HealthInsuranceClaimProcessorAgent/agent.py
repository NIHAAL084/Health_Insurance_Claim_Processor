"""Root agent entry point for Google ADK Web integration"""

from .workflow_agent import create_health_insurance_claim_processor_agent

# This is the main agent that ADK Web will look for
root_agent = create_health_insurance_claim_processor_agent()
