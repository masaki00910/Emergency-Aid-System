FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_CLOUD_PROJECT=sharelabai-hackathon2
ENV USE_MOCK_LLM=false

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "simple_faq_api.py"]