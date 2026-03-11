# Guia Prático e Benefícios: Adoção de Git Worktrees

**Status:** Complemento à Norma `20260309-1500_NORMA_GIT_WORKTREES.md`
**Objetivo:** Explicar o valor arquitetônico da decisão e mapear os pontos de atenção práticos no dia a dia do desenvolvedor IntelliCare.

---

## 🚀 Por que Git Worktrees é um divisor de águas no IntelliCare?

Em projetos complexos baseados em múltiplos microsserviços (atualmente 14 módulos FastAPI + 1 frontend React), a abordagem de Worktrees soluciona alguns dos problemas mais silenciosos e custosos no fluxo de desenvolvimento:

### 1. O Fim do "Inferno de Dependências Python"
Com 14 projetos distintos que podem possuir exigências diferentes no `pyproject.toml` e necessitam da compilação cruzada do `intellicare-core`, alternar entre branches (`feature/X` para `fix/Y`) no mesmo diretório frequentemente corrompia os *Virtualenvs* (ambientes virtuais) locais. 
**A Solução:** Ao usar um diretório por worktree, **cada demanda possui seu próprio ambiente virtual isolado completo e intocável**. O desenvolvedor não perde mais tempo reinstalando pacotes ou consertando erros de `ModuleNotFoundError` ao trocar de task.

### 2. Context-Switching (Troca de Contexto) 100% Seguro
No fluxo tradicional (`git checkout`), se o dev estiver no meio da `DEM-007` e surgir um bug crítico em produção/staging, ele precisa executar um `git stash` (arriscado), mudar a branch, reconstruir os containers, resolver o bug, e depois tentar voltar para a branch anterior (frequentemente perdendo arquivos não rastreados ou estado local).
**A Solução:** Com Worktrees, as alterações da `DEM-007` ficam estacionadas no diretório `.worktrees/DEM-007...`. O dev simplesmente navega (`cd`) para o diretório de `staging` ou para um worktree de `hotfix`, resolve o problema, e depois retorna à pasta da `DEM-007` que permaneceu perfeitamente intacta, com o servidor rodando e os arquivos abertos.

### 3. Staging como "Single Source of Truth" (Fonte Única da Verdade)
Manter a pasta principal (`C:\...\INTELLICARE`) eternamente travada na branch `staging` cria uma âncora de segurança. O desenvolvedor sempre terá uma cópia executável e limpa garantida do ambiente de homologação. Isso elimina o viés do "funciona na minha máquina" e permite testar o `docker-compose.full.yml` com a certeza de que é a versão base aprovada, sem sujeiras de desenvolvimento.

---

## ⚠️ Pontos de Atenção Práticos (O que muda no dia a dia)

Dado que cada `Worktree` cria uma cópia espelho isolada dos arquivos rastreados da branch, arquivos **não rastreados (`untracked`)** e ignorados (`.gitignore`) não são copiados automaticamente.

### 1. Arquivos de Ambiente (`.env`)
Sempre que o dev (ou o agente) inicializar uma nova demanda em `.worktrees/DEM-XXX...`, os arquivos `.env` não estarão presentes (pois são ignorados no Git).
**Ação Necessária:** O primeiro passo na nova pasta é sempre copiar o `.env` do ambiente padrão.
```bash
# Estando dentro da pasta do novo Worktree:
cp ../../.env.example .env
# Ou copiar o .env já configurado da pasta raiz:
cp ../../.env .env
```

### 2. Conflitos de Nomenclatura no Docker Compose
Por padrão, o comando `docker compose up -d` utiliza o nome da pasta atual como "Project Name" para prefixar os containers e as redes (ex: arquivos no worktree `DEM-007_FEATURE` vão criar containers chamados `dem-007_feature-intellicare-api-1`).
Isso é útil para rodar múltiplos ambientes paralelos, mas pode causar duplicação drástica de uso de RAM/CPU, ou confusões de rede, caso os containers base (banco, redis) também sejam duplicados.
**Ação Necessária:** Para garantir que o Worktree atual atualize os containers locais oficiais do projeto (sobrescrevendo os de staging e usando a mesma rede/volumes do setup local), deve-se usar a flag `-p` indicando o nome base do projeto:
```bash
docker compose -p intellicare -f docker-compose.full.yml up -d
```
*Isso garante que, independentemente de qual Worktree o dev esteja operando, o Docker atuará sobre a stack `intellicare` original.*

### 3. Limpeza Constante
Devido à duplicação dos repositórios no disco (incluindo módulos `node_modules` pesados do React e os `venv` do Python), Worktrees antigos inativos podem consumir gigabytes rapidamente.
**Ação Necessária:** Aplicar rigorosamente a regra do `git worktree remove` logo após a aprovação da PR daquela demanda, garantindo a saúde do armazenamento local.
