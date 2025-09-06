FROM python:3.11-slim

WORKDIR /app

COPY agents/support/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/support/ ./agents/support/
COPY agents/common/ ./agents/common/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

EXPOSE 8080

WORKDIR /app/agents/support

CMD ["python", "main.py"]