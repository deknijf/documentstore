FROM python:3.13-slim

ARG APP_VERSION=0.7.0
ARG GIT_TAG=v0.7.0

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
# Only the reverse proxy's own address may set X-Forwarded-*; with '*' any
# client could spoof its address, which lands in the audit log and would defeat
# rate limiting. Override FORWARDED_ALLOW_IPS if the proxy sits elsewhere.
ENV FORWARDED_ALLOW_IPS="127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

CMD ["sh", "-c", "if [ \"${TRUST_PROXY_HEADERS:-false}\" = \"true\" ] || [ \"${TRUST_PROXY_HEADERS:-false}\" = \"1\" ]; then exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=\"${FORWARDED_ALLOW_IPS}\"; else exec uvicorn app.main:app --host 0.0.0.0 --port 8000; fi"]
