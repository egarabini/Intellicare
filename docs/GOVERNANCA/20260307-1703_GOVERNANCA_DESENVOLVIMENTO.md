# Governança de Desenvolvimento — IntelliCare

Data: 2026-03-07
Versão: 1.0
Status: Ativo

---

## Visão geral

Este documento descreve o modelo de governança adotado para o desenvolvimento
do IntelliCare a partir da versão 2.0, com múltiplos desenvolvedores trabalhando
em paralelo em 13+ módulos independentes.

O objetivo é garantir que:
- Nenhuma mudança chegue ao staging sem revisão
- O trabalho de um dev não quebre o de outro
- Todo o histórico de decisões técnicas esteja registrado
- Qualquer erro possa ser rastreado e revertido com segurança

---

## Papéis e responsabilidades

### Eduardo Garabini — Tech Owner
- Visão do produto e priorização de demandas
- Aprovação final de Pull Requests
- Validação de resultados em staging
- Define quem é responsável por qual módulo

### Claude — Tech Lead virtual
- Co-define escopo técnico das demandas com Eduardo
- Cria branches antes de repassar ao dev
- Gera documentação de demanda (ANDAMENTO_DEMANDA)
- Revisa diffs técnicos antes do PR
- Cria Pull Requests
- Mantém índice de demandas atualizado

### Desenvolvedores
- Trabalham dentro do escopo definido pela demanda
- Responsáveis por testar localmente antes de qualquer push
- Preenchem o log de execução da demanda
- Comunicam impedimentos imediatamente
- Não tomam decisões de arquitetura ou escopo sem alinhamento

---

## Ciclo de vida de uma demanda

| Etapa | Quem | O que acontece |
|---|---|---|
| **Identificação** | Eduardo | Problema ou melhoria identificado |
| **Especificação** | Claude + Eduardo | Escopo definido, spec aprovada |
| **Criação da branch** | Claude | Branch criada antes de repassar ao dev |
| **ANDAMENTO_DEMANDA** | Claude | Documento de acompanhamento gerado |
| **Desenvolvimento** | Dev | Trabalha na branch, testa local, preenche log |
| **Sinalização** | Dev → Eduardo | "Demanda concluída, pronto para revisão" |
| **Revisão** | Claude + Eduardo | Diff revisado, critérios de aceite verificados |
| **Pull Request** | Claude | PR criado com mensagem padronizada |
| **Aprovação** | Eduardo | PR aprovado no GitHub |
| **Deploy** | GitHub Actions | Deploy automático em staging |
| **Validação** | Eduardo + Claude | Verificação em staging, DEPLOYED registrado |

---

## Estrutura de documentação

```
docs/
├── GOVERNANCA/
│   └── 20260307-1703_GOVERNANCA_DESENVOLVIMENTO.md   <- este arquivo
│
├── NORMAS_E_PADROES/
│   ├── 20260221-0714_PADRAO_NOMENCLATURA_DOCUMENTOS.md
│   ├── 20260307-1703_FLUXO_GIT_E_DEPLOY.md
│   └── 20260307-1703_TEMPLATE_ANDAMENTO_DEMANDA.md
│
├── RELATORIOS_E_ANDAMENTO/
│   └── DEMANDAS/
│       ├── README.md                                  <- índice de demandas
│       └── YYYYMMDD-HHMM_DEM-NNN_MODULO_DESC.md     <- uma por demanda
│
├── V2.0.0-KEYCLOAK/        <- specs técnicas por versão/feature
├── INFRAESTRUTURA/
├── PLANOS_E_ESTRATEGIA/
└── HISTORICO/
```

---

## Controle de qualidade — o que é verificado antes do deploy

### CI automático (GitHub Actions — já configurado)
- Build do portal (`npm run build`)
- Lint do portal (`npm run lint`)
- Build da imagem Docker

### Revisão manual (Claude + Eduardo)
- Escopo: apenas os arquivos da demanda foram alterados?
- Critérios de aceite: todos verificados?
- Log preenchido: decisões técnicas registradas?
- Sem credenciais no código?
- Testes adicionados quando necessário?

### Smoke test pós-deploy
- Endpoints de health de todos os módulos afetados
- Funcionalidade principal da demanda testada manualmente em staging

---

## Proteção de módulos — CODEOWNERS

O arquivo `.github/CODEOWNERS` define quem deve revisar mudanças em cada módulo.
Quando um PR toca arquivos de um módulo, o GitHub automaticamente solicita
revisão do responsável.

Módulos críticos (core, auth, wanda) exigem aprovação de Eduardo em qualquer mudança.
Módulos de feature podem ter devs especialistas como responsáveis à medida que o time cresce.

Ver: [`.github/CODEOWNERS`](../../.github/CODEOWNERS)

---

## Regras inegociáveis

1. **Nenhum dev edita arquivo diretamente no servidor** — violação desta regra
   implica em conversa sobre permanência no projeto

2. **Nenhum push direto em `staging` ou `main`** — o GitHub bloqueia,
   mas a regra deve ser entendida antes da barreira técnica

3. **Nenhuma demanda começa sem ANDAMENTO_DEMANDA gerado** — branch criada
   por Claude, não pelo dev

4. **Todo problema encontrado é registrado no log** — silenciar erros para
   parecer que funcionou é o principal gerador de problemas em cascata

5. **Dev avisa ao concluir — não assume que está pronto para staging** —
   a aprovação é sempre de Eduardo + Claude

---

## Histórico de versões

| Versão | Data | Mudança |
|---|---|---|
| 1.0 | 2026-03-07 | Criação inicial — feature branches, CODEOWNERS, ANDAMENTO_DEMANDA |
