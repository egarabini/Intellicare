# Visão do Planejador — IntelliCare .

**Data:** 2026-02-19  
**Autor:** PLANEJADOR (Cursor AI)  
**Papel:** Planejamento estratégico e especificações para agentes desenvolvedores

---

## 1. Síntese da Visão

O IntelliCare . é um ecossistema de saúde digital **bem estruturado** e **pronto para evolução governada**. A arquitetura modular (padrão LEGO), a separação clara de responsabilidades e a documentação existente criam uma base sólida para que o ARQUITETO e o PLANEJADOR conduzam o projeto de forma sistemática, entregando especificações funcionais de alta qualidade aos agentes desenvolvedores.

---

## 2. Pontos Fortes

| Aspecto | Avaliação |
|---------|-----------|
| **Arquitetura modular** | Módulos independentes, bem delimitados, com APIs REST padronizadas |
| **Stack moderna** | FastAPI, React 19, Vite 7, TypeScript 5.9 — alinhado ao estado da arte |
| **Documentação** | API_CATALOG, PLANO_UNIFICACAO_OPENAPI, levantamento de rotas |
| **Infraestrutura** | Docker Compose, Prometheus, Grafana — observabilidade presente |
| **Governança de dados** | Schemas separados (operacional/analítico), RLS, roles |
| **Demo funcional** | One-click com 6 módulos + portal integrados |

---

## 3. Oportunidades e Riscos

### 3.1 Oportunidades

1. **Unificação OpenAPI:** O plano já existe; falta execução (exportar specs, catálogo central).
2. **Auth (Keycloak):** Infra pronta, implementação pendente — prioridade para segurança.
3. **Padronização de entry points:** Reduzir inconsistência entre `run_api_lite.py`, `run_api_800X.py`, `src.*.api.main`.
4. **Integração entre módulos:** Wanda (orquestrador) + Nise (workflows) + Conhecimento (RAG) — potencial de valor clínico.
5. **Governança de especificações:** Com PLANNER-CURSOR, podemos versionar e rastrear decisões.

### 3.2 Riscos

| Risco | Mitigação sugerida |
|-------|---------------------|
| Complexidade de 15+ módulos | Priorizar ondas de evolução; não tentar padronizar tudo de uma vez |
| Auth pendente | Incluir intellicare-auth em onda prioritária |
| Dependências entre módulos | Mapear grafo de dependências; evitar acoplamento circular |
| Especificações ambíguas | Usar modelo ESPECIFICACAO_FUNCIONAL com critérios de aceite claros |

---

## 4. Proposta de Ondas de Evolução

### Onda 1 — Fundação (curto prazo)

- Unificação OpenAPI (Fase 1–2 do plano existente)
- Padronização de health/info em todos os módulos
- Documentar grafo de dependências entre módulos

### Onda 2 — Segurança e Governança

- Implementação intellicare-auth (Keycloak)
- Integração de auth no portal e nos backends
- RESSALVAS e checklist de PR para APIs

### Onda 3 — Integração Inteligente

- Integração Wanda ↔ Nise ↔ Conhecimento
- Fluxos end-to-end (ex.: alerta → workflow → RAG → resposta)
- Testes de integração automatizados

### Onda 4 — Controle de Versão e Deploy

- **Repositório:** `eduardo/intellicare` (já em uso)
- **Controle de atualizações Git:** definir estratégia de branches, tags, releases
- **Deploy:** ainda não realizado — definir pipeline (CI/CD), ambientes (dev/hml/prod)
- Políticas de retenção e LGPD
- SLA e SLO por módulo

### Onda 5 — Escalabilidade e Produção

- Kubernetes/Helm (se aplicável)
- Escalabilidade horizontal

---

## 5. Papel do PLANEJADOR

O PLANEJADOR atua como **ponte** entre a visão do ARQUITETO e a execução dos agentes desenvolvedores:

1. **Elaborar ESPECIFICACAO_FUNCIONAL** — versionada, com critérios de aceite, cenários e restrições.
2. **Revisar ESPECIFICACAO_TECNICA e PLANO_IMPLEMENTACAO** — validar alinhamento com a especificação funcional e com a arquitetura.
3. **Registrar RESSALVAS** — quando houver desvios ou riscos que exijam ajustes antes da implementação.
4. **Manter o REGISTRO_INTERACOES** — histórico de decisões para rastreabilidade.

---

## 6. Próximos Passos Recomendados

1. **Validar esta visão** com o ARQUITETO.
2. **Definir a primeira ESPECIFICACAO_FUNCIONAL** a ser entregue aos agentes (sugestão: Unificação OpenAPI Fase 1 ou Auth básico).
3. **Criar o template de ESPECIFICACAO_FUNCIONAL** no MODELO_ESPECIFICACAO.md.
4. **Estabelecer critérios de aprovação** para ESPECIFICACAO_TECNICA e PLANO_IMPLEMENTACAO.

---

## 7. Conclusão

O projeto está em excelente posição para evolução governada. Com o fluxo ARQUITETO ↔ PLANEJADOR ↔ Agentes Desenvolvedores, podemos garantir que cada mudança seja especificada, revisada e implementada de forma controlada. O PLANNER-CURSOR será o repositório central dessa governança.
