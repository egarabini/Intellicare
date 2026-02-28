# 🧪 Teste e Deploy - Roteamento de Domínios Raiz

**Data:** 2026-02-26  
**Versão:** 2.0.0  
**Status:** ✅ **PRONTO PARA TESTE**

---

## 📋 Visão Geral

Este guia cobre:
1. ✅ **Teste Local** - Validar configuração sem afetar produção
2. ✅ **Deploy Staging** - Testar em ambiente de homologação
3. ✅ **Deploy Produção** - Aplicar em produção com rollback

---

## 🧪 FASE 1: Teste Local (5 minutos)

### 1.1. Verificar Arquivo de Configuração

```bash
# Verificar se arquivo existe
ls -la ./traefik/dynamic/routes-root-domains.yml

# Ver conteúdo
cat ./traefik/dynamic/routes-root-domains.yml
```

**Esperado:** Arquivo existe e contém as rotas de redirecionamento

---

### 1.2. Validar Sintaxe YAML

```bash
# Instalar yamllint (se não tiver)
pip install yamllint

# Validar sintaxe
yamllint ./traefik/dynamic/routes-root-domains.yml
```

**Esperado:** Sem erros de sintaxe

---

### 1.3. Teste com Docker Compose Local

```bash
cd .

# Subir Traefik em modo dev (sem HTTPS)
docker compose -f docker-compose.full.yml -f docker-compose.traefik-dev.yml up -d traefik

# Aguardar 10 segundos
sleep 10

# Verificar logs do Traefik
docker logs intellicare-traefik --tail 50
```

**Esperado:** 
- ✅ Traefik iniciou sem erros
- ✅ Logs mostram "Configuration loaded"
- ✅ Sem erros de parsing YAML

---

### 1.4. Verificar Rotas no Dashboard Traefik

```bash
# Abrir dashboard Traefik
# http://localhost:8080/dashboard/

# Ou via curl
curl http://localhost:8080/api/http/routers | jq '.[] | select(.name | contains("root"))'
```

**Esperado:**
- ✅ Rotas `root-intellicare`, `www-intellicare`, `root-saudeconectada`, `www-saudeconectada` aparecem
- ✅ Status: "enabled"
- ✅ Middleware: "redirect-to-portal-intellicare"

---

### 1.5. Teste com /etc/hosts (Simulação Local)

```bash
# Editar /etc/hosts (Linux/Mac) ou C:\Windows\System32\drivers\etc\hosts (Windows)
sudo nano /etc/hosts

# Adicionar linhas:
127.0.0.1 intellicare.ia.br
127.0.0.1 www.intellicare.ia.br
127.0.0.1 saudeplanner.com.br
127.0.0.1 www.saudeplanner.com.br
127.0.0.1 portal.intellicare.ia.br

# Salvar e sair (Ctrl+X, Y, Enter)
```

**Testar redirecionamento:**

```bash
# Teste 1: intellicare.ia.br
curl -I http://intellicare.ia.br
# Esperado: HTTP/1.1 301 Moved Permanently
# Location: http://portal.intellicare.ia.br/

# Teste 2: www.intellicare.ia.br
curl -I http://www.intellicare.ia.br
# Esperado: HTTP/1.1 301 Moved Permanently
# Location: http://portal.intellicare.ia.br/

# Teste 3: saudeplanner.com.br
curl -I http://saudeplanner.com.br
# Esperado: HTTP/1.1 301 Moved Permanently
# Location: http://portal.intellicare.ia.br/
```

---

### 1.6. Limpar Teste Local

```bash
# Parar Traefik
docker compose -f docker-compose.full.yml -f docker-compose.traefik-dev.yml down traefik

# Remover entradas do /etc/hosts
sudo nano /etc/hosts
# Deletar as 5 linhas adicionadas
```

---

## ✅ Checklist Fase 1 (Teste Local)

- [ ] Arquivo `routes-root-domains.yml` existe
- [ ] Sintaxe YAML válida
- [ ] Traefik iniciou sem erros
- [ ] Rotas aparecem no dashboard
- [ ] Redirecionamento funciona localmente
- [ ] Teste local limpo

**Se TODOS os itens estão ✅, prosseguir para Fase 2**

---

## 🚀 FASE 2: Deploy Staging (10 minutos)

### 2.1. Conectar ao Servidor de Staging

```bash
# SSH no servidor
ssh root@167.86.97.142

# Navegar para diretório
cd /opt/intellicare
```

---

### 2.2. Backup da Configuração Atual

```bash
# Criar backup
mkdir -p /opt/intellicare/backups/$(date +%Y%m%d_%H%M%S)
cp -r traefik/dynamic /opt/intellicare/backups/$(date +%Y%m%d_%H%M%S)/

# Verificar backup
ls -la /opt/intellicare/backups/
```

---

### 2.3. Verificar DNS

```bash
# Verificar se DNS está configurado
dig intellicare.ia.br +short
# Esperado: 167.86.97.142

dig www.intellicare.ia.br +short
# Esperado: 167.86.97.142

dig saudeplanner.com.br +short
# Esperado: 167.86.97.142

dig www.saudeplanner.com.br +short
# Esperado: 167.86.97.142
```

**⚠️ IMPORTANTE:** Se algum DNS não retornar o IP correto, **PARAR** e configurar DNS primeiro!

---

### 2.4. Aplicar Configuração

```bash
# Verificar se arquivo existe
ls -la traefik/dynamic/routes-root-domains.yml

# Se não existir, criar (copiar do local)
# Ou fazer upload via scp:
# scp ./traefik/dynamic/routes-root-domains.yml root@167.86.97.142:/opt/intellicare/traefik/dynamic/

# Validar sintaxe
yamllint traefik/dynamic/routes-root-domains.yml
```

