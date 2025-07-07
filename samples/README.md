# Sample PDF Files

This directory should contain sample PDF files for testing the Health Insurance Claim Processor.

## Recommended Test Files

1. **Medical Bills** (e.g., `hospital_bill.pdf`, `clinic_invoice.pdf`)
   - Hospital invoices
   - Clinic statements
   - Medical service bills

2. **Discharge Summaries** (e.g., `discharge_summary.pdf`, `patient_discharge.pdf`)
   - Hospital discharge documents
   - Treatment summaries
   - Patient care records

3. **Insurance Documents** (e.g., `insurance_card.pdf`, `policy_document.pdf`)
   - Insurance ID cards
   - Policy documents
   - Coverage details

4. **Mixed Documents** (e.g., `combined_claim.pdf`)
   - Multiple document types in one PDF
   - Complete claim packages

## File Requirements

- **Format**: PDF only
- **Size**: Maximum 10MB per file
- **Content**: Readable text (not just images)
- **Language**: English preferred

## How to Test

1. Place your PDF files in this directory
2. Run the debug test: `python test_debug.py`
3. Or test the API: `python api_test.py`

## Notes

- The system will automatically find PDF files in this directory
- Files will be processed in alphabetical order
- Processing results will be saved to log files
- Check the logs for detailed processing information

---

**Important**: Do not commit actual medical documents to version control. Use anonymized or synthetic test data only.
