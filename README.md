# Health Insurance Claim Processor

An agentic backend pipeline that processes medical insurance claim documents using AI tools, FastAPI, and Google Agent Development Kit (ADK).

## Features

- **Document Processing**: Upload multiple PDF files (bills, discharge summaries, claim correspondence, etc.)
- **AI-Powered OCR**: Extract text from PDFs using Gemini API
- **Document Classification**: Automatically classify documents based on filename and content
- **Multi-Agent Processing**: Parallel processing using specialized agents (BillAgent, DischargeAgent, etc.)
- **Structured Output**: Convert unstructured data into defined JSON schemas
- **Validation**: Validate extracted data for missing information or inconsistencies
- **Claim Decision**: Automated approve/reject decisions with detailed reasoning

## Architecture

```
Sequential Flow:
OCR Agent → Document Classification Agent → Parallel Processing → Validation Agent → Claim Decision Agent

Parallel Processing:
├── Bill Processing Agent
├── Discharge Processing Agent
├── ID Card Processing Agent
└── Correspondence Processing Agent
```

## Quick Start

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Gemini API key
   ```

3. **Run the application:**
   ```bash
   uv run fastapi dev src/health_insurance_claim_processor/main.py
   ```

4. **Test the API:**
   ```bash
   curl -X POST "http://localhost:8000/process-claim" \
     -F "files=@tests/sample_bill.pdf" \
     -F "files=@tests/sample_discharge.pdf"
   ```

## API Endpoints

### POST /process-claim

Process medical insurance claim documents.

**Request:**
- Content-Type: `multipart/form-data`
- Field: `files` (multiple PDF files)

**Response:**
```json
{
  "documents": [
    {
      "type": "bill",
      "hospital_name": "ABC Hospital",
      "total_amount": 12500,
      "date_of_service": "2024-04-10",
      "content": "text from the bill document"
    }
  ],
  "validation": {
    "missing_documents": [],
    "discrepancies": []
  },
  "claim_decision": {
    "status": "approved",
    "reason": "All required documents present and data is consistent"
  }
}
```

## Development

### Run Tests
```bash
uv run pytest
```

### Docker Deployment
```bash
docker build -t claim-processor .
docker run -p 8000:8000 claim-processor
```

## Project Structure

```
├── src/health_insurance_claim_processor/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── agents/                 # AI agents
│   │   ├── __init__.py
│   │   ├── ocr_agent.py
│   │   ├── document_agent.py
│   │   ├── bill_agent.py
│   │   ├── discharge_agent.py
│   │   ├── validation_agent.py
│   │   └── claim_decision_agent.py
│   ├── models/                 # Pydantic models
│   │   ├── __init__.py
│   │   ├── request.py
│   │   └── response.py
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── pdf_processor.py
│   │   └── document_classifier.py
│   └── utils/                  # Utilities
│       ├── __init__.py
│       ├── config.py
│       └── logger.py
├── tests/                      # Test files
├── docker-compose.yml          # Docker services
├── Dockerfile                  # Container definition
├── .env.example               # Environment template
└── README.md
```

## License

MIT License
