# Health Insurance Claim Processor - Debug Guide

This guide provides comprehensive debugging instructions for the Health Insurance Claim Processor project.

## 🐛 Debug Mode Overview

The project now includes extensive debugging capabilities to help identify and resolve issues during development and testing:

### Debug Features Added

- **Comprehensive logging** throughout all components (agents, services, FastAPI app)
- **Debug configuration** files for maximum verbosity
- **Test scripts** for end-to-end validation
- **Error tracking** with detailed stack traces
- **Performance monitoring** with timing information

## 🔧 Debug Files Added

### 1. `debug_run.py` - Debug Server Runner

- Starts the FastAPI server with maximum debugging enabled
- Checks environment and configuration
- Logs startup process in detail

### 2. `test_debug.py` - End-to-End Testing

- Tests the complete processing pipeline
- Automatically finds sample PDF files
- Provides detailed error tracking
- Saves results and error logs

### 3. `api_test.py` - API Endpoint Testing

- Tests FastAPI endpoints via HTTP requests
- Validates health checks and claim processing
- Simulates real API usage scenarios

### 4. `.env.debug` - Debug Configuration

- Maximum verbosity settings
- Debug-specific environment variables
- Optimized for troubleshooting

## 🚀 How to Use Debug Mode

### Step 1: Start in Debug Mode

```bash
# Option 1: Use the debug runner
python debug_run.py

# Option 2: Use environment file
cp .env.debug .env
python run.py
```

### Step 2: Test with Sample PDFs

```bash
# Create a samples directory
mkdir samples

# Place your PDF files in the samples directory
# (medical bills, discharge summaries, etc.)

# Run the end-to-end test
python test_debug.py
```

### Step 3: Test API Endpoints

```bash
# First, make sure the server is running (Step 1)
# Then in another terminal:
python api_test.py
```

## 📊 Debug Outputs

### Log Files Created

- `debug.log` - Server startup and runtime logs
- `test_debug.log` - End-to-end test logs
- `api_test.log` - API testing logs
- `test_results.json` - Successful processing results
- `api_test_results.json` - API test results
- `test_error.log` - Error details when tests fail

### Console Output

The debug mode provides real-time console output with:

- 🚀 Startup progress
- 📄 File processing steps
- 🤖 Agent workflow execution
- ✅ Success indicators
- ❌ Error details with stack traces

## 🔍 Debug Logging Levels

### Components with Debug Logging

#### 1. **Agent Creation** (`agents/`)

- Agent initialization and configuration
- Model loading and setup
- Schema validation

#### 2. **Claim Processing Service** (`services/claim_processor.py`)

- Step-by-step workflow execution
- Session management
- Agent event processing
- Result parsing and validation

#### 3. **PDF Processing** (`services/pdf_processor.py`)

- File validation and preparation
- Text extraction from PDFs
- Page-by-page processing
- Character count and statistics

#### 4. **FastAPI Application** (`main.py`)

- Server startup and configuration
- Request/response logging
- Error handling and reporting
- Performance timing

#### 5. **Google ADK Integration**

- Runner and session management
- Agent execution events
- Model interactions

## 🏥 Testing with Sample PDFs

### Recommended Test Files

1. **Medical Bills** - Hospital invoices, clinic statements
2. **Discharge Summaries** - Patient discharge documents
3. **Insurance Cards** - ID cards, policy documents
4. **Mixed Documents** - Multiple document types in one PDF

### File Locations Checked

- `./samples/` (recommended)
- `./test_files/`
- `./pdfs/`
- `~/Documents/test_pdfs/`
- `~/Downloads/`

## 🚨 Common Issues and Solutions

### 1. **Ollama Connection Issues**

```bash
# Check if Ollama is running
ollama list

# Start Ollama if needed
ollama serve

# Pull required model
ollama pull llama3.2:3b
```

### 2. **Google API Key Issues**

```bash
# Set your Google API key
export GOOGLE_API_KEY="your_key_here"

# Or add to .env file
echo "GOOGLE_API_KEY=your_key_here" >> .env
```

### 3. **PDF Processing Errors**

- Check file permissions
- Verify PDF files are not corrupted
- Ensure files are under max size limit (10MB)
- Check file extensions are .pdf

### 4. **Memory Issues**

- Reduce number of parallel agents
- Use smaller PDF files for testing
- Increase agent timeout values

## 📈 Performance Monitoring

### Debug mode tracks

- **Processing time** for each step
- **Memory usage** during execution
- **File processing statistics**
- **Agent execution metrics**
- **API response times**

### Key Performance Indicators

- PDF text extraction time
- Agent workflow execution time
- Total request processing time
- Memory consumption per request

## 🔧 Configuration Options

### Environment Variables for Debugging

```bash
LOG_LEVEL=DEBUG                # Maximum verbosity
DEBUG=true                     # Enable debug mode
PYTHONUNBUFFERED=1            # Immediate output
PYTHONVERBOSE=1               # Detailed Python logging
AGENT_TIMEOUT=600             # Extended timeout for debugging
MAX_PARALLEL_AGENTS=2         # Reduced for stability
```

## 📝 Troubleshooting Steps

### If Tests Fail

1. **Check Logs** - Review the generated log files
2. **Verify Dependencies** - Ensure all packages are installed
3. **Test Components** - Run individual tests for each component
4. **Check Configuration** - Verify environment variables
5. **Resource Usage** - Monitor memory and CPU usage
6. **Network Connectivity** - Check Ollama/API connections

### Get Help

- Review log files for specific error messages
- Check the stack traces in error logs
- Verify all dependencies are properly installed
- Ensure sample PDF files are accessible

## 🎯 Next Steps

After debugging:

1. **Identify Issues** - Use logs to pinpoint problems
2. **Fix Code** - Address specific issues found
3. **Re-test** - Run tests again to verify fixes
4. **Performance Tuning** - Optimize based on metrics
5. **Production Setup** - Configure for production deployment

---

The debug system provides comprehensive visibility into the entire claim processing pipeline, making it easy to identify and resolve issues during development and testing.
