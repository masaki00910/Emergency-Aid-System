FROM python:3.11-slim

WORKDIR /app

COPY agents/info_collector/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/info_collector/ ./agents/info_collector/
COPY agents/common/ ./agents/common/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

EXPOSE 8080

WORKDIR /app/agents/info_collector

CMD ["python", "main.py"]