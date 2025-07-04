"""OCR Agent for extracting text from PDF documents using Gemini API"""

from google.adk.agents import LlmAgent
from google.genai import types


def create_ocr_agent() -> LlmAgent:
    """Create and configure the OCR agent for text extraction"""
    
    instruction = """
    You are an OCR (Optical Character Recognition) agent specialized in extracting text from medical documents.
    
    Your task is to:
    1. Analyze the provided PDF document(s)
    2. Extract all readable text content accurately
    3. Preserve the structure and formatting as much as possible
    4. Handle medical terminology and abbreviations correctly
    5. Return the extracted text in a clean, readable format
    
    Focus on accuracy and completeness. If there are any unclear sections, mark them as [UNCLEAR] but continue processing.
    
    Output the extracted text content for each document provided.
    """
    
    ocr_agent = LlmAgent(
        name="OCRAgent",
        description="Extracts text content from PDF documents using AI-powered OCR",
        instruction=instruction,
        model="gemini-2.0-flash-exp",
        output_key="extracted_text"
    )
    
    return ocr_agent