---

### 2.5. Recarregar Traefik

```bash
# Opção 1: Traefik detecta automaticamente (watch: true)
# Aguardar 10 segundos
sleep 10

# Opção 2: Forçar reload (se necessário)
docker restart intellicare-traefik

# Aguardar Traefik iniciar
sleep 15
```

---

### 2.6. Verificar Logs

```bash
# Ver logs do Traefik
docker logs intellicare-traefik --tail 100

# Procurar por erros
docker logs intellicare-traefik 2>&1 | grep -i error

# Procurar por "Configuration loaded"
docker logs intellicare-traefik 2>&1 | grep -i "configuration loaded"
```

**Esperado:**
- ✅ "Configuration loaded from file"
- ✅ Sem erros de parsing
- ✅ Rotas carregadas

---

### 2.7. Testar Redirecionamentos

```bash
# Teste 1: intellicare.ia.br
curl -I https://intellicare.ia.br
# Esperado: HTTP/2 301
# Location: https://portal.intellicare.ia.br/

# Teste 2: www.intellicare.ia.br
curl -I https://www.intellicare.ia.br
# Esperado: HTTP/2 301
# Location: https://portal.intellicare.ia.br/

# Teste 3: saudeplanner.com.br
curl -I https://saudeplanner.com.br
# Esperado: HTTP/2 301
# Location: https://portal.intellicare.ia.br/

# Teste 4: www.saudeplanner.com.br
curl -I https://www.saudeplanner.com.br
# Esperado: HTTP/2 301
# Location: https://portal.intellicare.ia.br/
```

---

### 2.8. Testar no Navegador

```bash
# Abrir navegador e testar:
# https://intellicare.ia.br
# → Deve redirecionar para https://portal.intellicare.ia.br

# https://www.intellicare.ia.br
# → Deve redirecionar para https://portal.intellicare.ia.br

# https://saudeplanner.com.br
# → Deve redirecionar para https://portal.intellicare.ia.br
```

---

## ✅ Checklist Fase 2 (Deploy Staging)

- [ ] Backup criado
- [ ] DNS configurado corretamente
- [ ] Arquivo `routes-root-domains.yml` no servidor
- [ ] Traefik recarregado sem erros
- [ ] Logs sem erros
- [ ] Redirecionamentos funcionam (curl)
- [ ] Redirecionamentos funcionam (navegador)
- [ ] Certificados HTTPS gerados

**Se TODOS os itens estão ✅, prosseguir para Fase 3**

---

## 🎯 FASE 3: Validação Final (5 minutos)

### 3.1. Verificar Certificados SSL

```bash
# Verificar certificado
echo | openssl s_client -connect intellicare.ia.br:443 -servername intellicare.ia.br 2>/dev/null | openssl x509 -noout -dates

# Verificar www
echo | openssl s_client -connect www.intellicare.ia.br:443 -servername www.intellicare.ia.br 2>/dev/null | openssl x509 -noout -dates
```

**Esperado:** Certificados Let's Encrypt válidos

---

### 3.2. Verificar Subdomínios Existentes (Não Afetados)

```bash
# Verificar que subdomínios continuam funcionando
curl -I https://portal.intellicare.ia.br
# Esperado: HTTP/2 200 OK

curl -I https://admin.intellicare.ia.br/api/v1/health
# Esperado: HTTP/2 200 OK

curl -I https://api.intellicare.ia.br/v1/oswaldo/api/v1/health
# Esperado: HTTP/2 200 OK
```

---

### 3.3. Smoke Test Completo

```bash
# Executar smoke test
cd /opt/intellicare
python3 scripts/smoke_tests.py
```

**Esperado:** Todos os testes passam

---

## ✅ Checklist Fase 3 (Validação Final)

- [ ] Certificados SSL válidos
- [ ] Subdomínios existentes funcionam
- [ ] Smoke tests passam
- [ ] Sem erros nos logs
- [ ] Performance normal

**Se TODOS os itens estão ✅, deploy COMPLETO!**

---

## 🔄 Rollback (Se Necessário)

Se algo der errado:

```bash
# 1. Restaurar backup
BACKUP_DIR=$(ls -t /opt/intellicare/backups/ | head -1)
cp -r /opt/intellicare/backups/$BACKUP_DIR/dynamic/* traefik/dynamic/

# 2. Reiniciar Traefik
docker restart intellicare-traefik

# 3. Verificar
docker logs intellicare-traefik --tail 50
```

---

## 📊 Resumo de Comandos Rápidos

### Teste Local
```bash
cd .
yamllint traefik/dynamic/routes-root-domains.yml
docker compose -f docker-compose.full.yml -f docker-compose.traefik-dev.yml up -d traefik
curl -I http://localhost:8080/api/http/routers
```

### Deploy Staging
```bash
ssh root@167.86.97.142
cd /opt/intellicare
cp -r traefik/dynamic /opt/intellicare/backups/$(date +%Y%m%d_%H%M%S)/
docker restart intellicare-traefik
curl -I https://intellicare.ia.br
```

### Rollback
```bash
BACKUP_DIR=$(ls -t /opt/intellicare/backups/ | head -1)
cp -r /opt/intellicare/backups/$BACKUP_DIR/dynamic/* traefik/dynamic/
docker restart intellicare-traefik
```

---

**Criado por:** Augment Agent  
**Data:** 2026-02-26  
**Versão:** 2.0.0  
**Status:** ✅ **PRONTO PARA EXECUÇÃO**

