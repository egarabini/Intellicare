# Diretrizes de Execução para o Desenvolvedor - Painel DRC

**Documento:** V0-202601310800-DiretrizesExecucaoDesenvolvedor.md
**Projeto:** Painel DRC (Protótipo)
**Versão:** 1.0
**Data:** 31 de Janeiro de 2026
**Emissor:** Manus AI (Planejador)

Este documento consolida as decisões tomadas pelo Arquiteto do Projeto (Usuário) em resposta às dúvidas do Desenvolvedor, servindo como base para a elaboração do Plano de Execução.

## 1. Confirmações Técnicas e Estratégicas

As seguintes diretrizes devem ser seguidas na elaboração do Plano de Execução e na implementação:

| Tópico | Decisão | Justificativa |
| :--- | :--- | :--- |
| **Servidor FHIR** | **Mock simples em JSON + Facade Python.** | Priorizar a agilidade do protótipo. O Mock deve ser estruturado para responder via `FHIRDataStore`, simulando o servidor real. |
| **Persistência** | **PostgreSQL + LMDB já no protótipo.** | Demonstrar arquitetura de alta performance desde o início. O LMDB será o cache de alta velocidade, e o PostgreSQL será o *source of truth*. |
| **Dataset Sintético** | **Gerar do zero.** | Criar "casos clínicos perfeitos" que demonstrem a longitudinalidade e as tendências de forma convincente para os gestores. |
| **Escopo UI** | **Manter o escopo completo.** | Incluir eGFR, PA, ACR, K+, meds, pendências, metas e os 4 formulários rápidos para maximizar o impacto da demonstração. |
| **Credenciais** | **Tudo via `.env`.** | Seguir as melhores práticas de segurança e facilitar a migração para ambientes de produção. |

## 2. Próximo Passo Esperado

O Desenvolvedor deve agora elaborar um **Plano de Execução Passo a Passo** (seguindo o padrão de nomenclatura `V0-20260131-PlanoExecucao.md`) que detalhe a sequência de tarefas para implementar a **Especificação Técnica (V0-20260131-EspecificacaoTecnica.md)**.

O Plano de Execução deve ser submetido ao Arquiteto e ao Planejador (Manus AI) para aprovação antes do início da codificação.
