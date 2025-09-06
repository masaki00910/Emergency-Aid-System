FROM python:3.11-slim

WORKDIR /app

COPY agents/detection/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/detection/ ./agents/detection/
COPY agents/common/ ./agents/common/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

EXPOSE 8080

WORKDIR /app/agents/detection

CMD ["python", "main.py"]