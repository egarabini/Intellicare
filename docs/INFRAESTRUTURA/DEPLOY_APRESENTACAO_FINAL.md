# Deploy Final: apresentacao.intellicare.ia.br

## ⚠️ Situação Atual

A conexão SSH está com timeouts persistentes, impedindo o deploy automático. Este documento contém todas as instruções para você executar manualmente quando tiver acesso ao servidor.

---

## ✅ O Que Já Foi Feito

1. ✅ **Portal React** - Corrigido erro JavaScript `toUpperCase()` e deployado
2. ✅ **Configuração Git** - Todos os arquivos commitados e enviados para GitHub
3. ✅ **Docker Compose** - Criado `intellicare-apresentacao/docker-compose.yml`
4. ✅ **Traefik Routes** - Criado `traefik/dynamic/routes-intellicare.yml` (backup)
5. ✅ **Scripts** - Criados scripts de deploy automatizado

---

## 🚀 Comandos para Executar no Servidor

### Opção 1: Comandos Manuais (Recomendado)

Conecte-se ao servidor via SSH e execute:

```bash
# 1. Ir para o diretório do projeto
cd /opt/intellicare/intellicare

# 2. Remover arquivo conflitante (se existir)
rm -f traefik/dynamic/routes-intellicare.yml

# 3. Fazer pull das mudanças do GitHub
git pull origin master

# 4. Ir para o diretório do módulo apresentação
cd intellicare-apresentacao

# 5. Iniciar o container via Docker Compose
docker-compose up -d

# 6. Verificar se o container está rodando
docker ps --filter name=apresentacao

# 7. Ver logs (opcional)
docker logs intellicare-apresentacao

# 8. Aguardar 30-60 segundos para o certificado SSL

# 9. Testar
curl -I https://apresentacao.intellicare.ia.br
```

### Opção 2: Script Bash (Alternativa)

```bash
# Fazer upload do script
cd /opt/intellicare/intellicare
bash scripts/deploy_apresentacao.sh
```

---

## 🔍 Verificação

Após executar os comandos, você deve ver:

### Container Rodando
```
CONTAINER ID   IMAGE          STATUS         PORTS      NAMES
xxxxx          nginx:alpine   Up X seconds   80/tcp     intellicare-apresentacao
```

### Teste HTTP
```bash
curl -I https://apresentacao.intellicare.ia.br
```

**Resultado esperado:**
```
HTTP/2 200
content-type: text/html
date: ...
```

---

## 📁 Arquivos Criados

Todos estes arquivos já estão no GitHub (commit `27d8d0f`):

1. **`intellicare-apresentacao/docker-compose.yml`**
   - Container Nginx com Traefik labels
   - Auto-discovery via Docker
   - Certificado SSL automático

2. **`traefik/dynamic/routes-intellicare.yml`**
   - Rota Traefik (backup, não necessária com labels)

3. **`scripts/deploy_apresentacao.sh`**
   - Script Bash para deploy

4. **`scripts/deploy_apresentacao.ps1`**
   - Script PowerShell para deploy

5. **`scripts/fix_apresentacao.sh`**
   - Script de correção rápida

---

## 🎯 Como Funciona

### Docker Compose + Traefik Labels

O arquivo `docker-compose.yml` usa **labels do Traefik** para configuração automática:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.apresentacao.rule=Host(`apresentacao.intellicare.ia.br`)"
  - "traefik.http.routers.apresentacao.entrypoints=websecure"
  - "traefik.http.routers.apresentacao.tls.certresolver=letsencrypt"
  - "traefik.http.services.apresentacao.loadbalancer.server.port=80"
```

**Vantagens:**
- ✅ Traefik detecta automaticamente o container
- ✅ Cria a rota para `apresentacao.intellicare.ia.br`
- ✅ Solicita certificado Let's Encrypt automaticamente
- ✅ Não precisa editar arquivos de configuração manualmente

---

## 🐛 Troubleshooting

### Problema: Container não inicia

```bash
# Ver logs
docker logs intellicare-apresentacao

# Verificar se o diretório existe
ls -la /opt/intellicare/intellicare/intellicare-apresentacao/apresentacao/web/
```

### Problema: 404 Not Found

```bash
# Verificar se Traefik detectou o container
docker logs intellicare-traefik | grep apresentacao

# Reiniciar Traefik
docker restart intellicare-traefik
```

### Problema: Certificado SSL não gerado

```bash
# Aguardar 2-3 minutos
# Let's Encrypt pode levar tempo para validar o domínio

# Verificar logs do Traefik
docker logs intellicare-traefik | grep letsencrypt
```

---

## 📊 Status Final

| Item | Status |
|------|--------|
| Portal React | ✅ Funcionando (`https://portal.intellicare.ia.br`) |
| Erro JavaScript | ✅ Corrigido |
| Configuração Apresentação | ✅ No GitHub (commit `27d8d0f`) |
| Docker Compose | ✅ Criado |
| Scripts de Deploy | ✅ Criados |
| Deploy no Servidor | ⏳ **Aguardando execução manual** |

---

## 🌐 URLs Finais

Após o deploy:

- **Portal:** https://portal.intellicare.ia.br ✅
- **Apresentação:** https://apresentacao.intellicare.ia.br ⏳

---

## 📞 Próximos Passos

1. Conecte-se ao servidor via SSH
2. Execute os comandos da **Opção 1** acima
3. Aguarde 30-60 segundos para o certificado SSL
4. Acesse `https://apresentacao.intellicare.ia.br` no navegador
5. Confirme que os slides Reveal.js estão sendo exibidos

---

**Última atualização:** 2026-02-27  
**Commit:** `27d8d0f` - feat: Add apresentacao.intellicare.ia.br subdomain configuration

