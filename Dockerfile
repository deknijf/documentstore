FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY static ./static
COPY data ./data

EXPOSE 8000
CMD ["sh", "-c", "if [ \"${TRUST_PROXY_HEADERS:-false}\" = \"true\" ] || [ \"${TRUST_PROXY_HEADERS:-false}\" = \"1\" ]; then exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'; else exec uvicorn app.main:app --host 0.0.0.0 --port 8000; fi"]
