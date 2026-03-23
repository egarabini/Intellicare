---
tipo: finalizacao
demanda: DEM-072
titulo: Receituário Digital
status: concluida
commit: 7d1c6a9
dev: DEV-1
data-entrega: 2026-03-22
---

# DEM-072 — Finalização (Receituário Digital)

## Resumo da Entrega
O Receituário Digital autônomo foi implementado com sucesso e os seguintes itens foram garantidos:
- Layout estrutural exigido pelo CFM/ANVISA via Jinja2 (cabeçalho com especialidade e CRM, símbolo ℞, rodapés com assinatura).
- Validação e segurança atendidas via autenticação e seleção de tenant (`ctx`).
- **Implementações Técnicas Complementares (Check de Qualidade):**
  1. Integração da biblioteca Python `qrcode[pil]` para gerar o Code em tempo real (base64) evitando depender de APIs externas para validação e limitando questões de expurgo/LGPD de dados trafegados.
  2. Remoção das classes duplicadas (`OswaldoSuggestRequest` e `OswaldoSuggestion`) no `contracts.py`, limpando o debt de estrutura grave.
  3. Adição do motor de formatação de posologia avançado garantida por testes: expansão de horas matemáticas (`8/8h` para `a cada 8 horas`), de unidade posológica ("1" para "1 (um)") e auto-descobrimento de rotas de administração farmacêutica baseada na forma referida ("comprimido" para "via oral").
  4. Integração do menu "Imprimir Receituário" atrelado às tabelas de Histórico para permitir ao clínico a emissão posterior no OswaldoEditor.

## Testes e Quality Assurance
- **Suíte de Testes:** Adicionados 7 testes com *pytest* validando não somente a emissão isolada, mas como a ferramenta de expansão do CFM atua sobre strings imperfeitas.
- **Status:** 100% Passed.

A demanda atende todos os critérios e pode ser integrada.
