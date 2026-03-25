# IntelliCare V3 — Catch-up DEV-4 (Documentação UTILIZACAO/)

> Gerado em: 2026-03-25
> Para: DEV-4
> Status: 5 sprints pendentes de aplicação na UTILIZACAO/

Este documento consolida **todas as ações pendentes** dos DELTAs das últimas sprints em ordem cronológica. Aplique uma a uma, marcando cada item ao concluir.

---

## Como usar este documento

1. Aplique as ações em ordem (mais antiga → mais nova)
2. Após concluir cada sprint, marque o DELTA correspondente como `✅ Aplicado` no `DOCUMENTACAO/SPRINTS/README.md`
3. Ao terminar tudo, informe o ARQUITETO para atualizar o README

---

## BLOCO 1 — Sprint 2026-04-18 (Addendum)

> Arquivo: `DELTA_SPRINT_2026_04_18_ADDENDUM.md`
> DEMs: DEM-068 (Staging Sync) + fixes colaterais

### Ação 1.1 — `UTILIZACAO/README.md`
Atualizar linha de escopo:
```
DE:   "cobertura funcional: entregas concluídas até DEM-067 (sprint 2026-04-18)"
PARA: "cobertura funcional: sprint 2026-04-18 concluída — DEMs 065 a 068 validadas em staging"
```

### Ação 1.2 — `UTILIZACAO/01_VISAO_GERAL_INTELLICARE.md`
Adicionar seção "Estado atual da plataforma (sprint 2026-04-18)":

| Módulo | Smoke staging | Observação |
|--------|-------------|------------|
| Florence (notas IA) | ✅ 200 | |
| Oswaldo (prescrições IA) | ✅ 200 | |
| CarePlanner (jornadas) | ✅ trigger 202 | Kestra com flows condicionais ativos |
| Push PWA (notificações) | ✅ subscribe 201 | ClinicoUI + GestorUI |
| Multi-tenant (provisioning) | ✅ provision 201 | Suspend/reactivate funcionais |
| WhatsApp Evolution | ✅ state: open | |
| Health adapters | ✅ 200 | |

### Ação 1.3 — `UTILIZACAO/02_GUIA_ADMINISTRADOR_PLATAFORMA.md`
Na seção sobre o Portal de Agentes, adicionar nota sobre renomeação de imagens:
> As imagens dos agentes foram renomeadas — o sufixo `_ia` foi removido. Padrão atual: `agente_florence.png`, `agente_oswaldo.png`, `agente_marie.png` (sem `_ia`). Não afeta a interface visual.

### Ação 1.4 — `UTILIZACAO/03_GUIA_GESTOR_TENANT.md`
Na seção CarePlanner, adicionar nota:
> Flows condicionais validados em staging (2026-03-21): fallback de canal WA→Email ativo, confirmação via WhatsApp automática, retry com backoff (2h→6h→24h).

### Ação 1.5 — Manuais consolidados
Atualizar cabeçalho/versão em `MANUAL_USUARIO_INTELLICARE_COMPLETO.md` e `PRONTO_PARA_IMPRESSAO.md/.html`:
- Versão: `Sprint 2026-04-18 — Concluída (DEMs 065–068)`
- Aplicar as mesmas adições das ações 1.2, 1.3, 1.4

---

## BLOCO 2 — Sprint 2026-05-02

> Arquivo: `DELTA_SPRINT_2026_05_02.md`
> DEMs: DEM-075 (Marie infra), DEM-076 (Portal Paciente histórico), DEM-077 (Interações medicamentosas)

### Ação 2.1 — `UTILIZACAO/GUIA_PACIENTE.md` (ou equivalente)
**Seção "Meu Histórico"** — nova experiência de linha do tempo:
- Como acessar: Portal do Paciente → "Meu Histórico"
- O que aparece: consultas, notas Florence (sem partes internas), prescrições, jornadas de acompanhamento
- Como baixar receituário: clicar em "Baixar Receituário" na prescrição → PDF em nova aba
- Privacidade: o paciente vê o que foi compartilhado pelo médico, não as anotações internas SOAP-A

### Ação 2.2 — `UTILIZACAO/GUIA_CLINICO_OSWALDO.md` (ou equivalente)
**Seção nova: "Alertas de Interação Medicamentosa"**:
- O alerta aparece automaticamente ao prescrever dois ou mais medicamentos com interação conhecida
- Cores: vermelho (GRAVE), amarelo (MODERADO), azul (LEVE)
- Como agir: avaliar clinicamente → clicar "Entendido — manter prescrição" se intencional
- O alerta **não impede** a prescrição — decisão sempre do médico
- Alertas marcados "por IA" devem ser confirmados com fontes clínicas antes de ignorar

### Ação 2.3 — Marie (DEM-075)
**Nenhuma ação necessária.** Marie está instalado como infraestrutura mas desativado para o usuário. Documentar quando for ativado em produção.

---

## BLOCO 3 — Sprint 2026-05-09

> Arquivo: `DELTA_SPRINT_2026_05_09.md`
> DEMs: DEM-079 (Florence contextual), DEM-080 (Certificado digital), DEM-081 (KPIs GestorUI)

### Ação 3.1 — `UTILIZACAO/GUIA_CLINICO_FLORENCE.md` (ou equivalente)
**Seção "Sugestão IA"** — atualizar descrição:
- A sugestão agora considera o **histórico longitudinal** do paciente (últimos encontros, notas, prescrições) — resultado mais personalizado
- Quando MARIE_ENABLED está ativo, a sugestão pode levar 2–5s a mais — comportamento esperado, não é erro
- Botão permanece o mesmo: "Sugestão IA" em EncounterView

