# Single-stage build for Health Insurance Claim Processor
FROM python:3.11-slim

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Install system dependencies required for building
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock* README.md ./

# Install dependencies (excluding dev dependencies for production)
RUN uv sync --no-dev --frozen

# Copy application code
COPY agents/ agents/
COPY services/ services/
COPY utils/ utils/
COPY main.py ./
COPY .env ./
COPY .env.debug ./

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV UVICORN_HOST=0.0.0.0
ENV UVICORN_PORT=8000

# Add labels for metadata
LABEL org.opencontainers.image.title="Health Insurance Claim Processor"
LABEL org.opencontainers.image.description="Agentic backend pipeline for medical insurance claim documents"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.authors="nihaal.a084@gmail.com"

# Run the application with proper signal handling using uv
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
