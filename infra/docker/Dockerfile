FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APEX_HOST=0.0.0.0 \
    APEX_PORT=8000 \
    APEX_AI_PROVIDER=light

WORKDIR /app

# OpenCV headless still requires a small set of native runtime libraries.
# Keep the production image free of the full desktop/X11 stack.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libxcb1 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt requirements-prod.txt
RUN python -m pip install --upgrade pip \
    && pip install -r requirements-prod.txt

COPY app ./app
COPY catalog ./catalog
COPY assets ./assets
COPY run.py ./run.py
COPY infra/docker/healthcheck.py ./infra/docker/healthcheck.py

RUN mkdir -p /app/output /app/uploads \
    && useradd --create-home --uid 10001 apex \
    && chown -R apex:apex /app

USER apex

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python /app/infra/docker/healthcheck.py || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
