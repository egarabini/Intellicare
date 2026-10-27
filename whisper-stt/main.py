"""API de transcrição de áudio — faster-whisper (large-v3-turbo, CPU int8)."""

import os
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from faster_whisper import WhisperModel

app = FastAPI(title="Whisper STT", version="1.0.0")

MODEL_SIZE = os.getenv("MODEL_SIZE", "deepdml/faster-whisper-large-v3-turbo")
CPU_THREADS = int(os.getenv("CPU_THREADS", "10"))

# Carregado uma única vez no boot (container dedicado a isso)
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8", cpu_threads=CPU_THREADS)

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))  # 25 MB


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_SIZE}


@app.post("/transcrever")
async def transcrever_audio(file: UploadFile = File(...)):
    # tempfile único evita colisão entre requisições simultâneas
    fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename or "audio")[1] or ".tmp")
    try:
        size = 0
        with os.fdopen(fd, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="Arquivo muito grande")
                buffer.write(chunk)

        segments, info = model.transcribe(temp_path, language="pt")
        texto_final = " ".join(segment.text for segment in segments)
        return {
            "texto": texto_final.strip(),
            "idioma": info.language,
            "duracao": round(info.duration, 2),
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
