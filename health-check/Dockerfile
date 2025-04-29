FROM python:3.9-slim

WORKDIR /app

COPY health-check.py .
COPY config/ /app/config/

RUN pip install fastapi uvicorn httpx

CMD ["uvicorn", "health-check:app", "--host", "0.0.0.0", "--port", "8081"]
