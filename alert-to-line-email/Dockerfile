FROM python:3.11-slim

WORKDIR /app

COPY alert_to_line.py .

RUN pip install fastapi uvicorn httpx

CMD ["uvicorn", "alert_to_line:app", "--host", "0.0.0.0", "--port", "8080"]
