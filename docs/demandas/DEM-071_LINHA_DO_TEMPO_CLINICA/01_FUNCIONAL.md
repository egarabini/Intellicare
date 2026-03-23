---
tipo: especificacao-funcional
demanda: DEM-071
titulo: Linha do Tempo Clínica
sprint: 2026-04-25
status: em-execucao
dev: DEV-2
criado: 2026-03-21
depende_de: [DEM-055, DEM-057, DEM-058, DEM-061, DEM-062]
habilita: [DEM-074]
tags: [clinico, historico, longitudinal, timeline, florence, oswaldo, careplanner]
---

# DEM-071 — Linha do Tempo Clínica

## Objetivo

Hoje o ClinicoUI mostra o paciente de forma pontual — o clínico vê apenas o encontro atual. Para ter uma visão clínica real do paciente, ele precisa abrir encontro por encontro manualmente. Esta DEM cria uma **view longitudinal unificada** que exibe toda a história do paciente em ordem cronológica reversa: encontros, notas Florence, prescrições Oswaldo e eventos CarePlanner em um único scroll.

---

## Estado Atual vs. Estado Desejado

| Aspecto | Hoje | Após DEM-071 |
|---------|------|--------------|
| Visão do paciente | Apenas encontro atual aberto | Timeline completa — todos os encontros do histórico |
| Notas Florence | Acessíveis só dentro do encontro ativo | Exibidas na linha do tempo com data e tipo (SOAP/FREE) |
| Prescrições Oswaldo | Acessíveis só dentro do encontro ativo | Exibidas com CID-10, medicamentos e data |
| Eventos CarePlanner | Visíveis só no módulo CarePlanner | Integrados na timeline (jornadas SENT/REPLIED/CLOSED) |
| Busca histórica | Impossível sem abrir cada encontro | Filtro por período e tipo de evento |

---

## Personas e fluxos

**Dr. Silva — retorno de paciente crônico:**
1. Abre perfil do paciente `João da Silva`
2. Clica em aba "Linha do Tempo"
3. Vê scroll cronológico: última consulta há 2 semanas (nota SOAP + prescrição), jornada CarePlanner "Confirmação retorno" REPLIED, consulta há 3 meses (nota FREE), etc.
4. Sem abrir nenhum encontro individualmente, já tem contexto completo para a consulta atual

**Dr. Silva — busca de medicamentos históricos:**
1. Filtra timeline por tipo "Prescrições"
2. Vê todos os medicamentos prescritos ao paciente com datas
3. Verifica se há medicamentos de uso contínuo antes de prescrever novo item

---

## Critérios de aceite

1. Aba "Linha do Tempo" visível no `PatientProfile` do ClinicoUI
2. Timeline exibe: encontros (data, status), notas Florence (tipo, preview), prescrições Oswaldo (CID-10, lista de medicamentos), jornadas CarePlanner (canal, status final)
3. Ordem cronológica reversa (mais recente no topo)
4. Filtro funcional por: todos / encontros / notas / prescrições / jornadas
5. Filtro por período (últimos 30/90/180 dias / tudo)
6. Mínimo 4 testes automatizados passando

---

## Fora de escopo

- Exportação da timeline como PDF (fase futura)
- Eventos de exames laboratoriais (aguarda MinIO/DEM-070)
- Timeline para o paciente no PacienteUI (fase futura)
