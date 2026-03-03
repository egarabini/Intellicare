# IntelliCare — Fluxo de Desenvolvimento e Deploy

> **Leia antes de fazer qualquer alteração no projeto.**  
> Não seguir este fluxo quebra o ambiente de outros desenvolvedores e o servidor de staging.

---

## 🗺️ Visão Geral

```
Sua máquina (dev)
      │
      │  1. Edita + testa local
      │  2. git commit + push → origin/staging
      ▼
GitHub (branch: staging)
      │
      │  3. Servidor puxa do git
      ▼
Servidor de Staging (167.86.97.142)
      │
      │  4. docker restart dos containers
      ▼
Ambiente de Homologação ✅
```

---

## ✅ O Fluxo Correto

### Passo 1 — Trabalhe SEMPRE localmente
- Faça as alterações na sua máquina usando VS Code / IDE
- **NUNCA** edite arquivos diretamente no servidor

### Passo 2 — Commit e push para o branch `staging`
```bash
git checkout staging
git add -A
git commit -m "feat: descrição da alteração"
git push origin staging
```

### Passo 3 — Use o script de deploy automático

No terminal do VS Code (PowerShell):
```powershell
.\scripts\deploy_staging.ps1
# ou com mensagem de commit direta:
.\scripts\deploy_staging.ps1 -Message "feat: nova tela de pacientes"
# se mudou o portal (frontend React), adicione -RebuildPortal:
.\scripts\deploy_staging.ps1 -Message "fix: layout" -RebuildPortal
```

O script faz **tudo automaticamente**:
- commit + push para o git
- SSH no servidor sem senha
- `git pull origin staging` no servidor
- restart dos containers Docker
- exibe o status final

---

## ❌ O Que NUNCA Fazer

| Proibido | Por quê |
|----------|---------|
| Editar arquivos diretamente no servidor | Suas mudanças somem no próximo `git pull` |
| `docker compose ... up -d --build` no servidor sem `git pull` antes | Deploy sem o código mais recente |
| Commitar só em `develop` sem fazer merge em `staging` | O servidor não vê as alterações |
| Commitar só em `main` sem passar por `staging` | Vai para produção sem homologação |
| Alterar `.env.full` no servidor manualmente | Será sobrescrito pelo git |

---

## 🌿 Estrutura de Branches

| Branch | Ambiente | Quem usa |
|--------|----------|----------|
| `develop` | Local / dev | Desenvolvimento do dia a dia |
| `staging` | Servidor 167.86.97.142 | Homologação — o servidor sincroniza com este branch |
| `main` | Produção | Apenas releases aprovadas |

**Fluxo entre branches:**
```
develop → (merge) → staging → (merge) → main
```

---

## 🔑 Pré-requisito: SSH sem senha (Windows)

O script de deploy usa SSH. Configure **uma única vez** por máquina:

```powershell
# 1. Gerar chave SSH (no PowerShell — só se não tiver)
ssh-keygen -t ed25519 -C "seu-email@empresa.com"
# Pressione Enter em tudo (sem passphrase) para não pedir senha depois

# 2. Ver a chave pública gerada
cat "$env:USERPROFILE\.ssh\id_ed25519.pub"
```

**Copie a linha inteira** que começa com `ssh-ed25519 ...`

```powershell
# 3. No PuTTY (conectado ao servidor), cole:
#    mkdir -p ~/.ssh && echo "COLE_SUA_CHAVE_AQUI" >> ~/.ssh/authorized_keys
#    && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys

# 4. Testar aqui no PowerShell (deve responder OK sem pedir senha)
ssh root@167.86.97.142 "echo OK"
```

> ⚠️ `ssh-copy-id` **não existe no Windows** — use o método manual acima via PuTTY.

---

## 🐳 Quando Fazer Rebuild do Docker

| Tipo de alteração | Rebuild necessário? | Flag no script |
|-------------------|--------------------|-|
| Python (backend) | ❌ Não — basta restart | (nenhuma) |
| React/TypeScript (portal) | ✅ Sim — rebuild obrigatório | `-RebuildPortal` |
| Dockerfile | ✅ Sim | `-RebuildPortal` |
| docker-compose*.yml | ❌ Não — só restart | (nenhuma) |
| .env.full | ❌ Não — só restart | (nenhuma) |

> **Por quê o portal precisa de rebuild?**  
> As variáveis `VITE_*` (URLs dos módulos) são compiladas dentro do bundle JavaScript  
> durante o `npm run build`. Se você só reiniciar o container sem rebuildar,  
> as URLs antigas ficam no bundle e o portal chama o endereço errado.

---

## 🚨 Em Caso de Emergência no Servidor

Se algo quebrou e você precisa reverter:

```bash
# No servidor — reverter para o commit anterior
git reset --hard HEAD~1
docker compose -f docker-compose.full.yml up -d
```

---

## 📋 Resumo Rápido

```
1. Editou? → salva local
2. Testou? → git commit + push staging
3. Executa: .\scripts\deploy_staging.ps1
4. Pronto!
```

**Dúvidas?** Fale com o líder técnico antes de fazer deploy manual no servidor.

