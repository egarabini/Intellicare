# Whisper STT — stt.saudeplanner.com.br

Serviço de transcrição de áudio (faster-whisper large-v3-turbo, CPU int8) isolado
em Docker, atrás de Nginx com whitelist de IP.

## Arquitetura

```
[Cliente autorizado 158.220.99.24]
        │ HTTPS (443)
        ▼
[Nginx — valida IP (allow/deny), TLS Let's Encrypt]
        │ proxy interno
        ▼
[Docker whisper-service — bindado em 127.0.0.1:8000]
```

- Docker **não publica porta no IP público** (`127.0.0.1:8000`) → não interfere
  em iptables/ufw nem expõe o serviço direto pelo IP da VPS.
- Nginx é o porteiro: quem não está na whitelist recebe **403** antes de tocar
  o Whisper.

## Arquivos

| Arquivo | Função |
|---|---|
| `Dockerfile` | python:3.10-slim + ffmpeg + faster-whisper; corrige `uvicorn main:app` |
| `main.py` | API FastAPI (`POST /transcrever`, `GET /health`), upload até 25 MB |
| `docker-compose.yml` | Sobe o container com bind `127.0.0.1`, modelo em volume |
| `nginx-whisper.conf` | Server block com whitelist (158.220.99.24 + localhost) |

## Deploy na VPS 40

```bash
# 1. Código no servidor
sudo mkdir -p /opt/whisper-stt && cd /opt/whisper-stt
# (copiar Dockerfile, main.py, docker-compose.yml, nginx-whisper.conf)

# 2. Subir o Docker (bind apenas em 127.0.0.1)
docker compose up -d --build
# O 1º boot baixa o modelo (~1,5 GB do HuggingFace) — pode demorar; o volume
# whisper_models persiste o cache para as próximas.

# 3. Testar localmente (dentro da VPS)
curl -s http://127.0.0.1:8000/health
curl -s -F "file=@teste.mp3" http://127.0.0.1:8000/transcrever

# 4. Nginx
sudo cp nginx-whisper.conf /etc/nginx/sites-available/whisper
sudo ln -sf /etc/nginx/sites-available/whisper /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 5. SSL (DNS de stt.saudeplanner.com.br precisa apontar para esta VPS)
sudo certbot --nginx -d stt.saudeplanner.com.br
```

## Uso

```bash
curl -X POST https://stt.saudeplanner.com.br/transcrever \
     -H "Authorization: Bearer <token>" \
     -F "file=@audio.ogg"
# → {"texto": "...", "idioma": "pt", "duracao": 12.34}
```

Fora da whitelist: `403 Forbidden` (não chega ao Whisper).

## Diferenças em relação ao guia original

1. **Bug corrigido:** `uvicorn main.py` → `uvicorn main:app` (o original não sobe).
2. `tempfile.mkstemp` único por requisição (evita colisão com chamadas simultâneas).
3. Endpoint `GET /health` + healthcheck do container.
4. Cache do modelo em volume (não re-baixa ~1,5 GB a cada recriação do container).
5. Limite de upload (25 MB) validado **dentro** da API, além do Nginx.
6. `docker compose` em vez de `docker run` (recriação/gestão mais simples).
7. Timeout do proxy elevado para 300s (áudios longos).
