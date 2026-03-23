# 6. Dashboards e Relatorios

## 6.1 Dashboard Admin - leitura executiva

## Indicadores

- Total de tenants
- Ativos x suspensos
- Receita mensal
- Servidores ativos
- Custo mensal de infraestrutura

## Decisoes suportadas

- Prioridade de suporte comercial (suspensos).
- Saude economica da plataforma (receita x custo).
- Necessidade de escala tecnica (servidores ativos).

## 6.2 Dashboard Gestor - leitura operacional

## Indicadores

- Pacientes ativos
- Consultas hoje/semana/mes
- Faturas pendentes
- Documentos de conhecimento/RAG
- Unidades ativas
- Profissionais alocados
- Atividade recente

## Exemplo de analise

Se `consultas hoje` cresce e `profissionais alocados` permanece estavel:

- revisar escala por unidade;
- antecipar jornadas para reduzir absenteismo;
- redistribuir agenda entre profissionais.

## 6.3 Dashboard CarePlanner - leitura de funil

## Funil padrao

`CREATED -> DISPATCHED -> SENT -> REPLIED -> CLOSED`

## Alertas operacionais

- `FAILED` alto: problema de canal, credencial ou contato invalido.
- `EXPIRED` alto: engajamento baixo ou janela de resposta inadequada.
- `REPLIED` baixo com `SENT` alto: revisar template e horario de disparo.

## 6.4 Dashboards Grafana (careplanner e multicanal)

O ambiente possui paineis de observabilidade com indicadores por canal, incluindo:

- taxa de disparo por canal;
- respostas por hora;
- expiradas por hora;
- eventos e orfaos;
- latencia p95 em etapas da jornada.

Uso recomendado: acompanhamento diario de operacao e revisao semanal de tendencia.

## 6.5 Relatorios PDF disponiveis

- Admin: exportacao de tenants ativos.
- Gestor/CarePlanner: relatorio de jornada (quando acionado no fluxo).
- Clinico: PDF de encontro com conteudo Florence + Oswaldo.

## Exemplo de uso do PDF Clinico

- compartilhar sumario da consulta entre profissionais do cuidado;
- anexar ao fluxo interno de continuidade assistencial;
- apoiar auditoria clinica.
