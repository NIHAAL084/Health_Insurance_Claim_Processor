"""Claim processing service that orchestrates the AI agents"""

import uuid
import time
from datetime import datetime
from typing import List, Dict, Any

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai.types import Content, Part
from fastapi import UploadFile, HTTPException

from ..agents.HealthInsuranceClaimProcessorAgent.workflow_agent import create_health_insurance_claim_processor_agent
from ..models.response import ClaimProcessResponse, DocumentData, ValidationResult, ClaimDecision
from ..services.pdf_processor import PDFProcessor
from ..utils.logger import logger
from ..utils.config import get_settings


class ClaimProcessingService:
    """Service for processing insurance claims using AI agents"""
    
    def __init__(self):
        self.settings = get_settings()
        self.pdf_processor = PDFProcessor()
        self.session_service = InMemorySessionService()
        
        # Create the main agent
        self.main_agent = create_health_insurance_claim_processor_agent()
        
        # Create runner
        self.runner = Runner(
            agent=self.main_agent,
            app_name="health_insurance_claim_processor",
            session_service=self.session_service
        )
    
    async def process_claim(self, files: List[UploadFile]) -> ClaimProcessResponse:
        """Process a complete insurance claim with multiple documents"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting claim processing for request {request_id} with {len(files)} files")
        
        try:
            # Step 1: Process PDF files and extract text
            processed_files = await self.pdf_processor.process_files(files)
            
            # Step 2: Prepare input for AI agents
            input_data = {
                "request_id": request_id,
                "files": processed_files,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Step 3: Create agent session
            session = await self.session_service.create_session(
                app_name="health_insurance_claim_processor",
                user_id=f"claim_processor_{request_id}",
                session_id=request_id
            )
            
            # Step 4: Run the agent workflow
            agent_results = await self._run_agent_workflow(
                input_data=input_data,
                user_id=f"claim_processor_{request_id}",
                session_id=request_id
            )
            
            # Step 5: Parse and structure the response
            response = await self._parse_agent_results(
                agent_results=agent_results,
                request_id=request_id,
                processing_time=time.time() - start_time
            )
            
            logger.info(f"Successfully processed claim {request_id} in {response.processing_time:.2f} seconds")
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing claim {request_id}: {e}")
            
            # Return error response in the expected format
            return ClaimProcessResponse(
                request_id=request_id,
                processing_time=processing_time,
                timestamp=datetime.utcnow(),
                documents=[],
                validation=ValidationResult(
                    missing_documents=["Processing failed"],
                    discrepancies=[f"Error: {str(e)}"],
                    validation_score=0.0
                ),
                claim_decision=ClaimDecision(
                    status="rejected",
                    reason=f"Processing error: {str(e)}",
                    confidence_score=1.0,
                    recommended_actions=["Contact support for assistance"]
                )
            )
    
    async def _run_agent_workflow(self, input_data: Dict[str, Any], user_id: str, session_id: str) -> Dict[str, Any]:
        """Run the AI agent workflow and collect results"""
        
        # Prepare the input message for the agent
        content = Content(
            role="user",
            parts=[Part.from_text(
                text=f"""
                Process the following insurance claim documents:
                
                Request ID: {input_data['request_id']}
                Number of files: {len(input_data['files'])}
                
                Files and content:
                {self._format_files_for_agent(input_data['files'])}
                
                Please extract text, classify documents, process them with appropriate agents, 
                validate the data, and make a final claim decision.
                """
            )]
        )
        
        # Run the agent and collect all results
        agent_results = {}
        final_response = None
        
        try:
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                # Collect results from different agents
                if hasattr(event, 'author') and event.author:
                    agent_results[event.author] = event
                
                # Capture the final response
                if event.is_final_response():
                    final_response = event
                    break
            
            # Get session state which contains intermediate results
            session = await self.session_service.get_session(
                app_name="health_insurance_claim_processor",
                user_id=user_id,
                session_id=session_id
            )
            
            # Combine final response with session state
            combined_results = {
                "final_response": final_response,
                "session_state": session.state if session else {},
                "agent_events": agent_results
            }
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Error running agent workflow: {e}")
            raise HTTPException(status_code=500, detail=f"Agent workflow failed: {str(e)}")
    
    def _format_files_for_agent(self, files: List[Dict[str, Any]]) -> str:
        """Format file information for agent input"""
        formatted = ""
        for i, file_info in enumerate(files, 1):
            formatted += f"\\n=== File {i}: {file_info['filename']} ===\\n"
            if file_info['status'] == 'success':
                formatted += file_info['text_content']
            else:
                formatted += f"[Error processing file: {file_info.get('error', 'Unknown error')}]"
            formatted += "\\n"
        return formatted
    
    async def _parse_agent_results(
        self, 
        agent_results: Dict[str, Any], 
        request_id: str, 
        processing_time: float
    ) -> ClaimProcessResponse:
        """Parse agent results into structured response format"""
        
        try:
            # Extract results from session state or final response
            session_state = agent_results.get("session_state", {})
            final_response = agent_results.get("final_response")
            
            # Parse document data (from parallel processing agents)
            documents = self._parse_document_data(session_state)
            
            # Parse validation results
            validation = self._parse_validation_results(session_state)
            
            # Parse claim decision
            claim_decision = self._parse_claim_decision(session_state, final_response)
            
            return ClaimProcessResponse(
                request_id=request_id,
                processing_time=processing_time,
                timestamp=datetime.utcnow(),
                documents=documents,
                validation=validation,
                claim_decision=claim_decision
            )
            
        except Exception as e:
            logger.error(f"Error parsing agent results: {e}")
            
            # Return fallback response
            return ClaimProcessResponse(
                request_id=request_id,
                processing_time=processing_time,
                timestamp=datetime.utcnow(),
                documents=[],
                validation=ValidationResult(
                    missing_documents=["Result parsing failed"],
                    discrepancies=[f"Parsing error: {str(e)}"],
                    validation_score=0.0
                ),
                claim_decision=ClaimDecision(
                    status="pending",
                    reason="Unable to parse agent results - manual review required",
                    confidence_score=0.0,
                    recommended_actions=["Manual review required"]
                )
            )
    
    def _parse_document_data(self, session_state: Dict[str, Any]) -> List[DocumentData]:
        """Parse document data from agent results"""
        documents = []
        
        # Try to extract from various possible keys
        bill_data = session_state.get("bill_data")
        discharge_data = session_state.get("discharge_data")
        document_classification = session_state.get("document_classification")
        
        # Create document entries based on available data
        if bill_data:
            documents.append(DocumentData(
                type="bill",
                content=str(bill_data),
                **self._extract_bill_fields(bill_data)
            ))
        
        if discharge_data:
            documents.append(DocumentData(
                type="discharge_summary",
                content=str(discharge_data),
                **self._extract_discharge_fields(discharge_data)
            ))
        
        return documents
    
    def _extract_bill_fields(self, bill_data: Any) -> Dict[str, Any]:
        """Extract bill-specific fields from agent output"""
        # This would parse the structured output from the bill agent
        # For now, return empty dict - would need to implement proper parsing
        return {}
    
    def _extract_discharge_fields(self, discharge_data: Any) -> Dict[str, Any]:
        """Extract discharge-specific fields from agent output"""
        # This would parse the structured output from the discharge agent
        # For now, return empty dict - would need to implement proper parsing
        return {}
    
    def _parse_validation_results(self, session_state: Dict[str, Any]) -> ValidationResult:
        """Parse validation results from agent output"""
        validation_data = session_state.get("validation_results")
        
        if validation_data:
            # Parse validation results - would need proper implementation
            return ValidationResult(
                missing_documents=[],
                discrepancies=[],
                validation_score=0.8  # Default for now
            )
        
        return ValidationResult()
    
    def _parse_claim_decision(self, session_state: Dict[str, Any], final_response: Any) -> ClaimDecision:
        """Parse claim decision from agent output"""
        decision_data = session_state.get("claim_decision")
        
        if decision_data:
            # Parse decision data - would need proper implementation
            return ClaimDecision(
                status="approved",  # Default for now
                reason="Processed successfully",
                confidence_score=0.8
            )
        
        # Fallback decision
        return ClaimDecision(
            status="pending",
            reason="Manual review required",
            confidence_score=0.5
        )