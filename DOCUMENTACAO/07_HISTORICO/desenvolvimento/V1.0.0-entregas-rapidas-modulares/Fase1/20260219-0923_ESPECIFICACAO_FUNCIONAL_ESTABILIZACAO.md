# ESPECIFICACAO_FUNCIONAL — Fase 1: Estabilização

**Versão:** 1.0  
**Data:** 2026-02-19  
**Status:** Aprovada para execução  
**Referência:** `docs/PLANNER-CURSOR/ESTRATEGIA_PROXIMOS_PASSOS.md`

---

## 1. Contexto e Objetivo

O IntelliCare . evoluiu rapidamente com múltiplos módulos Python. Antes de qualquer deploy, é essencial garantir que a demo funcione de ponta a ponta em ambiente local, sem erros críticos. Esta especificação define o escopo da **Fase 1 — Estabilização**.

**Objetivo:** Garantir que todos os serviços da demo sobem e respondem corretamente, com dependências Python isoladas em ambientes virtuais.

---

## 2. Escopo

### 2.1 Dentro do escopo

- Validação da infraestrutura (Postgres, Redis) via Docker Compose
- Validação do `start_demo.bat` e dos 7 processos (6 backends + portal)
- Teste funcional de cada módulo na demo (Oswaldo, Florence, Geralda, Nise, Zilda, Grahame)
- Uso obrigatório de ambiente virtual Python em todos os módulos
- Correção de bloqueadores críticos (serviço não sobe, crash)
- Documentação de issues conhecidos (não bloqueantes)
- Checklist de estabilização preenchido

### 2.2 Fora do escopo

- Deploy em servidor remoto
- Implementação de novos recursos
- Refatoração de código (exceto correções mínimas para estabilidade)
- Integração com módulos não incluídos na demo (comunicacao, conhecimento, donabedian, wanda, etc.)

---

## 3. Requisitos Funcionais

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RF-001 | Infraestrutura (Postgres, Redis) deve subir via `docker-compose up -d` e ficar healthy | Obrigatório |
| RF-002 | Cada módulo Python (Oswaldo, Florence, Geralda, Nise, Zilda, Grahame) deve iniciar sem erro | Obrigatório |
| RF-003 | Portal frontend deve carregar em http://localhost:5173 | Obrigatório |
| RF-004 | Cada módulo deve responder às funcionalidades principais da demo (conforme README_DEMO.md) | Obrigatório |
| RF-005 | Todos os módulos Python devem ser executados em ambiente virtual (venv, poetry ou conda) | Obrigatório |
| RF-006 | Problemas não bloqueantes devem ser documentados em ISSUES_CONHECIDOS.md | Desejável |

---

## 4. Requisitos Não Funcionais

| ID | Requisito | Prioridade |
|----|-----------|------------|
| RNF-001 | Sem conflitos de versão de bibliotecas Python entre módulos (isolamento via ambiente virtual) | Obrigatório |
| RNF-002 | Documentação de como executar cada módulo com seu ambiente virtual | Obrigatório |
| RNF-003 | `start_demo.bat` (ou equivalente) deve refletir o uso de ambientes virtuais | Obrigatório |

---

## 5. Critérios de Aceite

| ID | Critério |
|----|----------|
| CA-001 | Dado o ambiente limpo, quando subir `docker-compose up -d`, então Postgres e Redis ficam healthy |
| CA-002 | Dado o ambiente limpo, quando executar `start_demo.bat` (ou script equivalente), então os 7 processos iniciam sem erro |
| CA-003 | Dado que a demo está rodando, quando acessar http://localhost:5173, então o portal carrega e exibe os módulos |
| CA-004 | Dado que a demo está rodando, quando acessar cada módulo (Oswaldo, Florence, Geralda, Nise, Zilda, Grahame), então as funcionalidades principais respondem conforme README_DEMO.md |
| CA-005 | Dado cada módulo Python, quando verificar sua execução, então está rodando em ambiente virtual (venv/poetry/conda) |
| CA-006 | Dado o checklist de estabilização, quando preenchido, então está completo e disponível em docs/PLANNER-CURSOR/CHECKLIST_ESTABILIZACAO.md |

---

## 6. Cenários de Uso

### Cenário 1: Desenvolvedor sobe a demo pela primeira vez

1. Clona o repositório
2. Sobe infraestrutura: `docker-compose up -d`
3. Para cada módulo Python: cria/ativa ambiente virtual e instala dependências
4. Executa `start_demo.bat` (ou script que ativa venvs e inicia os processos)
5. Acessa http://localhost:5173
6. Resultado esperado: portal carrega e todos os módulos respondem

### Cenário 2: Validação de módulo individual

1. Ativa ambiente virtual do módulo
2. Executa o entry point do módulo (ex: `python run_api_8001.py` para Florence)
3. Verifica endpoint `/api/v1/health` ou `/health`
4. Resultado esperado: status 200 OK

---

## 7. Restrições e Premissas

### 7.1 Restrições

- **Python:** Sempre executar em ambiente virtual (venv, poetry, conda). O projeto teve problemas recorrentes de compatibilidade de versões de bibliotecas Python; ambientes virtuais são obrigatórios.
- **Ambiente:** Windows (start_demo.bat); considerar equivalente para Linux/Mac se necessário.

### 7.2 Premissas

- Docker e Docker Compose estão instalados
- Node.js 18+ instalado para o frontend
- Python 3.11+ disponível
- Portas 5173, 8000, 8001, 8002, 8003, 8004, 8006, 5432, 6379 livres

---

## 8. Entregáveis

| # | Entregável | Descrição |
|---|------------|-----------|
| 1 | Demo local funcionando | Todos os 6 módulos + portal respondendo |
| 2 | CHECKLIST_ESTABILIZACAO.md | Checklist preenchido em docs/PLANNER-CURSOR/ |
| 3 | ISSUES_CONHECIDOS.md | Lista de problemas não bloqueantes (se houver) em docs/PLANNER-CURSOR/ |
| 4 | Documentação de ambientes virtuais | Instruções ou README por módulo (ou centralizado) sobre como executar com venv/poetry |
| 5 | start_demo.bat (ou script) atualizado | Refletindo uso de ambientes virtuais |

**Artefatos do fluxo (neste diretório):** O dev deve registrar aqui a ESPECIFICACAO_TECNICA e o PLANO_IMPLEMENTACAO antes da implementação.

---

## 9. Referências

- `README_DEMO.md` — guia da demo
- `docs/PLANNER-CURSOR/ESTRATEGIA_PROXIMOS_PASSOS.md` — estratégia completa
- `docs/PLANNER-CURSOR/ESTUDO_PROJETO.md` — estrutura do projeto

---

## 10. Histórico de Alterações

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 2026-02-19 | Versão inicial |
