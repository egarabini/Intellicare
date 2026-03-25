# DEM-089 — Diário de Execução

## 2026-03-24

### 1. Leitura e adaptação ao código real

- A spec foi cruzada com o módulo existente [`modules/identity/`](/c:/Users/egara/INTELLICARE/modules/identity/) criado na DEM-083.
- Antes de escrever queries de reconciliação, os nomes reais foram confirmados no código vivo:
  - `patients.cpf`
  - `patients.pessoa_id`
  - `professionals.pessoa_id`
- A camada real de acesso permaneceu em SQL direto (`repository.py` / `services.py`), sem introduzir ORM novo.

### 2. Adaptação defensiva descoberta em implementação

- Foi identificado drift potencial entre tenants para profissionais.
- A tabela `professionals` existe de forma consistente, mas a coluna de CPF não é garantida de maneira única no histórico do projeto.
- Por isso, a reconciliação de profissionais foi implementada com detecção defensiva de coluna CPF:
  - tenta `cpf`
  - fallback para `document_cpf`
  - se nenhuma existir, o batch pula o escopo de profissionais naquele tenant sem quebrar a execução
- Essa adaptação não estava explícita no briefing e deve ser tratada como gotcha para futuras DEMs de identidade.

### 3. Backend implementado

- Endpoint `POST /identity/admin/reconcile?scope=patients|professionals|all`
- Endpoint `GET /identity/admin/stats`
- Reconciliação serial por tenant, idempotente, com isolamento de erro por linha.
- Stats com cobertura por tenant e percentual agregado.

### 4. AdminUI implementado

- Nova página `IdentityPage.tsx`
- Novo hook `useIdentity.ts`
- Nova rota `/admin-ui/identity`
- Novo item de navegação no `App.tsx`

### 5. Build estático validado

- O `AdminUI` foi recompilado a partir do source atualizado, já contendo `IdentityPage.tsx`.
- Comando executado:

```bash
npm run build
```

- Saída estática regenerada em [`packages/intellicare-core/intellicare_core/static/admin-ui/`](/c:/Users/egara/INTELLICARE/packages/intellicare-core/intellicare_core/static/admin-ui/)
- Bundle atual:
  - `assets/index-CEE6pvO7.js`
  - `assets/index-BnCyCbP0.css`

### 6. Testes executados

- Comando:

```bash
$env:PYTHONPATH='c:\Users\egara\INTELLICARE'; pytest packages\intellicare-core\tests\test_identity_foundation.py packages\intellicare-core\tests\test_identity_reconciliation.py -q
```

- Resultado:
  - `14 passed`
  - `6` testes novos são exclusivos da DEM-089 (`test_identity_reconciliation.py`)
  - `8` testes restantes vêm da base da DEM-083 (`test_identity_foundation.py`)
