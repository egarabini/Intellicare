---
tipo: delta-documentacao
sprint: 2026-04-25
destinatario: DEV-4
status: aplicado
criado: 2026-03-22
---

# DELTA Sprint 2026-04-25 — Atualizações para UTILIZACAO/

> DEV-4: este arquivo lista o que precisa ser criado ou atualizado na pasta `DOCUMENTACAO/UTILIZACAO/` com base nas entregas do sprint 2026-04-25.

---

## 1. Nova funcionalidade — Linha do Tempo Clínica (DEM-071)

**O que foi entregue:** Aba "Linha do Tempo" no perfil do paciente (ClinicoUI), agora exibida como aba padrão ao abrir qualquer paciente. Unifica consultas, notas Florence, prescrições Oswaldo e tarefas CarePlanner em ordem cronológica.

**Ação DEV-4:**

Criar `DOCUMENTACAO/UTILIZACAO/11_LINHA_DO_TEMPO.md` cobrindo:

- O que é a linha do tempo e para que serve (visão longitudinal do paciente)
- Como acessar: ClinicoUI → Paciente → aba "Linha do Tempo" (primeira aba)
- Como usar os filtros por tipo de evento (Consulta, Nota Clínica, Prescrição, Tarefa)
- O que cada tipo de evento exibe (campos visíveis para o clínico)
- Captura de tela sugerida: aba aberta com eventos de diferentes tipos visíveis

Atualizar também `DOCUMENTACAO/UTILIZACAO/05_CLINICO_GUIA.md` (ou equivalente):
- Mencionar que a aba padrão do perfil do paciente mudou para "Linha do Tempo"
- Remover qualquer referência que diga que outra aba é a padrão

---

## 2. Nova funcionalidade — Receituário Digital (DEM-072)

**O que foi entregue:** Geração de receituário médico no padrão CFM/ANVISA em PDF. Disponível no editor de prescrições do Oswaldo, no card de histórico de prescrições. Dois tipos: Receita Comum e Receita de Controle Especial (tarja preta).

**Ação DEV-4:**

Criar `DOCUMENTACAO/UTILIZACAO/12_RECEITUARIO_DIGITAL.md` cobrindo:

- O que é o receituário digital e qual o padrão seguido (CFM/ANVISA)
- Como acessar: ClinicoUI → Paciente → aba Oswaldo → Histórico de Prescrições → botão "Imprimir Receituário"
- Diferença entre "Receita Comum" e "Receita de Controle Especial":
  - Comum: medicamentos de uso geral
  - Controle Especial: tarja preta — exige CPF do paciente, validade e número de notificação
- O que aparece no PDF: cabeçalho com nome e CRM do médico, símbolo ℞, lista de medicamentos com posologia formatada, QR code de autenticidade, assinatura
- Orientação sobre impressão: PDF abre em nova aba — usar Ctrl+P ou o botão de impressão do navegador
- Captura de tela sugerida: menu "Imprimir Receituário" aberto + PDF gerado

---

## 3. Nova funcionalidade — Gestão de Prompts IA (DEM-073)

**O que foi entregue:** Página "Prompts IA" no AdminUI. Permite que o gestor da plataforma visualize, edite, versione e faça rollback dos prompts usados pela IA (Florence e Oswaldo) sem necessidade de redeploy.

**Ação DEV-4:**

Criar `DOCUMENTACAO/UTILIZACAO/13_PROMPTS_IA.md` cobrindo:

- O que são os prompts IA e por que podem precisar de ajuste (personalização do tom, especialidade clínica, etc.)
- Quem tem acesso: apenas usuário com perfil **Administrador de Plataforma** (AdminUI)
- Como acessar: AdminUI → menu lateral "Prompts IA" → `/admin/prompts`
- O que é exibido na listagem: nome do prompt (slug), versão ativa, data da última edição
- Como editar um prompt:
  1. Clicar no prompt desejado
  2. Editar o texto no campo de edição
  3. Preencher o campo "Descrição da alteração" (obrigatório — ex: "Adaptado para cardiologia")
  4. Clicar em "Salvar nova versão" — a versão é salva mas **não ativada automaticamente**
  5. No histórico, clicar em "Ativar" na versão desejada para colocá-la em uso
- Como fazer rollback: no histórico de versões, clicar em "Ativar" em uma versão anterior
- Prompts disponíveis e o que controlam:

| Prompt | Módulo | O que controla |
|--------|--------|---------------|
| `florence_soap` | Florence | Geração de nota SOAP clínica |
| `florence_free_text` | Florence | Nota em texto livre |
| `oswaldo_prescription` | Oswaldo | Sugestão de prescrição |
| `oswaldo_cid10` | Oswaldo | Sugestão de CID-10 por sintomas |

- Aviso importante: alterações nos prompts afetam **todas as sugestões de IA** a partir da ativação. Testar em ambiente de homologação antes de ativar em produção.
- Captura de tela sugerida: listagem de prompts + editor aberto com histórico de versões

---

## Resumo das ações

| Arquivo | Ação | Prioridade |
|---------|------|-----------|
| `UTILIZACAO/11_LINHA_DO_TEMPO.md` | Criar | Alta |
| `UTILIZACAO/12_RECEITUARIO_DIGITAL.md` | Criar | Alta |
| `UTILIZACAO/13_PROMPTS_IA.md` | Criar | Média |
| `UTILIZACAO/05_CLINICO_GUIA.md` | Atualizar — aba padrão mudou | Alta |

---

*Após aplicar todas as atualizações, alterar o status deste arquivo para `✅ Aplicado` no `README.md` da pasta SPRINTS.*