### Ação 3.2 — `UTILIZACAO/GUIA_CLINICO_RECEITUARIO.md` ou `12_RECEITUARIO_DIGITAL.md` (criar se não existir)
**Seção nova: "Certificado Digital"**:
- Para ativar: Perfil → "Certificado Digital" → enviar arquivo `.pfx` + senha do certificado
- Após upload: todos os receituários gerados terão assinatura digital embutida no PDF
- Para remover: botão "Remover" na mesma seção
- O receituário é gerado normalmente mesmo sem certificado — assinatura é opcional
- Para validade jurídica: o certificado deve ser emitido por AC credenciada ICP-Brasil. Certificados de teste mostram aviso no Adobe Reader

### Ação 3.3 — Criar `UTILIZACAO/16_GESTORUI_INDICADORES.md`
**KPIs Clínicos — nova página `/indicadores` no GestorUI**:
- Como acessar: GestorUI → menu lateral → "Indicadores"
- Filtros: período (data início/fim), profissional (opcional)
- KPIs disponíveis:
  - Total de encontros no período
  - Total de notas Florence geradas
  - Total de prescrições emitidas
  - Total de interações medicamentosas detectadas
  - Jornadas CarePlanner por status (ativa, concluída, expirada)
  - Top profissionais por prescrições
  - Gráfico de interações por dia
- **Nota importante**: o contador de interações não é retroativo — prescrições anteriores à DEM-077 aparecem como 0 interações
- Filtro por profissional não afeta o gráfico de interações por dia (limitação conhecida)

---

## BLOCO 4 — Sprint 2026-05-16

> Arquivo: `DELTA_SPRINT_2026_05_16.md`
> DEMs: DEM-084 (Identidade centralizada paciente)

### Ação 4.1 — Guia do módulo Clínico (seção de cadastro de pacientes)
**CPF recomendado no cadastro de paciente**:
- O campo CPF no cadastro de paciente agora é recomendado (não obrigatório)
- Quando preenchido, o sistema garante que o mesmo paciente não será duplicado entre estabelecimentos IntelliCare
- O paciente recebe um identificador único que o acompanha em toda a rede
- Não há mudança visual no formulário — o comportamento é automático e transparente

---

## BLOCO 5 — Sprint 2026-05-23 ✅ Encerrada

> Arquivo: `DELTA_SPRINT_2026_05_23.md`
> DEMs: DEM-088 (Identidade profissional), DEM-089 (Painel identidade AdminUI)
> Sprint encerrada em 2026-03-25 — aplicar agora

### Ação 5.1 — Guia do módulo Clínico (seção de cadastro de profissionais)
**CPF recomendado no cadastro de profissional**:
- Igualmente ao cadastro de pacientes, o CPF de profissionais agora conecta ao sistema de identidade central
- Quando preenchido, o profissional é reconhecido em todos os estabelecimentos da rede
- Comportamento transparente — sem mudança visual no formulário

### Ação 5.2 — `UTILIZACAO/02_GUIA_ADMINISTRADOR_PLATAFORMA.md`
**Seção nova: "Identidade Centralizada"**:
- Nova página disponível em AdminUI → "Identidade" (`/admin-ui/identity`)
- **Cards de totais**: total de pessoas cadastradas na plataforma, vínculos por estabelecimento, cobertura percentual
- **Tabela por tenant**: pacientes e profissionais com/sem identidade vinculada, percentual de cobertura
- **Botão "Reconciliar identidades"**: processa registros existentes que têm CPF mas ainda não têm vínculo de identidade central
  - Exige confirmação antes de executar
  - Retorna relatório: quantos registros foram processados e vinculados
  - Operação idempotente: pode ser executada mais de uma vez sem risco

---

## Resumo das ações por arquivo

| Arquivo | Blocos |
|---------|--------|
| `UTILIZACAO/README.md` | 1.1 |
| `UTILIZACAO/01_VISAO_GERAL_INTELLICARE.md` | 1.2 |
| `UTILIZACAO/02_GUIA_ADMINISTRADOR_PLATAFORMA.md` | 1.3, 5.2 |
| `UTILIZACAO/03_GUIA_GESTOR_TENANT.md` | 1.4 |
| `MANUAL_USUARIO_INTELLICARE_COMPLETO.md` | 1.5 |
| `UTILIZACAO/GUIA_PACIENTE.md` | 2.1 |
| `UTILIZACAO/GUIA_CLINICO_OSWALDO.md` | 2.2 |
| `UTILIZACAO/GUIA_CLINICO_FLORENCE.md` | 3.1 |
| `UTILIZACAO/GUIA_CLINICO_RECEITUARIO.md` (criar) | 3.2 |
| `UTILIZACAO/16_GESTORUI_INDICADORES.md` (criar) | 3.3 |
| Guia cadastro de pacientes | 4.1 |
| Guia cadastro de profissionais | 5.1 |

---

## Após concluir tudo

Marcar no `DOCUMENTACAO/SPRINTS/README.md` como `✅ Aplicado`:
- `DELTA_SPRINT_2026_04_18_ADDENDUM.md`
- `DELTA_SPRINT_2026_05_02.md`
- `DELTA_SPRINT_2026_05_09.md`
- `DELTA_SPRINT_2026_05_16.md`
- `DELTA_SPRINT_2026_05_23.md` (após encerramento da sprint)

*Gerado pelo ARQUITETO — IntelliCare V3*
