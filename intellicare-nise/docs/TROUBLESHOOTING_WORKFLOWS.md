# 🔧 Troubleshooting - Workflows Kestra

**Versão**: 1.0.0  
**Data**: 15/02/2026  
**Módulo**: IntelliCare NISE

---

## 📋 ÍNDICE

1. [Problemas Comuns](#problemas-comuns)
2. [Erros de Execução](#erros-de-execução)
3. [Problemas de Performance](#problemas-de-performance)
4. [Problemas de Configuração](#problemas-de-configuração)
5. [Ferramentas de Diagnóstico](#ferramentas-de-diagnóstico)

---

## 🚨 PROBLEMAS COMUNS

### 1. Workflow Não Aparece na UI

**Sintomas**:
- Arquivo YAML criado mas workflow não aparece no Kestra
- Lista de workflows vazia

**Diagnóstico**:
```bash
# Verificar se arquivo está montado
docker exec intellicare-kestra ls -la /app/workflows

# Verificar logs do Kestra
docker-compose logs kestra | grep -i error

# Validar sintaxe YAML
docker exec intellicare-kestra kestra flow validate /app/workflows/alerta-critico-notificacao.yml
```

**Soluções**:

1. **Arquivo não montado**:
   ```bash
   # Verificar docker-compose.yml
   # volumes:
   #   - ./kestra:/app/workflows:ro
   
   # Reiniciar Kestra
   docker-compose restart kestra
   ```

2. **Erro de sintaxe YAML**:
   ```bash
   # Validar YAML online: https://www.yamllint.com
   # Verificar indentação (usar espaços, não tabs)
   # Verificar aspas e caracteres especiais
   ```

3. **Namespace incorreto**:
   ```yaml
   # Verificar namespace no YAML
   namespace: intellicare  # Deve ser exatamente "intellicare"
   ```

---

### 2. Workflow Falha com "Connection Refused"

**Sintomas**:
- Workflow falha ao chamar serviços externos (NISE, Oswaldo)
- Erro: `Connection refused` ou `Host not found`

**Diagnóstico**:
```bash
# Verificar se serviços estão rodando
docker-compose ps

# Testar conectividade do Kestra
docker exec intellicare-kestra curl http://nise:8000/health
docker exec intellicare-kestra curl http://oswaldo:8002/health

# Verificar network Docker
docker network inspect intellicare_default
```

**Soluções**:

1. **Serviço não está rodando**:
   ```bash
   # Subir serviço
   docker-compose up -d nise oswaldo
   
   # Verificar logs
   docker-compose logs -f nise
   ```

2. **URL incorreta**:
   ```yaml
   # ❌ ERRADO (localhost não funciona dentro do container)
   uri: "http://localhost:8000/api/v1/..."
   
   # ✅ CORRETO (usar nome do serviço Docker)
   uri: "http://nise:8000/api/v1/..."
   ```

3. **Network incorreta**:
   ```bash
   # Verificar se Kestra está na mesma network
   docker inspect intellicare-kestra | grep NetworkMode
   
   # Reconectar à network
   docker network connect intellicare_default intellicare-kestra
   ```

---

### 3. Trigger Schedule Não Executa

**Sintomas**:
- Trigger schedule configurado mas workflow não executa automaticamente
- Execução manual funciona

**Diagnóstico**:
```bash
# Verificar se trigger está habilitado
curl http://localhost:8080/api/v1/flows/intellicare/alerta-critico-notificacao/triggers

# Verificar próxima execução agendada
curl http://localhost:8080/api/v1/flows/intellicare/alerta-critico-notificacao/triggers/schedule_diario

# Verificar timezone do Kestra
docker exec intellicare-kestra date
```

**Soluções**:

1. **Trigger desabilitado**:
   ```bash
   # Habilitar trigger
   curl -X PUT http://localhost:8080/api/v1/flows/intellicare/alerta-critico-notificacao/triggers/schedule_diario/enable
   ```

2. **Cron expression incorreta**:
   ```yaml
   # Validar em https://crontab.guru
   
   # ❌ ERRADO
   cron: "0 2 * * *"  # Pode estar em timezone diferente
   
   # ✅ CORRETO (especificar timezone)
   cron: "0 2 * * *"
   timezone: "America/Sao_Paulo"
   ```

3. **Kestra não está processando schedules**:
   ```bash
   # Verificar logs
   docker-compose logs kestra | grep -i schedule
   
   # Reiniciar Kestra
   docker-compose restart kestra
   ```

---

### 4. Secrets Não Funcionam

**Sintomas**:
- Workflow falha com erro de autenticação
- Erro: `Invalid credentials` ou `Unauthorized`

**Diagnóstico**:
```bash
# Listar secrets
curl http://localhost:8080/api/v1/secrets?namespace=intellicare

# Verificar uso no workflow
grep -r "secret(" kestra/
```

**Soluções**:

1. **Secret não configurado**:
   ```bash
   # Criar secret
   curl -X POST http://localhost:8080/api/v1/secrets \
     -H "Content-Type: application/json" \
     -d '{
       "key": "SMTP_PASSWORD",
       "value": "senha_secreta",
       "namespace": "intellicare"
     }'
   ```

2. **Nome do secret incorreto**:
   ```yaml
   # ❌ ERRADO (case-sensitive)
   password: "{{ secret('smtp_password') }}"
   
   # ✅ CORRETO
   password: "{{ secret('SMTP_PASSWORD') }}"
   ```

3. **Namespace incorreto**:
   ```bash
   # Secret deve estar no namespace correto
   # Criar no namespace "intellicare" ou global
   ```

---

### 5. Workflow Muito Lento

**Sintomas**:
- Workflow demora muito para executar
- Timeout em tasks

**Diagnóstico**:
```bash
# Verificar tempo de execução
curl http://localhost:8080/api/v1/executions/{execution_id}

# Verificar recursos do Kestra
docker stats intellicare-kestra

# Verificar logs de performance
docker-compose logs kestra | grep -i "duration"
```

**Soluções**:

1. **Aumentar workers**:
   ```yaml
   # docker-compose.yml
   kestra:
     command: server standalone --worker-thread=8  # Aumentar de 4 para 8
   ```

2. **Adicionar paralelização**:
   ```yaml
   # ❌ LENTO (sequencial)
   - id: processar_pacientes
     type: io.kestra.plugin.core.flow.EachSequential
   
   # ✅ RÁPIDO (paralelo)
   - id: processar_pacientes
     type: io.kestra.plugin.core.flow.EachParallel
     concurrent: 5  # Processar 5 por vez
   ```

3. **Adicionar timeout**:
   ```yaml
   - id: buscar_paciente
     type: io.kestra.plugin.core.http.Request
     uri: "http://nise:8000/api/v1/..."
     timeout: PT30S  # Timeout de 30 segundos
   ```

4. **Otimizar queries**:
   ```bash
   # Adicionar índices no banco
   # Usar cache (Redis)
   # Limitar número de registros processados
   ```

---

## ❌ ERROS DE EXECUÇÃO

### Erro: "Task Failed with Status Code 404"

**Causa**: Endpoint não encontrado.

**Solução**:
```yaml
# Verificar URL
uri: "http://nise:8000/api/v1/oswaldo/paciente/{{ inputs.paciente_id }}/resumo"

# Testar manualmente
curl http://localhost:8000/api/v1/oswaldo/paciente/PAC001/resumo
```

---

### Erro: "Task Failed with Status Code 500"

**Causa**: Erro interno no serviço.

**Solução**:
```bash
# Verificar logs do serviço
docker-compose logs nise | tail -100

# Verificar dados de entrada
# Validar que inputs estão corretos
```

---

### Erro: "Timeout Waiting for Response"

**Causa**: Serviço demorou muito para responder.

**Solução**:
```yaml
# Aumentar timeout
- id: buscar_paciente
  type: io.kestra.plugin.core.http.Request
  timeout: PT2M  # 2 minutos
```

---

### Erro: "Invalid JSON Response"

**Causa**: Resposta não é JSON válido.

**Solução**:
```bash
# Verificar resposta do serviço
curl http://localhost:8000/api/v1/... -v

# Adicionar validação no workflow
- id: validar_resposta
  type: io.kestra.plugin.core.flow.If
  condition: "{{ outputs.buscar_paciente.body != null }}"
```

---

## 🐌 PROBLEMAS DE PERFORMANCE

### Workflow Processa Muitos Registros

**Problema**: Workflow processa milhares de pacientes e demora horas.

**Solução**:
```yaml
# Adicionar paginação
- id: buscar_pacientes
  type: io.kestra.plugin.core.http.Request
  uri: "http://oswaldo:8002/api/v1/pacientes?limit=100&offset={{ taskrun.value }}"

# Processar em lotes
- id: processar_lotes
  type: io.kestra.plugin.core.flow.EachParallel
  value: [0, 100, 200, 300, 400]  # Offsets
  concurrent: 5
```

---

### Muitas Execuções Simultâneas

**Problema**: Muitos workflows executando ao mesmo tempo sobrecarregam o sistema.

**Solução**:
```yaml
# Adicionar concurrency limit
concurrency:
  limit: 3  # Máximo 3 execuções simultâneas
  behavior: QUEUE  # Enfileirar execuções extras
```

---

## ⚙️ PROBLEMAS DE CONFIGURAÇÃO

### Database Connection Error

**Sintomas**: Kestra não consegue conectar ao PostgreSQL.

**Solução**:
```bash
# Verificar PostgreSQL
docker-compose logs postgres

# Testar conexão
docker exec intellicare-kestra psql -U intellicare -h postgres -d intellicare_kestra -c "SELECT 1"

# Verificar variáveis de ambiente
docker exec intellicare-kestra env | grep KESTRA
```

---

### Workflows Desaparecem Após Restart

**Problema**: Workflows somem após reiniciar Kestra.

**Solução**:
```yaml
# Usar repository type = postgres (não memory)
environment:
  - KESTRA_CONFIGURATION_REPOSITORY_TYPE=postgres
```

---

## 🛠️ FERRAMENTAS DE DIAGNÓSTICO

### 1. Kestra CLI

```bash
# Validar workflow
docker exec intellicare-kestra kestra flow validate /app/workflows/alerta-critico-notificacao.yml

# Testar workflow
docker exec intellicare-kestra kestra flow test /app/workflows/alerta-critico-notificacao.yml
```

### 2. Logs Detalhados

```bash
# Logs do Kestra
docker-compose logs -f kestra

# Logs de execução específica
curl http://localhost:8080/api/v1/executions/{execution_id}/logs

# Filtrar por nível
docker-compose logs kestra | grep ERROR
```

### 3. Métricas

```bash
# Estatísticas de execuções
curl http://localhost:8080/api/v1/stats/executions

# Execuções por status
curl http://localhost:8080/api/v1/executions?state=FAILED&size=10
```

---

**Última atualização**: 15/02/2026  
**Versão do guia**: 1.0.0  
**Autor**: Equipe IntelliCare

