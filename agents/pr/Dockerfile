FROM python:3.11-slim

WORKDIR /app

COPY agents/pr/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/pr/ ./agents/pr/
COPY agents/common/ ./agents/common/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

EXPOSE 8080

WORKDIR /app/agents/pr

CMD ["python", "main.py"]