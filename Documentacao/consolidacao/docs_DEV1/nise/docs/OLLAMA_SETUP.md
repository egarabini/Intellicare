# 🤖 OLLAMA SETUP - Local LLM Configuration

---

## 📋 VISÃO GERAL

**Ollama** é usado no NISE para executar LLMs localmente, garantindo:
- 🔒 **Privacidade**: Dados médicos não saem do servidor
- ⚡ **Performance**: Baixa latência (<2s)
- 💰 **Custo**: Sem custos de API externa
- 🎯 **Controle**: Modelos customizáveis

---

## 🚀 INSTALAÇÃO

### **1. Docker (Recomendado)**

```yaml
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    container_name: nise_ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
    networks:
      - nise_network
    restart: unless-stopped

volumes:
  ollama_data:

networks:
  nise_network:
    external: true
```

### **2. Download do Modelo**

```bash
# Entrar no container
docker exec -it nise_ollama bash

# Download do modelo llama2:7b
ollama pull llama2:7b

# Verificar modelos instalados
ollama list
```

---

## 🔧 CONFIGURAÇÃO

### **Variáveis de Ambiente**

```bash
# .env
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama2:7b
OLLAMA_EMBEDDING_MODEL=llama2:7b
OLLAMA_TIMEOUT=60
```

### **Modelos Disponíveis**

| Modelo | Tamanho | RAM | Uso |
|--------|---------|-----|-----|
| **llama2:7b** | 3.8GB | 8GB | Produção (recomendado) |
| llama2:13b | 7.3GB | 16GB | Alta qualidade |
| mistral:7b | 4.1GB | 8GB | Alternativa rápida |
| codellama:7b | 3.8GB | 8GB | Código FHIR |

---

## 📊 PERFORMANCE

### **Benchmarks (llama2:7b)**

| Métrica | Valor |
|---------|-------|
| **Latência média** | 1.5s |
| **P95** | 2.5s |
| **P99** | 3.5s |
| **Throughput** | ~20 req/min |
| **RAM usage** | 4-6GB |

### **Otimizações**

```bash
# Aumentar contexto (padrão: 2048)
ollama run llama2:7b --ctx-size 4096

# Ajustar temperatura (criatividade)
# 0.0 = determinístico, 1.0 = criativo
# Padrão: 0.7
```

---

## 🧪 TESTES

### **1. Health Check**

```bash
curl http://localhost:11434/api/tags
```

**Resposta esperada**:
```json
{
  "models": [
    {
      "name": "llama2:7b",
      "modified_at": "2026-03-25T10:00:00Z",
      "size": 3825819519
    }
  ]
}
```

### **2. Teste de Geração**

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama2:7b",
  "prompt": "O que é FHIR R4?",
  "stream": false
}'
```

### **3. Teste de Embeddings**

```bash
curl http://localhost:11434/api/embeddings -d '{
  "model": "llama2:7b",
  "prompt": "Patient resource FHIR R4"
}'
```

---

## 🎯 INTEGRAÇÃO COM NISE

### **RAG Service**

```python
from app.services.rag_service import rag_service

# Gerar resposta com RAG
response = await rag_service.generate_response(
    query="Como criar um Patient FHIR R4?",
    use_rag=True
)

print(response["text"])
print(f"Fontes: {response['sources']}")
print(f"Contexto usado: {response['context_used']}")
```

### **Florence Endpoints**

```bash
# Chat com Dr. Nise (usa Ollama via RAG)
curl -X POST http://localhost:8000/api/v1/florence/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quais são os campos obrigatórios de um Patient?",
    "session_id": "session-001"
  }'
```

---

## 🔍 MONITORAMENTO

### **Logs**

```bash
# Ver logs do Ollama
docker logs -f nise_ollama

# Métricas de uso
docker stats nise_ollama
```

### **Métricas Importantes**

- **CPU usage**: <80% (ideal)
- **RAM usage**: 4-6GB (llama2:7b)
- **Response time**: <3s (P99)
- **Error rate**: <1%

---

## 🛠️ TROUBLESHOOTING

### **Problema: Modelo não encontrado**

```bash
# Verificar modelos
ollama list

# Re-download
ollama pull llama2:7b
```

### **Problema: Timeout**

```bash
# Aumentar timeout no código
OLLAMA_TIMEOUT=120  # 2 minutos
```

### **Problema: Out of Memory**

```bash
# Usar modelo menor
ollama pull mistral:7b

# Ou aumentar RAM do container
docker-compose.yml:
  ollama:
    deploy:
      resources:
        limits:
          memory: 12G
```

### **Problema: Respostas lentas**

```bash
# Verificar GPU (se disponível)
docker run --gpus all ollama/ollama:latest

# Reduzir contexto
--ctx-size 2048
```

---

## 📚 PROMPTS CUSTOMIZADOS

### **System Message para Dr. Nise**

```python
SYSTEM_MESSAGE = """Você é Dr. Nise, um assistente de IA especializado em 
treinamento médico e recursos FHIR R4. Você ajuda profissionais de saúde a 
aprender sobre interoperabilidade em saúde, padrões FHIR, e melhores práticas 
clínicas. 

Diretrizes:
- Seja educativo e didático
- Use exemplos práticos
- Cite fontes quando possível
- Explique termos técnicos
- Seja empático e encorajador
"""
```

---

## 🚀 PRÓXIMOS PASSOS

1. ✅ Instalação básica (Dia 17)
2. ⏳ Fine-tuning com dados FHIR (Semana 5)
3. ⏳ Otimização de prompts (Semana 6)
4. ⏳ Cache de respostas (Semana 7)
5. ⏳ Multi-model support (Fase 2)

---

**Responsável**: DEV1  
**Data**: 25/03/2026  
**Versão**: 1.0

