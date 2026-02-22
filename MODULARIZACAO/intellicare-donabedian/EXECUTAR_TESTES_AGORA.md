# 🚀 EXECUTAR TESTES AGORA - GUIA RÁPIDO

**Status**: ✅ Tudo pronto para testar!  
**Tempo estimado**: 5 minutos

---

## 📋 PASSO A PASSO SIMPLIFICADO

### PASSO 1: Abrir Terminal 1 (Servidor)

1. Abra um **novo terminal** (PowerShell ou CMD)
2. Execute:

```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-donabedian
start_server.bat
```

3. **Aguarde** até ver estas mensagens:
   ```
   INFO:     Application startup complete.
   🔐 Keycloak authentication enabled
      Realm: bemcuidar
      Client: intellicare-donabedian
   ```

4. **DEIXE ESTE TERMINAL ABERTO** (servidor rodando)

---

### PASSO 2: Abrir Terminal 2 (Testes)

1. Abra um **segundo terminal** (PowerShell ou CMD)
2. Execute:

```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-donabedian
run_tests.bat
```

3. **Aguarde** os testes executarem (30-60 segundos)

---

## ✅ RESULTADOS ESPERADOS

Você deve ver:

```
🧪 ========================================================================== 🧪
🧪  TESTES DE INTEGRAÇÃO KEYCLOAK - INTELLICARE-DONABEDIAN
🧪 ========================================================================== 🧪

================================================================================
TESTE 1: Endpoint Público (GET /health)
================================================================================
✅ Status: 200
✅ Response: {'status': 'healthy'}
✅ TESTE PASSOU: Endpoint público acessível sem token

================================================================================
TESTE 2: Endpoint Protegido SEM Token (GET /pillars)
================================================================================
Status: 403
✅ TESTE PASSOU: Endpoint protegido bloqueou acesso sem token

================================================================================
TESTE 3: Endpoint Protegido COM Token Válido (GET /pillars)
================================================================================
Obtendo token do Keycloak...
✅ Token obtido com sucesso (role: intellicare_doctor)
Status: 200
✅ Response: [...]
✅ TESTE PASSOU: Endpoint protegido acessível com token válido

================================================================================
TESTE 4: Endpoint Admin SEM Role Admin (POST /pillars)
================================================================================
Obtendo token de usuário não-admin...
✅ Token obtido (role: intellicare_doctor - NÃO é admin)
Status: 403
✅ TESTE PASSOU: Endpoint admin bloqueou usuário sem role admin

================================================================================
📊 RESUMO DOS TESTES
================================================================================
✅ Teste 1: Endpoint público acessível
✅ Teste 2: Endpoint protegido bloqueia sem token
✅ Teste 3: Endpoint protegido permite com token válido
✅ Teste 4: Endpoint admin bloqueia sem role admin

🎉 INTEGRAÇÃO KEYCLOAK FUNCIONANDO CORRETAMENTE!
================================================================================
```

---

## ❌ SE ALGO DER ERRADO

### Erro: "ModuleNotFoundError: No module named 'httpx'"

**Solução**: Instalar dependências

```bash
pip install httpx
```

### Erro: "Connection refused" ou "Cannot connect"

**Solução**: Servidor não está rodando. Volte ao PASSO 1.

### Erro: "401 Unauthorized" ou "Invalid credentials"

**Solução**: Problema com Keycloak. Verifique:
- Keycloak está acessível: https://keycloak.gsi.srv.br/
- Credenciais no arquivo `.env.keycloak` estão corretas

### Erro: "404 Not Found"

**Solução**: Verifique se o servidor está rodando na porta 8003

---

## 🎯 APÓS OS TESTES

Se **TODOS os 4 testes passarem** ✅:

1. **Parar o servidor** (Ctrl+C no Terminal 1)
2. **Avisar o desenvolvedor**: "Testes passaram com sucesso!"
3. **Próximo passo**: Replicar para outros módulos

Se **algum teste falhar** ❌:

1. **Copiar a mensagem de erro completa**
2. **Avisar o desenvolvedor** com o erro
3. **Aguardar correções**

---

## 📝 COMANDOS RÁPIDOS

### Iniciar servidor:
```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-donabedian
python -m uvicorn src.donabedian.api.main:app --reload --port 8003
```

### Executar testes:
```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-donabedian
python test_keycloak_integration.py
```

### Testar manualmente (com curl):
```bash
# Endpoint público
curl http://localhost:8003/api/v1/health

# Endpoint protegido (sem token - deve retornar 403)
curl http://localhost:8003/api/v1/pillars
```

---

**TUDO PRONTO! PODE EXECUTAR OS TESTES AGORA!** 🚀

