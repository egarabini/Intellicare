# ⚠️ INSTRUÇÕES PARA EXECUÇÃO MANUAL DOS TESTES

**Situação**: Os processos automatizados estão sendo interrompidos pelo sistema.  
**Solução**: Executar manualmente seguindo este guia.

---

## 🔧 PASSO 0: PREPARAR AMBIENTE (APENAS UMA VEZ)

### Instalar o módulo donabedian

Abra um terminal e execute:

```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-donabedian
pip install -e .
```

**Aguarde** até ver: `Successfully installed donabedian`

### Verificar instalação da biblioteca intellicare-auth

```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-auth
pip install -e .
```

**Aguarde** até ver: `Successfully installed intellicare-auth`

### Instalar httpx (para testes)

```bash
pip install httpx
```

---

## 🚀 EXECUTAR TESTES (SEMPRE QUE QUISER TESTAR)

### TERMINAL 1: Iniciar Servidor

```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-donabedian
python -m uvicorn src.donabedian.api.main:app --reload --port 8003
```

**Aguarde ver estas mensagens**:
```
INFO:     Uvicorn running on http://0.0.0.0:8003
INFO:     Application startup complete.
INFO:     Starting intellicare-donabedian v1.0.0
🔐 Keycloak authentication enabled
   Realm: bemcuidar
   Client: intellicare-donabedian
   Server: https://keycloak.gsi.srv.br/
```

✅ **Servidor está pronto quando ver "Application startup complete"**

**DEIXE ESTE TERMINAL ABERTO!**

---

### TERMINAL 2: Executar Testes

Abra um **NOVO terminal** e execute:

```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-donabedian
python test_keycloak_integration.py
```

**Pressione ENTER** quando solicitado.

---

## ✅ RESULTADOS ESPERADOS

Você deve ver **4 testes passando**:

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

## ❌ POSSÍVEIS ERROS E SOLUÇÕES

### Erro: "ModuleNotFoundError: No module named 'donabedian'"

**Causa**: Módulo não instalado  
**Solução**: Execute o PASSO 0 acima

```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-donabedian
pip install -e .
```

### Erro: "ModuleNotFoundError: No module named 'intellicare_auth'"

**Causa**: Biblioteca intellicare-auth não instalada  
**Solução**:

```bash
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-auth
pip install -e .
```

### Erro: "ModuleNotFoundError: No module named 'httpx'"

**Causa**: httpx não instalado  
**Solução**:

```bash
pip install httpx
```

### Erro: "Connection refused" ou "Cannot connect to localhost:8003"

**Causa**: Servidor não está rodando  
**Solução**: Volte ao TERMINAL 1 e inicie o servidor

### Erro: "Address already in use" ou "Port 8003 is already in use"

**Causa**: Já existe um servidor rodando na porta 8003  
**Solução**: Mate o processo ou use outra porta:

```bash
# Usar porta diferente
python -m uvicorn src.donabedian.api.main:app --reload --port 8004
```

E no teste, altere `API_BASE_URL` para `http://localhost:8004/api/v1`

---

## 🎯 APÓS OS TESTES

### Se TODOS os testes passarem ✅

1. **Parar o servidor**: Pressione `Ctrl+C` no Terminal 1
2. **Avisar**: "Todos os 4 testes passaram! ✅"
3. **Próximo passo**: Replicar integração para outros módulos

### Se algum teste falhar ❌

1. **Copiar a mensagem de erro completa**
2. **Verificar** se é um dos erros conhecidos acima
3. **Avisar** com o erro completo para análise

---

## 📝 COMANDOS RESUMIDOS

```bash
# PASSO 0 (apenas uma vez)
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-donabedian
pip install -e .
pip install httpx

# TERMINAL 1 (servidor)
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-donabedian
python -m uvicorn src.donabedian.api.main:app --reload --port 8003

# TERMINAL 2 (testes)
cd C:\DOCSHARE\INTELLICARE\MODULARIZACAO\intellicare-donabedian
python test_keycloak_integration.py
```

---

**TUDO PRONTO! EXECUTE OS COMANDOS ACIMA E ME AVISE O RESULTADO!** 🚀

