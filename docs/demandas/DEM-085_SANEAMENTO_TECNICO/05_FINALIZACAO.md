---
tipo: finalizacao
demanda: DEM-085
autor: DEV-1
data: 2026-05-16
---

# Finalização — DEM-085 (Saneamento Técnico)

A execução do saneamento varreu pontas soltas bloqueadoras conforme a roadmap e estabilizou as conexões do core FastAPI/Compose.

## O que foi entregue
- **Item 1:** O repositório git foi limpo na ramificação local; O diretório rascunho `estudos/` foi permanentemente colocado na policy restritiva global de gitignore. O relatório `AUDITORIA_GIT_y_m_d.md` final está na base docs.
- **Item 2:** As dependências CarePlanner-PubSub resolvido pelo injetamento fix de URL-encoding para tokens/senhas contendo `#`. O serviço não confunde mais as credenciais do hash staging, permitindo as execuções contínuas intellicare.
- **Item 3:** Nova Migration V2 `023_fix_clinical_notes_encounter_id.sql` introduzida para sanar os logs de warning index convertendo instâncias órfãs de BIGINT originais em mapeamentos reais de string UUID via re-casting dinâmico do PostgreSQL. 
- **Item 4:** Suíte de teste do Care planner unitária (`test_cuidado.py`) despoluída substituindo keyword injection `full_name` para var mapping `name` alinhado à DTO vigente. Passou sem intercorrências.

## Decisões Arquiteturais e Dívidas Futuras
O acúmulo da quebra no REDIS alerta a atenção estendida em revisar os URIs do Redis para outros canais que incorporem senhas complexas por hard-inject de docker env. Decidimos tratar a url a priori do container-layer (na infra env e no docker-compose local do service target). A migration V2 foi formatada num schema tolerante permitindo upcasts silenciosos não retroativos para BIGINTs zumbis sem abortar o startup.  

## Próximos Passos
Prosseguir com a trilha original, abrindo DEM-086 com confiança redobrada nas suites e consistência modular do banco de metadados clínicos.
