# 🖥️ Servidores - Documentação e Configurações

Esta pasta contém toda a documentação relacionada a servidores, configurações de deploy e ambientes.

---

## 📁 Estrutura de Organização

### Por Ambiente

Cada ambiente possui sua própria documentação completa:

- **Desenvolvimento (Local)**
  - Configuração de ambiente local
  - Docker Compose para desenvolvimento
  - Guias de troubleshooting local

- **Homologação (Staging)**
  - Servidores de teste e validação
  - Configurações de homologação
  - Scripts de deploy automatizado

- **Produção**
  - Servidores de produção
  - Configurações de alta disponibilidade
  - Procedimentos de deploy e rollback

---

## 📋 Documentos Disponíveis

### Homologação

- **`SERVIDOR_HOMOLOGACAO_CONTABO.md`**
  - Documentação completa do servidor de homologação
  - IP: 167.86.97.142 (Contabo VPS)
  - Guia passo a passo de configuração
  - Segurança, backup, monitoramento
  - Troubleshooting completo

- **`SERVIDOR_HOMOLOGACAO_README.md`**
  - Quick start para deploy rápido
  - Comandos essenciais
  - Checklist de validação

---

## 🔗 Arquivos Relacionados

### Configurações de Ambiente

Localizados em `MODULARIZACAO/`:

- `.env.example` - Template geral
- `.env.homologacao` - Configuração para homologação
- `.env.producao` - Configuração para produção (futuro)

### Scripts de Deploy

Localizados em `MODULARIZACAO/scripts/`:

- `deploy_homologacao.sh` - Deploy automático para homologação
- `smoke_tests.sh` - Testes de validação
- `backup.sh` - Scripts de backup (futuro)

---

## 🚀 Quick Links

### Homologação (Contabo)

| Recurso | URL/Comando |
|---------|-------------|
| **SSH** | `ssh root@167.86.97.142` |
| **Portal** | http://167.86.97.142:3001 |
| **APIs** | http://167.86.97.142:8001-8006/docs |
| **Grafana** | http://167.86.97.142:3000 |
| **Deploy** | `./scripts/deploy_homologacao.sh` |

### Desenvolvimento (Local)

| Recurso | URL/Comando |
|---------|-------------|
| **Portal** | http://localhost:3001 |
| **APIs** | http://localhost:8001-8006/docs |
| **Grafana** | http://localhost:3000 |
| **Deploy** | `docker-compose -f docker-compose.full.yml up -d` |

---

## 📊 Inventário de Servidores

### SERVER 05 - INTELLICARE (Homologação)

| Item | Valor |
|------|-------|
| **Provedor** | Contabo VPS |
| **IP** | 167.86.97.142 |
| **vCPU** | 12 Cores |
| **RAM** | 48 GB |
| **Disco** | 250 GB NVMe |
| **Rede** | 800 Mbit/s |
| **Custo** | USD 20.80/mês |
| **Ambiente** | Homologação |
| **Status** | ✅ Ativo |

---

## 🔐 Segurança

### Credenciais

**⚠️ IMPORTANTE:** Credenciais sensíveis NÃO devem ser versionadas!

- Senhas de produção: usar gerenciador de senhas (1Password, Bitwarden, etc)
- Chaves SSH: armazenar localmente, nunca no repositório
- Tokens de API: usar variáveis de ambiente

### Acesso aos Servidores

1. **SSH com chave pública** (obrigatório para produção)
2. **Fail2Ban** configurado em todos os servidores
3. **Firewall (UFW)** ativo e restritivo
4. **Logs de acesso** monitorados

---

## 📝 Convenções de Nomenclatura

### Arquivos de Documentação

```
SERVIDOR_<AMBIENTE>_<PROVEDOR>.md
```

Exemplos:
- `SERVIDOR_HOMOLOGACAO_CONTABO.md`
- `SERVIDOR_PRODUCAO_AWS.md`
- `SERVIDOR_DESENVOLVIMENTO_LOCAL.md`

### Arquivos de Configuração

```
.env.<ambiente>
```

Exemplos:
- `.env.homologacao`
- `.env.producao`
- `.env.staging`

### Scripts de Deploy

```
deploy_<ambiente>.sh
```

Exemplos:
- `deploy_homologacao.sh`
- `deploy_producao.sh`
- `deploy_staging.sh`

---

## 🔄 Fluxo de Deploy

```
Desenvolvimento (Local)
    ↓
    git push
    ↓
Homologação (Contabo)
    ↓
    Testes e Validação
    ↓
Produção (AWS/Azure)
```

---

## 📚 Documentação Adicional

- **Deploy Geral:** `../GUIA_DEPLOY.md` (raiz do MODULARIZACAO)
- **Docker Compose:** `../../docker-compose.full.yml`
- **Smoke Tests:** `../../scripts/smoke_tests.sh`
- **Arquitetura:** `../ARQUITETURA_E_DADOS/`

---

## ✅ Checklist de Novo Servidor

Ao configurar um novo servidor, seguir:

- [ ] Atualizar sistema operacional
- [ ] Instalar Docker e Docker Compose
- [ ] Configurar firewall (UFW)
- [ ] Configurar SSH com chave pública
- [ ] Instalar Fail2Ban
- [ ] Clonar repositório
- [ ] Configurar arquivo `.env`
- [ ] Executar deploy
- [ ] Validar com smoke tests
- [ ] Configurar backup automático
- [ ] Configurar monitoramento
- [ ] Documentar no inventário
- [ ] Adicionar ao README desta pasta

---

**Última atualização:** 2026-02-21  
**Responsável:** Equipe IntelliCare

