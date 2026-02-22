FROM python:3.11-slim AS base

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir . && pip cache purge

COPY florence/ florence/

# API target
FROM base AS api
EXPOSE 8000
CMD ["uvicorn", "florence.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]

# UI target (futuro)
FROM base AS ui
RUN pip install --no-cache-dir ".[ui]" && pip cache purge
COPY florence/ui/ florence/ui/
EXPOSE 8502
CMD ["streamlit", "run", "florence/ui/main.py", "--server.port=8502", "--server.headless=true"]
