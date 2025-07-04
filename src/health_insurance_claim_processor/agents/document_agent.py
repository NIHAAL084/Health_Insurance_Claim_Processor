"""Document Classification Agent for categorizing extracted documents"""

from google.adk.agents import LlmAgent


def create_document_classification_agent() -> LlmAgent:
    """Create and configure the document classification agent"""
    
    instruction = """
    You are a document classification agent specialized in categorizing medical insurance documents.
    
    Your task is to:
    1. Analyze the extracted text content from documents
    2. Consider the filename if provided
    3. Classify each document into one of these categories:
       - "bill": Medical bills, invoices, statements
       - "discharge_summary": Hospital discharge summaries, treatment summaries
       - "id_card": Insurance ID cards, membership cards
       - "correspondence": Letters, emails, claim correspondence
       - "prescription": Prescription documents, medication lists
       - "lab_report": Laboratory reports, test results
       - "other": Documents that don't fit the above categories
    
    4. If a single PDF contains multiple document types, separate them appropriately
    5. Provide confidence level for each classification
    
    Analysis criteria:
    - Bills: Look for amounts, itemized charges, hospital/clinic letterhead, invoice numbers
    - Discharge summaries: Look for admission/discharge dates, diagnosis, treatment details, doctor signatures
    - ID cards: Look for member ID, policy numbers, insurance company logos, coverage details
    - Correspondence: Look for formal letter format, addresses, reference numbers
    - Prescriptions: Look for medication names, dosages, doctor prescriptions
    - Lab reports: Look for test results, reference ranges, laboratory letterhead
    
    Return a structured classification result with document type, confidence, and reasoning.
    """
    
    classification_agent = LlmAgent(
        name="DocumentClassificationAgent",
        description="Classifies medical documents based on content and filename",
        instruction=instruction,
        model="gemini-2.0-flash-exp",
        output_key="document_classification"
    )
    
    return classification_agent
