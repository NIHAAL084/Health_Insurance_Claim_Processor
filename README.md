
# Health Insurance Claim Processor

The Health Insurance Claim Processor is an agentic backend pipeline that automates the extraction, classification, validation, and decision-making for medical insurance claim documents. It is designed for hospitals, TPAs, and insurance companies to streamline claim processing, reduce manual effort, and improve accuracy.

**Use Cases:**

- Automated claims intake for hospitals and insurers
- Bulk processing of scanned medical documents
- Pre-validation of claims before human review
- Integration with hospital/insurance portals for real-time claim status

---

## System Overview & Agent Flow

The system processes uploaded PDFs (bills, discharge summaries, ID cards, claim forms, etc.) through a multi-agent pipeline:

```mermaid
flowchart TD
    A[Upload PDF(s)] --> B[Text Extraction (PyPDF)]
    B --> C[Document Classification Agent]
    C --> D1[Bill Processing Agent]
    C --> D2[Discharge Processing Agent]
    C --> D3[Claim Data Agent]
    D1 & D2 & D3 --> E[Validation Agent]
    E --> F[Claim Decision Agent]
    F --> G[API Response]
```

**Step-by-step:**

1. **Upload**: User uploads one or more PDF files via the `/process-claim` endpoint.
2. **Text Extraction**: PyPDF extracts text from each PDF (no external OCR required).
3. **Document Classification**: An LLM agent classifies each document (bill, discharge, ID card, claim form, etc.).
4. **Parallel Agent Processing**: Specialized agents extract structured data from each document type:
    - **Bill Processing Agent**: Extracts billing details (amounts, hospital, patient, etc.)
    - **Discharge Processing Agent**: Extracts discharge summary details (diagnosis, dates, instructions, etc.)
    - **Claim Data Agent**: Extracts data from ID cards, correspondence, prescriptions, etc.
5. **Validation**: The validation agent checks for missing documents, inconsistencies, and data quality issues.
6. **Claim Decision**: The claim decision agent makes an automated approve/reject/pending decision with reasoning and confidence.
7. **Response**: The API returns a structured JSON with all agent outputs, validation, and decision.

**Agent Roles:**

- **PDFProcessor**: Extracts text from PDFs using PyPDF.
- **Document Classification Agent**: Classifies each document by type.
- **Bill Processing Agent**: Extracts billing details (amounts, hospital, patient, etc.).
- **Discharge Processing Agent**: Extracts discharge summary details (diagnosis, dates, instructions, etc.).
- **Claim Data Agent**: Extracts data from ID cards, correspondence, prescriptions, etc.
- **Validation Agent**: Checks for missing documents, discrepancies, and data quality issues.
- **Claim Decision Agent**: Makes the final claim decision and provides reasoning and confidence.

---

## Response Format Explained

The `/process-claim` endpoint returns a comprehensive JSON object with all extracted, validated, and decision data. The response is richer and more detailed when a full set of claim documents (bill, discharge summary, claim form, ID card, etc.) is provided.

**Response Fields:**

- `request_id`: Unique identifier for the claim processing request.
- `processing_time`: Time taken to process the request (seconds).
- `timestamp`: ISO timestamp when processing completed.
- `workflow_status`: `completed`, `no_outputs`, or `error`.
- `agent_outputs`:
  - `documents`: List of all classified documents, each with type, filename, extracted content, and confidence score.
  - `bill_data`: List of extracted bill details (hospital, patient, amounts, service details, etc.).
  - `discharge_data`: List of extracted discharge summary details (diagnosis, admission/discharge dates, procedures, etc.).
  - `claim_data`: List of extracted claim-related data (ID cards, correspondence, prescriptions, etc.).
  - `validation_results`: Validation summary (missing documents, discrepancies, validation score, recommendations, agent compliance issues).
  - `claim_decision`: Final decision (`approved`, `rejected`, or `pending`), reason, confidence score, and recommended actions.
- `raw_session_state`: (Advanced) Full agent state for debugging or audit.

**Note:**
Due to hardware limitations, the provided example and test runs may only include a single bill. In production, when a large PDF or a full set of documents is uploaded, the response will include:

- Multiple documents (bill, discharge summary, claim form, ID card, etc.)
- Complete extraction of all relevant fields from each document
- Detailed validation and cross-checking between documents
- A more confident and automated claim decision

**Example (full, idealized response):**

