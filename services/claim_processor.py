"""Claim processing service that orchestrates the AI agents"""

import uuid
import time
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai.types import Content, Part
from fastapi import UploadFile

from ..agents.HealthInsuranceClaimProcessorAgent.workflow_agent import create_health_insurance_claim_processor_agent
 # Removed unused response models
from ..services.pdf_processor import PDFProcessor
from ..utils.logger import logger
from ..utils.config import get_settings


class ClaimProcessingService:
    """Service for processing insurance claims using AI agents"""
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.session_service = InMemorySessionService()
        self.settings = get_settings()
        
        # Create the main agent
        self.main_agent = create_health_insurance_claim_processor_agent()
        
        # Create runner
        self.runner = Runner(
            agent=self.main_agent,
            app_name="health_insurance_claim_processor",
            session_service=self.session_service
        )
    
    async def process_claim(self, files: List[UploadFile]) -> dict[str, Any]:
        """Process insurance claim documents through AI agent workflow and return JSON string or dict"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"🚀 Starting claim processing {request_id} with {len(files)} files")
        
        try:
            # Process PDF files and extract text
            processed_files = await self.pdf_processor.process_files(files)
            
            # Run agent workflow with timeout protection
            session_state = await asyncio.wait_for(
                self._run_workflow(request_id, processed_files),
                timeout=self.settings.agent_timeout
            )
            
            # Create final response with all agent outputs
            processing_time = time.time() - start_time
            response = self._create_final_response(request_id, session_state, processing_time)
            logger.info(f"✅ Completed claim processing {request_id} in {processing_time:.2f}s")
            return response
            
        except asyncio.TimeoutError:
            processing_time = time.time() - start_time
            logger.error(f"⏰ Workflow timeout after {self.settings.agent_timeout}s for {request_id}")
            return self._create_error_response(request_id, processing_time, "timeout")
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ Processing failed for {request_id}: {e}")
            return self._create_error_response(request_id, processing_time, str(e))
    
    async def _run_workflow(self, request_id: str, processed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run the agent workflow and return final session state"""
        user_id = f"claim_processor_{request_id}"
        
        # Create session
        await self.session_service.create_session(
            app_name="health_insurance_claim_processor",
            user_id=user_id,
            session_id=request_id
        )
        
        # Prepare agent input
        content = Content(
            role="user",
            parts=[Part.from_text(text=self._format_input_text(request_id, processed_files))]
        )
        
        # Run workflow and wait for completion
        logger.debug(f"🎬 Starting workflow execution for {request_id}")
        
        async for event in self.runner.run_async(
            user_id=user_id,
            session_id=request_id,
            new_message=content
        ):
            # Just log progress, let the workflow complete
            if hasattr(event, 'author'):
                logger.debug(f"🔄 {event.author} processing...")
        
        # Get final session state
        session = await self.session_service.get_session(
            app_name="health_insurance_claim_processor",
            user_id=user_id,
            session_id=request_id
        )
        
        final_state = session.state if session else {}
        logger.info(f"🎯 Workflow completed with outputs: {list(final_state.keys())}")
        return final_state
    
    def _format_input_text(self, request_id: str, processed_files: List[Dict[str, Any]]) -> str:
        """Format input text for agents"""
        content = f"Process insurance claim {request_id} with {len(processed_files)} documents:\n\n"
        
        for i, file_info in enumerate(processed_files, 1):
            content += f"=== Document {i}: {file_info['filename']} ===\n"
            if file_info['status'] == 'success':
                content += file_info['text_content']
            else:
                content += f"[Error: {file_info.get('error', 'Processing failed')}]"
            content += "\n\n"
        
        return content
    
    def _create_final_response(self, request_id: str, session_state: Dict[str, Any], processing_time: float) -> dict[str, Any]:
        """Return the final_report as a dict with all agent outputs, no extra/empty fields"""
        timestamp = datetime.now(timezone.utc)
        final_report = {
            "request_id": request_id,
            "processing_time": processing_time,
            "timestamp": timestamp.isoformat(),
            "workflow_status": "completed" if session_state else "no_outputs",
            "agent_outputs": {
                "documents": session_state.get("documents"),
                "bill_data": session_state.get("bill_data"),
                "discharge_data": session_state.get("discharge_data"),
                "claim_data": session_state.get("claim_data"),
                "validation_results": session_state.get("validation_results"),
                "claim_decision": session_state.get("claim_decision")
            },
            "raw_session_state": session_state
        }
        return final_report
    
    def _create_error_response(self, request_id: str, processing_time: float, error: str) -> dict[str, Any]:
        """Create error response as a dict matching the new output style"""
        timestamp = datetime.now(timezone.utc)
        error_report = {
            "request_id": request_id,
            "processing_time": processing_time,
            "timestamp": timestamp.isoformat(),
            "workflow_status": "error",
            "error": str(error),
            "agent_outputs": None,
            "raw_session_state": None,
            "recommended_actions": ["Contact support" if "timeout" in error else "Retry processing"]
        }
        return error_report
