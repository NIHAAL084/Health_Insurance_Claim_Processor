"""Claim processing service that orchestrates the AI agents"""

import os
import uuid
import time
import asyncio
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
            
            # Step 4: Run the agent workflow with timeout
            try:
                # Use a timeout wrapper to prevent infinite waiting
                agent_results = await asyncio.wait_for(
                    self._run_agent_workflow(
                        input_data=input_data,
                        user_id=f"claim_processor_{request_id}",
                        session_id=request_id
                    ),
                    timeout=self.settings.agent_timeout  # From config.py (default 300s)
                )
            except asyncio.TimeoutError:
                logger.error(f"Agent workflow timed out after {self.settings.agent_timeout} seconds for request {request_id}")
                raise HTTPException(
                    status_code=504, 
                    detail=f"Agent processing timed out after {self.settings.agent_timeout} seconds. Please try again or contact support."
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
        event_count = 0
        final_events = []
        
        try:
            logger.debug("🎬 Starting agent workflow execution...")
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                event_count += 1
                logger.debug(f"🎬 Event {event_count}: {type(event).__name__} from {getattr(event, 'author', 'unknown')}")
                
                # Create unique agent identifier using author and agent_path
                agent_id = getattr(event, 'author', 'unknown')
                agent_path = getattr(event, 'agent_path', None)
                
                # Use agent_path for better identification if available
                if agent_path:
                    unique_agent_id = f"{agent_id}:{agent_path}"
                else:
                    unique_agent_id = agent_id
                
                # Collect results from different agents
                if hasattr(event, 'author') and event.author:
                    agent_results[unique_agent_id] = event
                    logger.debug(f"🎬 Collected result from agent: {unique_agent_id}")
                
                # Log event details for debugging
                if hasattr(event, 'actions') and event.actions and hasattr(event.actions, 'state_delta'):
                    logger.debug(f"🎬 State delta from {unique_agent_id}: {list(event.actions.state_delta.keys()) if event.actions.state_delta else 'None'}")
                
                # Collect final responses instead of breaking immediately
                if hasattr(event, 'is_final_response') and event.is_final_response():
                    final_events.append(event)
                    logger.debug(f"🎬 Final response captured from: {unique_agent_id}")
                    
                    # Set the main final response (could be the last one or most relevant one)
                    final_response = event
            
            logger.debug(f"🎬 Agent workflow completed. Total events: {event_count}, Agent results: {list(agent_results.keys())}, Final events: {len(final_events)}")
            
            # Get session state which contains intermediate results  
            session = await self.session_service.get_session(
                app_name="health_insurance_claim_processor",
                user_id=user_id,
                session_id=session_id
            )
            
            # Debug: Log complete session state
            session_state = session.state if session else {}
            logger.info("=" * 80)
            logger.info("🔍 COMPLETE AGENTIC SYSTEM FINAL STATE:")
            logger.info("=" * 80)
            logger.info(f"🔍 Session state keys: {list(session_state.keys())}")
            
            # Log each key's content in detail
            for key, value in session_state.items():
                logger.info(f"🔍 [{key}] Type: {type(value)}")
                logger.info(f"🔍 [{key}] Content: {value}")
                logger.info("-" * 50)
            
            # Log agent events
            logger.info(f"🔍 Agent events collected: {list(agent_results.keys())}")
            for agent_name, event in agent_results.items():
                logger.info(f"🔍 Agent [{agent_name}] Event type: {type(event)}")
                if hasattr(event, 'actions') and event.actions and hasattr(event.actions, 'state_delta'):
                    logger.info(f"🔍 Agent [{agent_name}] State delta: {event.actions.state_delta}")
                if hasattr(event, 'content'):
                    logger.info(f"🔍 Agent [{agent_name}] Content: {event.content}")
                logger.info("-" * 50)
            
            logger.info("=" * 80)
            
            # Combine final response with session state
            combined_results = {
                "final_response": final_response,
                "final_events": final_events,
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
            
            # Debug: Log the structure of agent_results
            logger.debug(f"🔍 Agent results keys: {list(agent_results.keys())}")
            logger.debug(f"🔍 Final response type: {type(final_response)}")
            logger.debug(f"🔍 Final response: {final_response}")
            
            # Debug: Log session state contents
            logger.debug(f"🔍 Session state keys: {list(session_state.keys())}")
            for key, value in session_state.items():
                logger.debug(f"🔍 Session state[{key}]: {type(value)} - {str(value)[:200]}...")
            
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
        
        # Debug: Log what's actually in session_state
        logger.debug(f"🔍 Session state keys: {list(session_state.keys())}")
        logger.debug(f"🔍 Session state content: {session_state}")
        
        # NEW APPROACH: Parse results from specialized agents using correct output keys
        # 1. Get results from BillProcessingAgent (output_key="bill_data")
        bill_results = session_state.get("bill_data")
        if bill_results:
            logger.debug(f"🔍 Found bill processing results: {bill_results}")
            documents.extend(self._parse_bill_results(bill_results))
        else:
            logger.debug("🔍 No bill_data found in session state")
        
        # 2. Get results from DischargeProcessingAgent (output_key="discharge_data")
        discharge_results = session_state.get("discharge_data")
        if discharge_results:
            logger.debug(f"🔍 Found discharge processing results: {discharge_results}")
            documents.extend(self._parse_discharge_results(discharge_results))
        else:
            logger.debug("🔍 No discharge_data found in session state")
        
        # 3. Get results from ClaimDataAgent (output_key="claim_data")
        claim_data_results = session_state.get("claim_data")
        if claim_data_results:
            logger.debug(f"🔍 Found claim data processing results: {claim_data_results}")
            documents.extend(self._parse_claim_data_results(claim_data_results))
        else:
            logger.debug("🔍 No claim_data found in session state")
        
        # 4. Get classification results from DocumentAgent (output_key="documents")
        classification_results = session_state.get("documents")
        if classification_results and not documents:
            # Only use classification results if we don't have processed results from specialized agents
            logger.debug(f"🔍 Found document classification results: {classification_results}")
            documents.extend(self._parse_classification_results(classification_results))
        elif classification_results:
            logger.debug(f"🔍 Found document classification results but already have {len(documents)} processed documents")
        else:
            logger.debug("🔍 No documents found in session state")
        
        # FALLBACK: Try legacy parsing if no new results found
        if not documents:
            logger.debug("🔍 No new agent results found, trying legacy parsing...")
            documents.extend(self._parse_legacy_results(session_state))
        
        logger.debug(f"🔍 Final documents count: {len(documents)}")
        return documents
    
    def _create_document_from_info(self, doc_info: Any) -> DocumentData:
        """Create DocumentData object from agent output info"""
        if isinstance(doc_info, dict):
            # Extract structured fields if available
            extracted_fields = doc_info.get("extracted_fields", {})
            
            # Initialize document data with default values
            doc_data = DocumentData(
                type=doc_info.get("type", "unknown"),
                content=str(doc_info.get("content", doc_info)),
                hospital_name=None,
                patient_name=None,
                date_of_service=None,
                total_amount=None,
                insurance_amount=None,
                patient_amount=None,
                bill_number=None,
                diagnosis=None,
                admission_date=None,
                discharge_date=None,
                treatment_summary=None,
                doctor_name=None,
                policy_number=None,
                member_id=None,
                insurance_company=None,
                coverage_type=None,
                extracted_data=extracted_fields if extracted_fields else None
            )
            
            # Map extracted fields to document data fields
            if extracted_fields:
                logger.debug(f"🔍 Extracted fields found: {extracted_fields}")
                
                # Map common fields (handling various possible field names)
                if "Insured Name" in extracted_fields:
                    doc_data.patient_name = extracted_fields["Insured Name"]
                elif "patient_name" in extracted_fields:
                    doc_data.patient_name = extracted_fields["patient_name"]
                
                if "Policy Number" in extracted_fields:
                    doc_data.policy_number = extracted_fields["Policy Number"]
                elif "policy_number" in extracted_fields:
                    doc_data.policy_number = extracted_fields["policy_number"]
                
                if "Insurance Company" in extracted_fields:
                    doc_data.insurance_company = extracted_fields["Insurance Company"]
                elif "insurance_company" in extracted_fields:
                    doc_data.insurance_company = extracted_fields["insurance_company"]
                
                if "Treating Hospital" in extracted_fields:
                    doc_data.hospital_name = extracted_fields["Treating Hospital"]
                elif "hospital_name" in extracted_fields:
                    doc_data.hospital_name = extracted_fields["hospital_name"]
                
                if "Diagnosis" in extracted_fields:
                    doc_data.diagnosis = extracted_fields["Diagnosis"]
                elif "diagnosis_code" in extracted_fields:
                    doc_data.diagnosis = extracted_fields["diagnosis_code"]
                
                if "Admitted Date" in extracted_fields:
                    doc_data.admission_date = extracted_fields["Admitted Date"]
                elif "admission_date" in extracted_fields:
                    doc_data.admission_date = extracted_fields["admission_date"]
                
                if "Discharged Date" in extracted_fields:
                    doc_data.discharge_date = extracted_fields["Discharged Date"]
                elif "discharge_date" in extracted_fields:
                    doc_data.discharge_date = extracted_fields["discharge_date"]
                
                if "Claim Amount" in extracted_fields:
                    # Try to parse amount as float
                    try:
                        amount_str = str(extracted_fields["Claim Amount"]).replace(",", "").replace("INR", "").replace("/-", "").strip()
                        doc_data.total_amount = float(amount_str)
                    except (ValueError, TypeError):
                        logger.debug(f"Could not parse amount: {extracted_fields['Claim Amount']}")
                elif "claim_amount" in extracted_fields:
                    # Try to parse amount as float
                    try:
                        amount_str = str(extracted_fields["claim_amount"]).replace(",", "").replace("INR", "").replace("/-", "").strip()
                        doc_data.total_amount = float(amount_str)
                    except (ValueError, TypeError):
                        logger.debug(f"Could not parse amount: {extracted_fields['claim_amount']}")
                elif "total_amount" in extracted_fields and extracted_fields["total_amount"]:
                    try:
                        doc_data.total_amount = float(extracted_fields["total_amount"])
                    except (ValueError, TypeError):
                        logger.debug(f"Could not parse amount: {extracted_fields['total_amount']}")
                
                if "Procedure" in extracted_fields:
                    doc_data.treatment_summary = extracted_fields["Procedure"]
                elif "treatment_details" in extracted_fields:
                    doc_data.treatment_summary = str(extracted_fields["treatment_details"])
                
                # Additional field mappings
                if "doctor_name" in extracted_fields:
                    doc_data.doctor_name = extracted_fields["doctor_name"]
                if "date_of_service" in extracted_fields:
                    doc_data.date_of_service = extracted_fields["date_of_service"]
            
            return doc_data
        else:
            return DocumentData(
                type="processed_document",
                content=str(doc_info),
                hospital_name=None,
                patient_name=None,
                date_of_service=None,
                total_amount=None,
                insurance_amount=None,
                patient_amount=None,
                bill_number=None,
                diagnosis=None,
                admission_date=None,
                discharge_date=None,
                treatment_summary=None,
                doctor_name=None,
                policy_number=None,
                member_id=None,
                insurance_company=None,
                coverage_type=None,
                extracted_data=None
            )
    
    def _parse_string_content(self, content_str: str) -> List[DocumentData]:
        """Parse structured data from string content, returning a list of documents"""
        import json
        import ast
        
        documents = []
        
        try:
            # Try to parse as JSON first
            if content_str.strip().startswith('[') or content_str.strip().startswith('{'):
                try:
                    parsed_data = json.loads(content_str)
                    logger.debug(f"🔍 Successfully parsed JSON content: {parsed_data}")
                    
                    if isinstance(parsed_data, list):
                        # Process each document in the list
                        for doc_info in parsed_data:
                            documents.append(self._create_document_from_info(doc_info))
                    elif isinstance(parsed_data, dict):
                        documents.append(self._create_document_from_info(parsed_data))
                        
                except json.JSONDecodeError:
                    # Try ast.literal_eval for Python-like strings
                    try:
                        parsed_data = ast.literal_eval(content_str)
                        logger.debug(f"🔍 Successfully parsed AST content: {parsed_data}")
                        
                        if isinstance(parsed_data, list):
                            # Process each document in the list
                            for doc_info in parsed_data:
                                documents.append(self._create_document_from_info(doc_info))
                        elif isinstance(parsed_data, dict):
                            documents.append(self._create_document_from_info(parsed_data))
                    except (ValueError, SyntaxError):
                        logger.debug("🔍 Could not parse as JSON or AST, treating as plain text")
                        
        except Exception as e:
            logger.debug(f"🔍 Error parsing string content: {e}")
        
        # If no documents were parsed, return as plain text document
        if not documents:
            documents.append(DocumentData(
                type="processed_document",
                content=content_str,
                hospital_name=None,
                patient_name=None,
                date_of_service=None,
                total_amount=None,
                insurance_amount=None,
                patient_amount=None,
                bill_number=None,
                diagnosis=None,
                admission_date=None,
                discharge_date=None,
                treatment_summary=None,
                doctor_name=None,
                policy_number=None,
                member_id=None,
                insurance_company=None,
                coverage_type=None,
                extracted_data={"parsing_failed": True}
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
        # Try multiple possible keys where validation results might be stored
        validation_data = (
            session_state.get("validation_results") or 
            session_state.get("validation") or 
            session_state.get("ValidationAgent")
        )
        
        logger.debug(f"🔍 Validation data: {validation_data}")
        
        if validation_data:
            # Parse validation results - basic implementation
            if isinstance(validation_data, dict):
                return ValidationResult(
                    missing_documents=validation_data.get("missing_documents", []),
                    discrepancies=validation_data.get("discrepancies", []),
                    validation_score=validation_data.get("validation_score", 0.8)
                )
            else:
                # If it's a string, try to extract basic info
                validation_text = str(validation_data)
                return ValidationResult(
                    missing_documents=[],
                    discrepancies=[] if "valid" in validation_text.lower() else ["Validation issues detected"],
                    validation_score=0.8 if "valid" in validation_text.lower() else 0.4
                )
        
        # Default validation when no explicit validation data found
        return ValidationResult(
            missing_documents=[],
            discrepancies=[],
            validation_score=0.7  # Moderate confidence when no validation data
        )
    
    def _parse_claim_decision(self, session_state: Dict[str, Any], final_response: Any) -> ClaimDecision:
        """Parse claim decision from agent output"""
        # Try multiple possible keys where claim decision might be stored
        decision_data = (
            session_state.get("claim_decision") or 
            session_state.get("decision") or 
            session_state.get("ClaimDecisionAgent") or
            session_state.get("final_decision")
        )
        
        logger.debug(f"🔍 Decision data: {decision_data}")
        logger.debug(f"🔍 Final response: {final_response}")
        
        if decision_data:
            # Parse decision data
            if isinstance(decision_data, dict):
                return ClaimDecision(
                    status=str(decision_data.get("status", "pending")),
                    reason=str(decision_data.get("reason", "Processed by agent")),
                    confidence_score=float(decision_data.get("confidence_score", 0.8)),
                    recommended_actions=decision_data.get("recommended_actions", ["Review processed claim"])
                )
            else:
                # Try to extract basic decision from string
                decision_text = str(decision_data).lower()
                if "approve" in decision_text:
                    status = "approved"
                    reason = "Claim approved by automated review"
                elif "reject" in decision_text or "deny" in decision_text:
                    status = "rejected"
                    reason = "Claim rejected by automated review"
                else:
                    status = "pending"
                    reason = "Manual review required"
                
                return ClaimDecision(
                    status=status,
                    reason=reason,
                    confidence_score=0.7,
                    recommended_actions=["Review claim details"]
                )
        
        # Check if final_response contains decision info
        if final_response and hasattr(final_response, 'content'):
            response_text = str(final_response.content).lower()
            if "approve" in response_text:
                return ClaimDecision(
                    status="approved",
                    reason="Claim approved based on document analysis",
                    confidence_score=0.8,
                    recommended_actions=["Process claim for payment"]
                )
            elif "reject" in response_text or "deny" in response_text:
                return ClaimDecision(
                    status="rejected",
                    reason="Claim rejected based on document analysis",
                    confidence_score=0.8,
                    recommended_actions=["Notify claimant of rejection"]
                )
        
        # Fallback decision
        return ClaimDecision(
            status="pending",
            reason="Automated processing completed - manual review recommended",
            confidence_score=0.6,
            recommended_actions=["Manual review by claim specialist required"]
        )
    
    def _parse_bill_results(self, bill_results: Any) -> List[DocumentData]:
        """Parse results from BillProcessingAgent"""
        documents = []
        
        try:
            # Handle different possible formats
            if isinstance(bill_results, str):
                # Try to parse string content
                parsed_docs = self._parse_string_content(bill_results)
                documents.extend(parsed_docs)
            elif isinstance(bill_results, dict):
                # Extract processed_bills from result structure
                processed_bills = bill_results.get("processed_bills", [])
                for bill_data in processed_bills:
                    documents.append(self._create_bill_document(bill_data))
            elif isinstance(bill_results, list):
                # Direct list of bill data
                for bill_data in bill_results:
                    documents.append(self._create_bill_document(bill_data))
        except Exception as e:
            logger.debug(f"Error parsing bill results: {e}")
        
        return documents
    
    def _parse_discharge_results(self, discharge_results: Any) -> List[DocumentData]:
        """Parse results from DischargeProcessingAgent"""
        documents = []
        
        try:
            # Handle different possible formats
            if isinstance(discharge_results, str):
                # Try to parse string content
                parsed_docs = self._parse_string_content(discharge_results)
                documents.extend(parsed_docs)
            elif isinstance(discharge_results, dict):
                # Extract processed_discharge_summaries from result structure
                processed_summaries = discharge_results.get("processed_discharge_summaries", [])
                for discharge_data in processed_summaries:
                    documents.append(self._create_discharge_document(discharge_data))
            elif isinstance(discharge_results, list):
                # Direct list of discharge data
                for discharge_data in discharge_results:
                    documents.append(self._create_discharge_document(discharge_data))
        except Exception as e:
            logger.debug(f"Error parsing discharge results: {e}")
        
        return documents
    
    def _parse_claim_data_results(self, claim_data_results: Any) -> List[DocumentData]:
        """Parse results from ClaimDataAgent"""
        documents = []
        
        try:
            # Handle different possible formats
            if isinstance(claim_data_results, str):
                # Try to parse string content
                parsed_docs = self._parse_string_content(claim_data_results)
                documents.extend(parsed_docs)
            elif isinstance(claim_data_results, dict):
                # Extract processed_documents from result structure
                processed_docs = claim_data_results.get("processed_documents", [])
                for claim_data in processed_docs:
                    documents.append(self._create_claim_data_document(claim_data))
            elif isinstance(claim_data_results, list):
                # Direct list of claim data
                for claim_data in claim_data_results:
                    documents.append(self._create_claim_data_document(claim_data))
        except Exception as e:
            logger.debug(f"Error parsing claim data results: {e}")
        
        return documents
    
    def _parse_classification_results(self, classification_results: Any) -> List[DocumentData]:
        """Parse results from DocumentAgent (classification only)"""
        documents = []
        
        try:
            # Handle different possible formats
            if isinstance(classification_results, str):
                # Try to parse string content
                parsed_docs = self._parse_string_content(classification_results)
                documents.extend(parsed_docs)
            elif isinstance(classification_results, dict):
                # Extract documents from classification result structure
                classified_docs = classification_results.get("documents", [])
                for doc_data in classified_docs:
                    documents.append(self._create_classification_document(doc_data))
            elif isinstance(classification_results, list):
                # Direct list of classified documents
                for doc_data in classification_results:
                    documents.append(self._create_classification_document(doc_data))
        except Exception as e:
            logger.debug(f"Error parsing classification results: {e}")
        
        return documents
    
    def _parse_legacy_results(self, session_state: Dict[str, Any]) -> List[DocumentData]:
        """Parse legacy/fallback results from session state"""
        documents = []
        
        # Try to extract from any other keys that might contain agent results
        for key, value in session_state.items():
            if key not in ['validation_results', 'claim_decision'] and value:
                logger.debug(f"🔍 Found potential legacy document data in key '{key}': {type(value)}")
                documents.append(DocumentData(
                    type=key,
                    content=str(value),
                    hospital_name=None,
                    patient_name=None,
                    date_of_service=None,
                    total_amount=None,
                    insurance_amount=None,
                    patient_amount=None,
                    bill_number=None,
                    diagnosis=None,
                    admission_date=None,
                    discharge_date=None,
                    treatment_summary=None,
                    doctor_name=None,
                    policy_number=None,
                    member_id=None,
                    insurance_company=None,
                    coverage_type=None,
                    extracted_data={"source_key": key, "processed_by": "legacy_parsing"}
                ))
        
        return documents
    
    def _create_bill_document(self, bill_data: Any) -> DocumentData:
        """Create DocumentData from BillProcessingAgent result"""
        if isinstance(bill_data, dict):
            return DocumentData(
                type="bill",
                content=bill_data.get("content", str(bill_data)),
                hospital_name=bill_data.get("hospital_name"),
                patient_name=bill_data.get("patient_name"),
                date_of_service=bill_data.get("date_of_service"),
                total_amount=bill_data.get("total_amount"),
                insurance_amount=bill_data.get("insurance_amount"),
                patient_amount=bill_data.get("patient_amount"),
                bill_number=bill_data.get("bill_number"),
                diagnosis=None,
                admission_date=None,
                discharge_date=None,
                treatment_summary=None,
                doctor_name=bill_data.get("doctor_name"),
                policy_number=None,
                member_id=None,
                insurance_company=None,
                coverage_type=None,
                extracted_data=bill_data
            )
        else:
            return DocumentData(
                type="bill",
                content=str(bill_data),
                hospital_name=None,
                patient_name=None,
                date_of_service=None,
                total_amount=None,
                insurance_amount=None,
                patient_amount=None,
                bill_number=None,
                diagnosis=None,
                admission_date=None,
                discharge_date=None,
                treatment_summary=None,
                doctor_name=None,
                policy_number=None,
                member_id=None,
                insurance_company=None,
                coverage_type=None,
                extracted_data={"raw_data": bill_data}
            )
    
    def _create_discharge_document(self, discharge_data: Any) -> DocumentData:
        """Create DocumentData from DischargeProcessingAgent result"""
        if isinstance(discharge_data, dict):
            return DocumentData(
                type="discharge_summary",
                content=discharge_data.get("content", str(discharge_data)),
                hospital_name=discharge_data.get("hospital_name"),
                patient_name=discharge_data.get("patient_name"),
                date_of_service=None,
                total_amount=None,
                insurance_amount=None,
                patient_amount=None,
                bill_number=None,
                diagnosis=discharge_data.get("primary_diagnosis"),
                admission_date=discharge_data.get("admission_date"),
                discharge_date=discharge_data.get("discharge_date"),
                treatment_summary=discharge_data.get("discharge_instructions"),
                doctor_name=discharge_data.get("doctor_name"),
                policy_number=None,
                member_id=None,
                insurance_company=None,
                coverage_type=None,
                extracted_data=discharge_data
            )
        else:
            return DocumentData(
                type="discharge_summary",
                content=str(discharge_data),
                hospital_name=None,
                patient_name=None,
                date_of_service=None,
                total_amount=None,
                insurance_amount=None,
                patient_amount=None,
                bill_number=None,
                diagnosis=None,
                admission_date=None,
                discharge_date=None,
                treatment_summary=None,
                doctor_name=None,
                policy_number=None,
                member_id=None,
                insurance_company=None,
                coverage_type=None,
                extracted_data={"raw_data": discharge_data}
            )
    
    def _create_claim_data_document(self, claim_data: Any) -> DocumentData:
        """Create DocumentData from ClaimDataAgent result"""
        if isinstance(claim_data, dict):
            doc_type = claim_data.get("document_type", "other")
            return DocumentData(
                type=doc_type,
                content=claim_data.get("content", str(claim_data)),
                hospital_name=None,
                patient_name=claim_data.get("patient_name"),
                date_of_service=claim_data.get("test_date") or claim_data.get("prescription_date"),
                total_amount=None,
                insurance_amount=None,
                patient_amount=None,
                bill_number=None,
                diagnosis=None,
                admission_date=None,
                discharge_date=None,
                treatment_summary=None,
                doctor_name=claim_data.get("prescribing_doctor") or claim_data.get("ordering_physician"),
                policy_number=claim_data.get("policy_number"),
                member_id=claim_data.get("member_id"),
                insurance_company=claim_data.get("insurance_company"),
                coverage_type=claim_data.get("coverage_type"),
                extracted_data=claim_data
            )
        else:
            return DocumentData(
                type="other",
                content=str(claim_data),
                hospital_name=None,
                patient_name=None,
                date_of_service=None,
                total_amount=None,
                insurance_amount=None,
                patient_amount=None,
                bill_number=None,
                diagnosis=None,
                admission_date=None,
                discharge_date=None,
                treatment_summary=None,
                doctor_name=None,
                policy_number=None,
                member_id=None,
                insurance_company=None,
                coverage_type=None,
                extracted_data={"raw_data": claim_data}
            )
    
    def _create_classification_document(self, doc_data: Any) -> DocumentData:
        """Create DocumentData from DocumentAgent classification result"""
        if isinstance(doc_data, dict):
            return DocumentData(
                type=doc_data.get("type", "unknown"),
                content=doc_data.get("content", str(doc_data)),
                hospital_name=None,
                patient_name=None,
                date_of_service=None,
                total_amount=None,
                insurance_amount=None,
                patient_amount=None,
                bill_number=None,
                diagnosis=None,
                admission_date=None,
                discharge_date=None,
                treatment_summary=None,
                doctor_name=None,
                policy_number=None,
                member_id=None,
                insurance_company=None,
                coverage_type=None,
                extracted_data={"classification_confidence": doc_data.get("confidence"), "filename": doc_data.get("filename")}
            )
        else:
            return DocumentData(
                type="unknown",
                content=str(doc_data),
                hospital_name=None,
                patient_name=None,
                date_of_service=None,
                total_amount=None,
                insurance_amount=None,
                patient_amount=None,
                bill_number=None,
                diagnosis=None,
                admission_date=None,
                discharge_date=None,
                treatment_summary=None,
                doctor_name=None,
                policy_number=None,
                member_id=None,
                insurance_company=None,
                coverage_type=None,
                extracted_data={"raw_data": doc_data}
            )