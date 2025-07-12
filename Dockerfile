FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv


# Copy project files
COPY pyproject.toml ./
COPY .env ./
COPY .env.debug ./
COPY uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Copy source code and all relevant directories
COPY agents/ agents/
COPY services/ services/
COPY utils/ utils/
COPY main.py ./
COPY tests/ tests/

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser


# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1


# Run the application
CMD ["uv", "run", "fastapi", "dev", "main.py"]
