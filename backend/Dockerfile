FROM python:3.10-slim

WORKDIR /workspace

# Install system dependencies needed for compiling security packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY backend/app /workspace/backend/app

# Set environment paths
ENV PYTHONPATH=/workspace

# Expose port
EXPOSE 8000

# Start server
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
