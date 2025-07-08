# Backend Testing Guide

## Overview

The Health Insurance Claim Processor backend has been updated to work with both ADK Web and standalone backend testing.

## Key Changes Made

### 1. Agent Directory Structure (Google ADK Compliant)

- All agents are now under `src/health_insurance_claim_processor/agents/HealthInsuranceClaimProcessorAgent/`
- Sub-agents are in `sub_agents/` subdirectories
- Added `root_agent.py` for ADK Web compatibility

### 2. Environment Variable Configuration

- Agents now use `OLLAMA_MODEL` environment variable instead of config imports
- Main application sets the environment variable from settings during startup

### 3. Removed OCR Agent

- Removed redundant OCR agent since PyPDF is used for text extraction
- Workflow now starts directly with document classification

## Testing

### Backend Testing (without ADK Web)

```bash
# Run the test script
python3 test_backend.py

# Or manually test imports
python3 -c "
import os
os.environ['OLLAMA_MODEL'] = 'llama3.2:3b'
from src.health_insurance_claim_processor.services.claim_processor import ClaimProcessingService
service = ClaimProcessingService()
print('Backend is ready!')
"
```

### ADK Web Testing

1. Navigate to the agent directory: `src/health_insurance_claim_processor/agents/HealthInsuranceClaimProcessorAgent/`
2. Ensure `.env` file contains `OLLAMA_MODEL=llama3.2:3b`
3. Use ADK Web to load the agent directory

## Agent Workflow

1. **DocumentAgent** - Classifies and separates medical documents
2. **Parallel Processing**:
   - **BillProcessingAgent** - Processes medical bills
   - **DischargeProcessingAgent** - Processes discharge summaries
3. **ValidationAgent** - Validates data consistency and completeness
4. **ClaimDecisionAgent** - Makes final claim approval/rejection decisions

## Files Updated

- `src/health_insurance_claim_processor/services/claim_processor.py` - Updated to use new agent structure and environment variables
- `src/health_insurance_claim_processor/main.py` - Sets OLLAMA_MODEL environment variable during startup
- `src/health_insurance_claim_processor/agents/HealthInsuranceClaimProcessorAgent/root_agent.py` - Added for ADK Web compatibility
- All agent files updated to use environment variables instead of settings imports

## Status

✅ Backend is ready for testing  
✅ ADK Web integration working  
✅ All agents using environment variables  
✅ Google ADK compliant structure  
