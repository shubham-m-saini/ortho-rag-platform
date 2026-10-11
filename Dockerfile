FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project structure
COPY api_gateway/ ./api_gateway/
COPY services/ ./services/

# 🔑 CRITICAL: Add root and services to Python Path
ENV PYTHONPATH=/app:/app/services

EXPOSE 8000

# Run the orchestrator located in api_gateway/main.py
CMD ["uvicorn", "api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
