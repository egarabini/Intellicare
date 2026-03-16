# DEM-029 — 03_PLANO

## Contexto

`01_FUNCIONAL.md` e `02_TECNICA.md` ainda não existem para esta demanda.
Execução realizada por fallback pragmático, usando os contratos já disponíveis
em `modules/cuidado`, `modules/gestor`, `frontend/ClinicoUI` e
`frontend/PacienteUI`.

## Objetivo de execução

Fechar a integração operacional de agendamento entre ClinicoUI e PacienteUI
sobre a mesma tabela `appointments`, garantindo:

- compatibilidade com schemas legados e novos de `patients`
- resolução estável do paciente logado no portal
- exibição do nome do clínico no portal do paciente
- reflexo visual no ClinicoUI de confirmações/cancelamentos feitos no PacienteUI
- tratamento correto de erro nos endpoints de confirmação/cancelamento

## Plano

1. Corrigir backend de `cuidado` para compatibilidade de schema e integração.
2. Ajustar ClinicoUI para leitura mais clara do status dos agendamentos.
3. Ajustar PacienteUI para mostrar profissional e atualizar dados em tempo real.
4. Adicionar teste de integração cobrindo o fluxo principal.
5. Validar com `pytest` e `npm run build` nos dois frontends.
