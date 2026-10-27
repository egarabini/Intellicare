"""API de transcrição de áudio — faster-whisper otimizado para CPU.

Perguntas curtas (5-10 s) de consulta de leito; alvo de latência < 15 s.
Privacidade: áudio processado 100% em memória (nada em disco), nada de
conteúdo em logs, sem chamadas externas em operação (modelo pré-baixado).
"""

import io
import os
import time

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from faster_whisper import WhisperModel

app = FastAPI(title="Whisper STT", version="2.0.0")

# Modelos permitidos (lazily carregados e cacheados em memória)
MODEL_SIZES = {
    "turbo": "deepdml/faster-whisper-large-v3-turbo-ct2",
    "medium": "Systran/faster-whisper-medium",
    "small": "Systran/faster-whisper-small",
}
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "turbo")
CPU_THREADS = int(os.getenv("CPU_THREADS", "12"))
BEAM_SIZE = int(os.getenv("BEAM_SIZE", "1"))  # 1 = greedy: ~4x mais rápido que o padrão 5
NUM_WORKERS = int(os.getenv("NUM_WORKERS", "1"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))  # 25 MB
# Token Bearer opcional: se STT_BEARER_TOKEN estiver definido, exige
# "Authorization: Bearer <token>"; se vazio, endpoint aberto (whitelist de IP only)
STT_BEARER_TOKEN = os.getenv("STT_BEARER_TOKEN", "")

models: dict[str, WhisperModel] = {}


def get_model(key: str) -> WhisperModel:
    if key not in models:
        models[key] = WhisperModel(
            MODEL_SIZES[key], device="cpu", compute_type="int8",
            cpu_threads=CPU_THREADS, num_workers=NUM_WORKERS,
        )
    return models[key]


async def check_auth(request: Request) -> None:
    if not STT_BEARER_TOKEN:
        return
    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {STT_BEARER_TOKEN}":
        raise HTTPException(status_code=401, detail="Token inválido")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": MODEL_SIZES[DEFAULT_MODEL],
        "beam_size": BEAM_SIZE,
        "cpu_threads": CPU_THREADS,
        "auth": "bearer" if STT_BEARER_TOKEN else "ip-whitelist",
        "loaded_models": sorted(models),
    }


@app.post("/transcrever")
async def transcrever_audio(
    file: UploadFile = File(...),
    language: str = Form("pt"),
    prompt: str = Form(""),
    model_size: str = Form(DEFAULT_MODEL),
    _: None = Depends(check_auth),
):
    if model_size not in MODEL_SIZES:
        raise HTTPException(status_code=400, detail=f"model_size deve ser um de: {', '.join(MODEL_SIZES)}")
    if language in ("", "auto"):
        language = None  # deixa o Whisper detectar

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo muito grande")

    model = get_model(model_size)
    started = time.perf_counter()
    segments, info = model.transcribe(
        io.BytesIO(data),  # 100% em memória — nada gravado em disco
        language=language,
        beam_size=BEAM_SIZE,
        initial_prompt=prompt or None,
        vad_filter=True,  # pula silêncio: menos compute em perguntas curtas
    )
    texto_final = " ".join(segment.text for segment in segments)
    elapsed = time.perf_counter() - started

    return {
        "texto": texto_final.strip(),
        "idioma": info.language,
        "duracao": round(info.duration, 2),
        "tempo_processamento": round(elapsed, 2),
        "modelo": model_size,
    }
