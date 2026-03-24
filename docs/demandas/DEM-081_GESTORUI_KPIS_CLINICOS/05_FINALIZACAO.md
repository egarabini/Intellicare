# DEM-081 — GestorUI KPIs Clínicos
## Finalização

A demanda GestorUI KPIs Clínicos (DEM-081) foi executada e concluída com êxito conforme especificações. 

### Resultados Alcançados
- **Backend:** Concluída e avaliada a feature `get_clinical_kpis` via `async`/`await` de chamadas do banco de dados agregando todas as requisições KPI essenciais em única transação. Adicionado isolamento e fixture para aprimorar independência unitária nos ambientes de simulação (pytest).
- **Frontend / ReactUI:** Adicionado endpoint e Hook assíncrono `@tanstack/react-query` `useClinicalKPIs` que abstrai o fetch `/admin/kpis/clinical`.
- **UI:** A página de `IndicadoresPage.tsx` foi materializada utilizando o core stack com `Mantine` e biblioteca estática `recharts`. A renderização injetada em rotas ativas dentro do `App.tsx` foi validada com build limpo local via Vite.

### Lições Aprendidas
- Em testes Unitários compartilhando Tenant Schemas assíncronos (como `tenant_session`), a poluição da tabela de execuções anteriores exigia atenção especial com persistência que impactava resultados assíncronos. Uso de fixture limpadora é recomendado para futuros pipelines.
- Arquitetura de `App.tsx` reestruturada para suportar hooks e providers encapsulados para as rotas com autenticação KeyCloak OIDC. 

O módulo está habilitado para deployment e os commits de homologação se estendem aos repositórios.

---

**Commit em origin/main:** `bd33879` (cherry-pick de worktree limpo — hash original local: `81cb29d`)
Push: `git push origin HEAD:main` ✅ confirmado via `.tmp_push_fix`
