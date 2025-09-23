FROM python:3.11-slim

WORKDIR /app

# Install FastAPI and essential packages
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    google-cloud-firestore \
    google-cloud-aiplatform \
    langchain \
    langchain-google-vertexai

# Copy application files
COPY api_gateway/ ./api_gateway/
COPY shared/ ./shared/

# Set environment variables
ENV PYTHONPATH=/app
ENV GOOGLE_CLOUD_PROJECT=sharelabai-hackathon2
ENV USE_MOCK_LLM=false

# Expose port
EXPOSE 8081

# Run the FastAPI application
CMD ["uvicorn", "api_gateway.main:app", "--host", "0.0.0.0", "--port", "8081"]