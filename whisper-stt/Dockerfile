FROM python:3.10-slim

# Dependências de sistema para processamento de áudio
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# faster-whisper + API
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" faster-whisper python-multipart

COPY main.py .

EXPOSE 8000

# Cache do modelo HuggingFace persistido em volume (evita re-download a cada recriação)
ENV HF_HOME=/app/models
VOLUME /app/models

HEALTHCHECK --interval=30s --timeout=5s --start-period=300s \
    CMD curl -sf http://localhost:8000/health || exit 1

# main:app (módulo:variável) — "uvicorn main.py" não funciona
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
