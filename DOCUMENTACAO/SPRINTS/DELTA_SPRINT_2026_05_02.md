---
tipo: delta-documentacao
sprint: 2026-05-02
destinatario: DEV-4
status: pendente
criado: 2026-03-22
---

# DELTA Sprint 2026-05-02 — Atualizações para UTILIZACAO/

> DEV-4: este arquivo lista o que precisa ser criado ou atualizado na pasta `DOCUMENTACAO/UTILIZACAO/` com base nas entregas do sprint 2026-05-02.

---

## 1. Nova funcionalidade — Portal Paciente: Meu Histórico (DEM-076)

**O que foi entregue:** A página "Meu Histórico" no portal do paciente foi reformulada. Agora exibe uma linha do tempo completa com consultas, notas clínicas, prescrições e tarefas de acompanhamento, além de um botão para baixar o receituário de cada prescrição.

**Ação DEV-4:**

Atualizar `DOCUMENTACAO/UTILIZACAO/` — criar ou atualizar guia do paciente cobrindo:

- Como acessar "Meu Histórico" no portal
- O que cada tipo de evento exibe na linha do tempo (consulta, nota, prescrição, jornada)
- Como baixar o receituário: clicar em "Baixar Receituário" na prescrição → PDF abre em nova aba
- Nota sobre privacidade: o paciente vê o que relatou ao médico, mas não as anotações clínicas internas

---

## 2. Nova funcionalidade — Interação Medicamentosa no Oswaldo (DEM-077)

**O que foi entregue:** O editor de prescrições do Oswaldo agora verifica automaticamente interações entre os medicamentos prescritos e exibe um alerta visual quando detecta conflito.

**Ação DEV-4:**

Atualizar `DOCUMENTACAO/UTILIZACAO/` — adicionar seção no guia do clínico (Oswaldo) cobrindo:

- O que é o alerta de interação medicamentosa e quando aparece
- Cores e significado: vermelho (GRAVE), amarelo (MODERADO), azul (LEVE)
- Como proceder ao ver o alerta: avaliar clinicamente → clicar "Entendido — manter prescrição" se for intencional
- Nota sobre alertas "por IA": alertas marcados como verificação por IA devem ser confirmados com fontes clínicas antes de ignorar
- O alerta **não impede** a prescrição — é sempre decisão do médico

---

## 3. Novo módulo — Marie (infraestrutura — sem impacto imediato para usuário) (DEM-075)

**O que foi entregue:** Infraestrutura do módulo Marie (orquestradora IA) instalada. Atualmente desligada por padrão — sem impacto na experiência do usuário neste sprint.

**Ação DEV-4:** Nenhuma ação necessária neste sprint. Documentação do Marie será solicitada quando a funcionalidade for ativada para os usuários.

---

## Resumo das ações

| Arquivo | Ação | Prioridade |
|---------|------|-----------|
| `UTILIZACAO/GUIA_PACIENTE.md` (ou equivalente) | Atualizar — seção "Meu Histórico" com timeline + receituário | Alta |
| `UTILIZACAO/GUIA_CLINICO_OSWALDO.md` (ou equivalente) | Atualizar — seção de alertas de interação medicamentosa | Alta |

---

*Após aplicar todas as atualizações, alterar o status deste arquivo para `✅ Aplicado` no `README.md` da pasta SPRINTS.*
