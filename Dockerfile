FROM python:3.13-slim

ARG APP_VERSION=0.6.7
ARG GIT_TAG=v0.6.7

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_VERSION=${APP_VERSION}
ENV GIT_TAG=${GIT_TAG}

LABEL org.opencontainers.image.title="docstore"
LABEL org.opencontainers.image.version="${APP_VERSION}"
LABEL org.opencontainers.image.ref.name="${GIT_TAG}"

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip==25.3 \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY static ./static
COPY data ./data

EXPOSE 8000
CMD ["sh", "-c", "if [ \"${TRUST_PROXY_HEADERS:-false}\" = \"true\" ] || [ \"${TRUST_PROXY_HEADERS:-false}\" = \"1\" ]; then exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'; else exec uvicorn app.main:app --host 0.0.0.0 --port 8000; fi"]
