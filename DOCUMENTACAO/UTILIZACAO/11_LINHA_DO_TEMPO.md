# 11. Linha do Tempo Clinica (DEM-071)

## O que e

A **Linha do Tempo Clinica** consolida o historico do paciente em uma visao unica, cronologica e filtravel.  
Ela une eventos que antes estavam espalhados em telas diferentes.

## Para que serve

- dar visao longitudinal da jornada clinica;
- reduzir tempo de busca de contexto antes da consulta;
- apoiar decisao clinica com historico estruturado.

## Como acessar

No `ClinicoUI`:

1. abrir `Pacientes`;
2. selecionar um paciente;
3. entrar na aba **Linha do Tempo** (agora aba padrao no perfil do paciente).

## Filtros disponiveis

- **Tipo de evento:** `Consulta`, `Nota Clínica`, `Prescrição`, `Tarefa`.
- **Período:** ultimos `N` dias (conforme filtro da tela).

## O que cada evento exibe

- **Consulta:** data/hora, status e referencia do atendimento.
- **Nota Clinica (Florence):** tipo da nota (`SOAP` ou `FREE`) e resumo.
- **Prescricao (Oswaldo):** data, itens prescritos e status.
- **Tarefa (CarePlanner):** tipo da tarefa, canal e status da jornada.

## Exemplo de uso no dia a dia

1. Antes de atender, abrir a linha do tempo.
2. Filtrar ultimos 30 dias.
3. Revisar sequencia: consulta anterior -> nota -> prescricao -> tarefa de acompanhamento.
4. Entrar na consulta atual com contexto completo.

## Captura de tela sugerida

- Aba "Linha do Tempo" aberta, com pelo menos 3 tipos de evento visiveis.
- Filtro por tipo e filtro por periodo aparentes na imagem.
