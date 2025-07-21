FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app/unified_agent_system

CMD ["uvicorn", "unified_agent_system.main:app", "--host", "0.0.0.0", "--port", "80"]
