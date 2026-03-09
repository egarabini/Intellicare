# Instruções Finais - Correção do Oswaldo

**Data:** 2026-02-22  
**Problema:** Container Oswaldo não está pegando o `.env` atualizado com URL encoding

---

## 🎯 Situação Atual

### ✅ Correções Já Aplicadas

1. **`.env` corrigido** - Senhas agora têm URL encoding correto:
   ```
   IntelliCare%40Homolog2026%21Pg  (@ → %40, ! → %21)
   ```

2. **Donabedian**: ✅ RODANDO
3. **Comunicacao**: ✅ RODANDO  
4. **Oswaldo**: ❌ AINDA FALHANDO (usando cache antigo do .env)

---

## 🔧 Solução: Recriar Container Oswaldo

O container Oswaldo precisa ser **completamente recriado** para pegar o novo `.env`.

### Comandos para Executar no Servidor

```bash
# 1. Conectar ao servidor
ssh root@167.86.97.142

# 2. Navegar para o diretório
cd /opt/intellicare/intellicare

# 3. Verificar que o .env está correto
grep "INTELLICARE_OSWALDO_DATABASE_URL" .env
# Deve mostrar: ...IntelliCare%40Homolog2026%21Pg@postgres...

# 4. Parar e remover o container Oswaldo
docker-compose -f docker-compose.full.yml stop oswaldo
docker-compose -f docker-compose.full.yml rm -f oswaldo

# 5. Recriar o container (vai pegar o .env atualizado)
docker-compose -f docker-compose.full.yml up -d oswaldo

# 6. Aguardar 30 segundos
sleep 30

# 7. Verificar status
docker-compose -f docker-compose.full.yml ps oswaldo

# 8. Ver logs
docker logs intellicare-oswaldo --tail 20
```

---

## ✅ Resultado Esperado

Após executar os comandos acima, você deve ver nos logs do Oswaldo:

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
2026-02-22 XX:XX:XX,XXX - oswaldo.api.main - INFO - Starting intellicare-oswaldo v1.0.0
2026-02-22 XX:XX:XX,XXX - oswaldo.api.main - INFO - Environment: development
2026-02-22 XX:XX:XX,XXX - oswaldo.api.main - INFO - Database schema: intellicare_oswaldo
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 🚨 Se Ainda Falhar

Se o erro persistir, execute:

```bash
# Verificar se o .env está sendo montado corretamente no container
docker exec intellicare-oswaldo env | grep DATABASE_URL

# Deve mostrar a URL com %40 e %21
```

Se ainda mostrar a senha sem encoding, o problema é que o Docker Compose está usando variáveis de ambiente do sistema. Nesse caso:

```bash
# Forçar rebuild completo
docker-compose -f docker-compose.full.yml down oswaldo
docker-compose -f docker-compose.full.yml build --no-cache oswaldo
docker-compose -f docker-compose.full.yml up -d oswaldo
```

---

## 📊 Verificação Final de Todos os Módulos

Após corrigir o Oswaldo, verifique todos os 3 módulos:

```bash
docker-compose -f docker-compose.full.yml ps | grep -E "(oswaldo|donabedian|comunicacao)"

# Todos devem mostrar "Up" e "healthy" ou "health: starting"
```

```bash
# Ver logs de todos
docker logs intellicare-oswaldo --tail 10
docker logs intellicare-donabedian --tail 10
docker logs intellicare-comunicacao --tail 10

# Todos devem mostrar "Application startup complete"
```

---

## 📝 Resumo das Correções Aplicadas

1. ✅ Donabedian: Adicionado `intellicare-auth` ao Dockerfile
2. ✅ Donabedian: Tornado imports de `intellicare_auth` opcionais em 7 arquivos
3. ✅ Oswaldo: Adicionado `psycopg[binary]` ao `pyproject.toml`
4. ✅ Comunicacao: Adicionado `psycopg[binary]` ao `pyproject.toml`
5. ✅ Todos: Aplicado URL encoding nas senhas do `.env`
6. ⏳ Oswaldo: Aguardando recriação do container para pegar novo `.env`

---

**Execute os comandos acima e me avise o resultado!** 🚀

