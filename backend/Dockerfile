FROM python:3.11-slim

WORKDIR /app

# Install dependencies first so Docker can cache this layer — it only
# re-runs when requirements.txt actually changes, not on every code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY attribution/ ./attribution/
COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 