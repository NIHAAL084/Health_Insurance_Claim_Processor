# Overview

The Health Insurance Claim Processor is an agentic backend pipeline that automates the extraction, classification, validation, and decision-making for medical insurance claim documents. It is designed for hospitals, TPAs, and insurance companies to streamline claim processing, reduce manual effort, and improve accuracy.

**Use Cases:**

- Automated claims intake for hospitals and insurers
- Bulk processing of scanned medical documents
- Pre-validation of claims before human review
- Integration with hospital/insurance portals for real-time claim status

---

## How It Works

1. **Upload**: User uploads one or more PDF files (bills, discharge summaries, ID cards, etc.) via the `/process-claim` endpoint.
2. **Text Extraction**: The system uses PyPDF to extract text from each PDF (no external OCR required).
3. **Document Classification**: An LLM agent classifies each document (bill, discharge, ID card, etc.).
4. **Parallel Agent Processing**: Specialized agents extract structured data from each document type.
5. **Validation**: The validation agent checks for missing documents, inconsistencies, and data quality issues.
6. **Claim Decision**: The claim decision agent makes an automated approve/reject/pending decision with reasoning and confidence.
7. **Response**: The API returns a structured JSON with all agent outputs, validation, and decision.

---

## Agent Roles

- **PDFProcessor**: Extracts text from PDFs using PyPDF.
- **Document Classification Agent**: Classifies each document by type.
- **Bill Processing Agent**: Extracts billing details (amounts, hospital, patient, etc.).
- **Discharge Processing Agent**: Extracts discharge summary details (diagnosis, dates, instructions, etc.).
- **Claim Data Agent**: Extracts data from ID cards, correspondence, prescriptions, etc.
- **Validation Agent**: Checks for missing documents, discrepancies, and data quality issues.
- **Claim Decision Agent**: Makes the final claim decision and provides reasoning and confidence.

---

## Response Format Explained

The `/process-claim` endpoint returns a JSON object with the following fields:

- `request_id`: Unique identifier for the claim processing request.
- `processing_time`: Time taken to process the request (seconds).
- `timestamp`: ISO timestamp when processing completed.
- `workflow_status`: `completed`, `no_outputs`, or `error`.
- `agent_outputs`:
  - `documents`: List of classified documents with type, filename, content, and confidence.
  - `bill_data`: List of extracted bill details.
  - `discharge_data`: List of extracted discharge summary details.
  - `claim_data`: List of extracted claim-related data (ID cards, correspondence, etc.).
  - `validation_results`: Validation summary (missing documents, discrepancies, score).
  - `claim_decision`: Final decision, reason, and confidence score.
- `raw_session_state`: (Advanced) Full agent state for debugging or audit.

**Example:**

```json
{
  "request_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
  "processing_time": 12.34,
  "timestamp": "2025-07-12T12:34:56.789Z",
  "workflow_status": "completed",
  "agent_outputs": {
    "documents": [ ... ],
    "bill_data": [ ... ],
    "discharge_data": [ ... ],
    "claim_data": [ ... ],
    "validation_results": { ... },
    "claim_decision": { ... }
  },
  "raw_session_state": { ... }
}
```

---

## Error Handling & Troubleshooting

- If a timeout or error occurs, the response will have `workflow_status: "error"` and an `error` field with details.
- Check the `recommended_actions` field for next steps (e.g., retry, contact support).
- All errors are logged to the console and (optionally) to `app.log` if running with log file enabled.
- For debugging, inspect the `raw_session_state` field in the response.

**Example error response:**

```json
{
  "request_id": "...",
  "processing_time": 900.0,
  "timestamp": "...",
  "workflow_status": "error",
  "error": "timeout",
  "agent_outputs": null,
  "raw_session_state": null,
  "recommended_actions": ["Contact support"]
}
```

---

## Configuration & Environment Variables

All configuration is managed via `.env` and `utils/config.py`. Key settings:

- `OLLAMA_MODEL`: LLM model to use (e.g., `mistral:latest`, `llama3.2:3b`)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, etc.)
- `MAX_FILE_SIZE`: Maximum PDF upload size (default: 10MB)
- `ALLOWED_EXTENSIONS`: Allowed file types (default: pdf)
- `AGENT_TIMEOUT`: Maximum time (seconds) for agent workflow (default: 900)

See `utils/config.py` for all options and defaults.

---

## Logs & Monitoring

- All major events, errors, and agent progress are logged to the console.
- To save logs to a file, run with:

  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info --log-file app.log
  ```

- Review logs with `less app.log` or any text editor.
- Log format and level can be customized in `.env` and `utils/logger.py`.

---

## FAQ

**Q: Can I use this with scanned images or only PDFs?**
A: Only PDFs are supported. For scanned images, convert them to PDF first. OCR is performed using PyPDF (text-based PDFs only).

**Q: What LLMs are supported?**
A: Any model supported by Ollama (e.g., mistral, llama3). Set `OLLAMA_MODEL` in your `.env`.

**Q: How do I increase the timeout for large claims?**
A: Set `AGENT_TIMEOUT` in your `.env` (default: 900 seconds).

**Q: How do I debug agent outputs?**
A: Inspect the `raw_session_state` field in the API response for full agent state.

**Q: How do I add new document types or agents?**
A: Extend the agent classes in `agents/HealthInsuranceClaimProcessorAgent/sub_agents/` and update the workflow in `workflow_agent.py`.

---

# Health Insurance Claim Processor

An agentic backend pipeline that processes medical insurance claim documents using FastAPI, Google Agent Development Kit (ADK), and local LLMs (via Ollama). OCR and PDF parsing are handled using PyPDF, with no external AI OCR dependencies.

## Features

- **Document Upload & Parsing**: Upload multiple PDF files (bills, discharge summaries, ID cards, correspondence, etc.)
- **OCR & Text Extraction**: Extract text from PDFs using PyPDF (no external OCR API required)
- **Document Classification**: Automatically classify documents using LLM agents
- **Multi-Agent Orchestration**: Specialized agents (Bill, Discharge, Validation, Claim Decision, etc.) process documents in parallel and sequence
- **Structured Output**: Convert unstructured data into clean, minimal JSON
- **Validation**: Check for missing documents, data inconsistencies, and quality issues
- **Automated Claim Decision**: Approve/reject claims with detailed reasoning and confidence scores

## Architecture & Agent Flow

```
Sequential Flow:
PDFProcessor (PyPDF OCR/Text Extraction)
→ Document Classification Agent
→ Parallel Processing:
    ├── Bill Processing Agent
    ├── Discharge Processing Agent
    ├── Claim Data Agent (ID cards, correspondence, prescriptions, etc.)