```json
{
  "request_id": "a1b2c3d4-5678-90ef-ghij-klmnopqrstuv",
  "processing_time": 18.42,
  "timestamp": "2025-07-12T12:34:56.789Z",
  "workflow_status": "completed",
  "agent_outputs": {
    "documents": [
      { "type": "bill", "filename": "bill.pdf", "content": "...", "confidence": 0.98 },
      { "type": "discharge_summary", "filename": "discharge.pdf", "content": "...", "confidence": 0.97 },
      { "type": "claim_form", "filename": "claim_form.pdf", "content": "...", "confidence": 0.96 },
      { "type": "id_card", "filename": "id_card.pdf", "content": "...", "confidence": 0.99 }
    ],
    "bill_data": [
      {
        "hospital_name": "ABC Hospital",
        "total_amount": 12500,
        "date_of_service": "2024-04-10",
        "patient_name": "John Doe",
        "bill_number": "BILL12345",
        "insurance_amount": 10000,
        "patient_amount": 2500,
        "service_details": ["Surgery", "Room Charges", "Medicines"],
        "doctor_name": "Dr. Smith",
        "department": "Orthopedics"
      }
    ],
    "discharge_data": [
      {
        "patient_name": "John Doe",
        "admission_date": "2024-04-05",
        "discharge_date": "2024-04-10",
        "primary_diagnosis": "Fracture",
        "procedures_performed": ["Surgery"],
        "doctor_name": "Dr. Smith",
        "hospital_name": "ABC Hospital",
        "department": "Orthopedics"
      }
    ],
    "claim_data": [
      {
        "document_type": "id_card",
        "policy_number": "XYZ1234567",
        "member_id": "M123456",
        "insurance_company": "Best Insurance Co.",
        "coverage_type": "Family Floater"
      },
      {
        "document_type": "claim_form",
        "claim_number": "CLM987654",
        "date_filed": "2024-04-11"
      }
    ],
    "validation_results": {
      "missing_documents": [],
      "discrepancies": [],
      "validation_score": 100.0,
      "recommendations": [],
      "agent_compliance_issues": []
    },
    "claim_decision": {
      "status": "approved",
      "reason": "All required documents present and data is consistent.",
      "confidence_score": 98.5,
      "recommended_actions": []
    }
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

2. **Set up Ollama and pull a model:**

   Ollama is required to run local LLMs (e.g., mistral, llama3). If you haven't already:

   - [Install Ollama](https://ollama.com/download) for your platform and start the Ollama service.
   - Pull a model (e.g., mistral):

     ```bash
     ollama pull mistral
     ```

   You can use any supported model (e.g., llama3) by pulling it and setting `OLLAMA_MODEL` accordingly.

3. **Set up environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env to set OLLAMA_MODEL (e.g., mistral:latest or llama3.2:3b)
   # Set LOG_LEVEL as needed (DEBUG, INFO, etc.)
   ```

4. **Run the application (development):**

   ```bash
   uv run fastapi dev main.py
   ```

5. **Run the application with logging to a file (production-style):**

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info --log-config utils/logger.py --log-file app.log
   # or, for custom logging, see utils/logger.py and config.py
   ```

6. **Test the API with curl:**

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

**Response:**
See the detailed example and field explanations in the [Response Format Explained](#response-format-explained) section above. The response includes:

- `request_id`, `processing_time`, `timestamp`, `workflow_status`
- `agent_outputs` (with `documents`, `bill_data`, `discharge_data`, `claim_data`, `validation_results`, `claim_decision`)
- `raw_session_state` (for advanced debugging)

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

Build and run the application in a containerized environment:

```bash
# Build the Docker image
docker build -t health-claim-processor .

# Run the container (default: port 8000)
docker run --rm -p 8000:8000 \
  -e OLLAMA_MODEL=mistral:latest \
  -e LOG_LEVEL=INFO \
  health-claim-processor
```

**Notes:**

- The container runs as a non-root user for security.
- All environment variables in `.env` can be overridden with `-e` flags at runtime.
- The default entrypoint uses `uv` and `uvicorn` for robust FastAPI serving.
- For production, use a process manager or container orchestration for resilience.

## Project Structure

## Project Directory Structure

```
├── agents/                         # All agent logic and orchestration
│   └── HealthInsuranceClaimProcessorAgent/
│       ├── agent.py                # Main agent entrypoint
│       ├── workflow_agent.py       # Orchestrates the agent workflow
│       └── sub_agents/             # Specialized sub-agents for each document type
│           ├── BillProcessingAgent/bill_agent.py           # Bill extraction logic
│           ├── ClaimDataAgent/claim_data_agent.py          # ID card, correspondence, prescription extraction
│           ├── ClaimDecisionAgent/claim_decision_agent.py  # Final claim decision logic
│           ├── DischargeProcessingAgent/discharge_agent.py # Discharge summary extraction
│           ├── DocumentAgent/document_agent.py             # Document classification logic
│           └── ValidationAgent/validation_agent.py         # Data validation logic
├── main.py                          # FastAPI app entrypoint
├── services/                        # Service layer for business logic
│   ├── claim_processor.py           # Main claim processing service
│   └── pdf_processor.py             # PDF text extraction service
├── utils/                           # Utility modules
│   ├── config.py                    # Configuration management
│   └── logger.py                    # Logging setup
├── test_files/                      # Example/test PDFs
├── Dockerfile                       # Docker build instructions
├── pyproject.toml                   # Python project metadata & dependencies
├── uv.lock                          # Locked dependency versions
├── .env                             # Environment variables (user config)
├── .env.debug                       # Debug environment variables
├── README.md                        # Project documentation
├── .gitignore                       # Git ignore rules
```

**Other files:**

- `extracted_text_from_pdf_used_for_testrun.txt`: the text extracted from the test PDF.
- `testrun.md`: output of the API request and response for the test run.

Each file/folder is commented above for its purpose in the project.

## Configuration

All configuration is managed via `.env` and `utils/config.py`. Key settings:

### Example .env file

```env
OLLAMA_MODEL=mistral:latest
LOG_LEVEL=DEBUG
```

Copy this to `.env` and adjust as needed for your environment.

- `OLLAMA_MODEL`: LLM model to use (e.g., `mistral:latest`)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, etc.)

See `utils/config.py` for all options.

## License

MIT License

## Maintainer

Nihaal Anupoju  
<nihaal.a084@gmail.com>
