FROM python:3.11-slim

WORKDIR /app

COPY agents/orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/orchestrator/ ./agents/orchestrator/
COPY agents/common/ ./agents/common/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

EXPOSE 8080

WORKDIR /app/agents/orchestrator

CMD ["python", "main.py"]