# POC — Painel de Ala Hospitalar com Voz

> **Escopo:** validar chat com IA local + entrada/saída por voz, servido em
> `voice.intellicare.ia.br`, como prova de conceito para um futuro módulo de
> controle de painel de ala hospitalar. Depois de validado, o módulo definitivo
> será implementado seguindo o padrão da plataforma (`BaseAgent`, portas 80XX,
> integração com Wanda).

> **Nota sobre "VoiceLab":** o projeto VoiceLab (`F:\BEMCUIDAR-EC\voicelab`) é um
> aplicativo **desktop** de análise acústica de voz (pitch, espectrogramas) — não
> possui interface web nem API, e não serve para este POC. Esta POC usa
> **Ollama + Open WebUI**, que entregam chat com IA local e voz prontos.

## Stack

| Serviço | Imagem | Função |
|---|---|---|
| `voice-poc-ollama` | `ollama/ollama:latest` | LLM local (modelos baixados via `ollama pull`) |
| `voice-poc-webui` | `ghcr.io/open-webui/open-webui:main` | Chat web com **voz** (STT Whisper local + TTS do navegador) |

## Como subir

### 0. Pré-requisitos

- Stack IntelliCare no ar (cria a rede `intellicare_intellicare-network`):
  ```bash
  docker compose -f docker-compose.yml up -d   # ou docker-compose.full.yml
  ```
- DNS: registro A `voice.intellicare.ia.br` → IP do servidor
  (se usar o certificado wildcard `letsencrypt-wildcard`, o `*.intellicare.ia.br`
  já cobre este subdomínio — basta o registro DNS).

### 1. Configurar segredo e subir

```bash
cd voice-poc
echo "WEBUI_SECRET_KEY=$(openssl rand -hex 32)" > .env
docker compose up -d
```

### 2. Baixar um modelo no Ollama

```bash
# Modelo leve para POC em CPU (~4,7 GB). Em GPU, pode usar algo maior.
docker exec voice-poc-ollama ollama pull qwen2.5:7b
```

### 3. Rota no Traefik

Adicione ao `traefik/dynamic/routes-intellicare.yml` (seguindo o padrão do arquivo):

```yaml
    # ── POC Painel de Ala (voz) — voice.intellicare.ia.br ──
    voice-poc:
      rule: "Host(`voice.intellicare.ia.br`)"
      entryPoints:
        - websecure
      service: voice-poc-svc
      tls:
        certResolver: letsencrypt        # ou letsencrypt-wildcard
```

E na seção `services:` do mesmo arquivo:

```yaml
    voice-poc-svc:
      loadBalancer:
        servers:
          - url: "http://voice-poc-webui:8080"
```

O file provider do Traefik observa o diretório — a rota entra sem restart.

### 4. Primeiro acesso

1. Abra `https://voice.intellicare.ia.br` (ou `http://localhost:3080` em teste local).
2. **Registre o primeiro usuário** — ele vira admin automaticamente.
3. Selecione o modelo `qwen2.5:7b` no topo do chat.
4. Para voz: clique no **microfone** no campo de mensagem (STT) e ative a voz
   nas configurações do chat (TTS fala as respostas).
5. Configuração de áudio fina (modelos de STT/TTS, voz, velocidade):
   Painel Admin → Configurações → Áudio.

## Segurança

- `WEBUI_AUTH=True` é **obrigatório** — o subdomínio fica público. O `.env`
  com `WEBUI_SECRET_KEY` **não deve ser commitado**.
- O acesso direto `localhost:3080` está bindado em `127.0.0.1` — não exposto.
- Para o módulo definitivo na plataforma: autenticar via Keycloak
  (`intellicare-auth`), não usar o login interno do Open WebUI.

## Ambiente totalmente separado (sem IntelliCare)

No `docker-compose.yml`, troque o bloco `networks:` final por:

```yaml
networks:
  intellicare-network:
    driver: bridge
```

Nesse modo o acesso é apenas `http://localhost:3080` (sem domínio/TLS), a menos
que suba um Traefik próprio no mesmo compose.

## Próximos passos (pós-POC)

1. Definir o módulo definitivo (ex.: `intellicare-ala/`) com `BaseAgent` e os
   3 endpoints obrigatórios (`/health`, `/info`, `/analyze`).
2. STT dedicado (faster-whisper em serviço próprio) se o Whisper embutido no
   Open WebUI não atender latência/acurácia.
3. Integração do LLM via `OLLAMA_URL` já prevista no Wanda
   (`wanda/llm/ollama_provider.py`).