→ Validation Agent
→ Claim Decision Agent
```

**Key Technologies:**

- FastAPI (REST API)
- Google ADK (agent orchestration)
- Ollama (local LLMs, e.g., mistral, llama3)
- PyPDF (PDF parsing and text extraction)

## Quick Start

1. **Install dependencies:**

   ```bash
   uv sync
   ```

2. **Set up environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env to set OLLAMA_MODEL (e.g., mistral:latest or llama3.2:3b)
   # Set LOG_LEVEL as needed (DEBUG, INFO, etc.)
   ```

3. **Run the application (development):**

   ```bash
   uv run fastapi dev main.py
   ```

4. **Run the application with logging to a file (production-style):**

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info --log-config utils/logger.py --log-file app.log
   # or, for custom logging, see utils/logger.py and config.py
   ```

5. **Test the API with curl:**

   ```bash
   curl --max-time 1200 -X POST "http://127.0.0.1:8000/process-claim" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@test_files/25013102111-2_20250427_120738-Appolo-ts.pdf"
   ```

## API Endpoints

### POST `/process-claim`

Process medical insurance claim documents (PDFs). Returns a structured JSON response with extracted data, validation, and claim decision.

**Request:**

- Content-Type: `multipart/form-data`
- Field: `files` (multiple PDF files)

**Example Response:**

```json
{
  "request_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
  "processing_time": 12.34,
  "timestamp": "2025-07-12T12:34:56.789Z",
  "workflow_status": "completed",
  "agent_outputs": {
    "documents": [
      {
        "type": "bill",
        "filename": "25013102111-2_20250427_120738-Appolo.pdf",
        "content": "...extracted text...",
        "confidence": 0.98
      }
    ],
    "bill_data": [
      {
        "hospital_name": "ABC Hospital",
        "total_amount": 12500,
        "date_of_service": "2024-04-10",
        "patient_name": "John Doe"
      }
    ],
    "discharge_data": [
      {
        "patient_name": "John Doe",
        "admission_date": "2024-04-05",
        "discharge_date": "2024-04-10",
        "primary_diagnosis": "Fracture"
      }
    ],
    "claim_data": [
      {
        "document_type": "id_card",
        "policy_number": "XYZ1234567"
      }
    ],
    "validation_results": {
      "missing_documents": [],
      "discrepancies": [],
      "validation_score": 1.0
    },
    "claim_decision": {
      "status": "approved",
      "reason": "All required documents present and data is consistent",
      "confidence_score": 0.97
    }
  }
}
```

## Development & Testing

### Run Tests

```bash
uv run pytest
# or
pytest
```

### Run with Uvicorn and Save Logs

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info --log-file app.log
# Review logs later with:
less app.log
```

### Docker Deployment

```bash
docker build -t claim-processor .
docker run -p 8000:8000 claim-processor
```

The container will start the FastAPI server on port 8000 using `uv` and the `main.py` entrypoint as defined in the Dockerfile.

## Project Structure

```
├── agents/
│   └── HealthInsuranceClaimProcessorAgent/
│       ├── agent.py
│       ├── workflow_agent.py
│       └── sub_agents/
│           ├── BillProcessingAgent/
│           │   └── bill_agent.py
│           ├── ClaimDataAgent/
│           │   └── claim_data_agent.py
│           ├── ClaimDecisionAgent/
│           │   └── claim_decision_agent.py
│           ├── DischargeProcessingAgent/
│           │   └── discharge_agent.py
│           ├── DocumentAgent/
│           │   └── document_agent.py
│           └── ValidationAgent/
│               └── validation_agent.py
├── apollo_pdf_extracted_text.txt
├── main.py
├── services/
│   ├── claim_processor.py
│   └── pdf_processor.py
├── test_files/
│   ├── 25013102111-2_20250427_120738-Appolo.pdf
│   ├── 25013102111-2_20250427_120738-Appolo-ts.pdf
│   ├── 25020300401-3_20250427_120739-max health.pdf
│   ├── 25020500888-2_20250427_120744-ganga ram.pdf
│   └── 25020701680-2_20250427_120746-fortis.pdf
├── utils/
│   ├── config.py
│   └── logger.py
├── Dockerfile
├── README.md
├── pyproject.toml
├── uv.lock
├── .env
├── .env.debug
├── .gitignore
```

## Configuration

All configuration is managed via `.env` and `utils/config.py`. Key settings:

- `OLLAMA_MODEL`: LLM model to use (e.g., `mistral:latest`)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, etc.)
- `MAX_FILE_SIZE`: Maximum PDF upload size (default: 10MB)
- `ALLOWED_EXTENSIONS`: Allowed file types (default: pdf)

See `utils/config.py` for all options.

## License

MIT License
