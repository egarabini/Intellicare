# DEM-037 — AdminUI: Correções e Melhorias (Rodada de Testes v1)

## Origem

Bugs e lacunas identificados durante a primeira sessão de testes funcionais do AdminUI. Todos os itens são correções diretas — nenhum representa nova funcionalidade fora do escopo já especificado.

---

## Itens

### #1 — Dashboard zerado sem feedback (Frontend)

**Problema:** Quando o ambiente não tem tenants cadastrados, o Dashboard mostra todos os cards com "0" sem qualquer orientação ao usuário.

**Comportamento esperado:**
- Se `total_tenants === 0`, exibir um `Alert` com ícone de informação: _"Nenhum tenant cadastrado. Crie o primeiro tenant para começar."_ com botão "Criar tenant" que navega para `/tenants/new`
- Os cards continuam sendo renderizados com 0 (para manter o layout), mas o Alert aparece acima deles

---

### #2 — Tenants: sem botão de editar (Backend + Frontend)

**Problema:** Na listagem de tenants existe apenas Visualizar e Suspender/Reativar. Não é possível editar o nome do tenant.

**Comportamento esperado:**
- Botão `IconPencil` na linha da listagem abre formulário de edição do tenant
- Campos editáveis: apenas **Nome** (`name`) — o slug é imutável por design
- Ao salvar, o `TenantDetail` atualiza sem recarregar
- Rota: o botão editar navega para `/tenants/:slug/edit` (nova rota)

---

### #3 — Tenants: gestor não visível (Backend + Migration + Frontend)

**Problema:** O `gestor_email` informado na criação do tenant é usado para criar o usuário no Keycloak, mas não é armazenado na tabela `public.tenants` nem exibido em nenhuma tela. Operacionalmente, o admin perde a referência de quem é o responsável por aquele tenant.

**Comportamento esperado:**
- A tabela `public.tenants` passa a ter coluna `gestor_email TEXT`
- Ao criar o tenant, o `gestor_email` é persistido no banco
- `TenantList` exibe coluna "Gestor" com o e-mail
- `TenantDetail` exibe "Gestor: gestor@cliente.com" na seção de dados do tenant
- Campo `gestor_email` também é editável na tela de edição (item #2)

---

### #4 — Usuários do tenant: badge de role vazio (Frontend)

**Problema:** Na página `Usuários — {slug}` (rota `/tenants/:slug/users`), a coluna Role exibe um badge vazio quando o usuário não tem role atribuída no Keycloak.

**Comportamento esperado:**
- Se `roles` for vazio ou indefinido, exibir `Badge` cinza com texto "Sem role"
- Se há role, exibir normalmente em azul

---

### #5 — Usuários Admin: senha temporária não exibida (Backend + Frontend)

**Problema:** Ao criar um usuário administrativo, o Keycloak gera uma senha temporária (`Tmp@xxxxxxxx`). Essa senha é salva no log de auditoria mas **não é retornada para o frontend**. O admin não tem como saber a senha para repassar ao novo usuário.

**Comportamento esperado:**
- Após criar o usuário admin com sucesso, exibir um `Modal` com:
  - Título: "Usuário criado"
  - Mensagem: "Senha temporária de primeiro acesso:"
  - Campo de texto somente-leitura com a senha, com botão "Copiar"
  - Alerta: "Esta senha não será exibida novamente. Anote antes de fechar."
  - Botão "Fechar"
- O modal só aparece uma vez (na criação, não na edição)

---

### #6 — Usuários Admin: erro genérico ao criar (Frontend)

**Problema:** Quando a criação de usuário admin falha (ex: e-mail já existe no Keycloak), a notificação exibe apenas "Falha ao salvar usuario admin." sem o motivo real.

**Comportamento esperado:**
- O handler de erro extrai `error.response.data.detail` (mesmo padrão já usado em `TenantForm.tsx`)
- A notificação exibe a mensagem real do backend
- Ex: "User with email X already exists in Keycloak" em vez da mensagem genérica

---

## Critérios de aceitação

1. Dashboard com ambiente vazio → Alert visível com botão "Criar tenant"
2. Botão de editar aparece na listagem de tenants → abre formulário pré-preenchido → salvar atualiza o nome
3. `gestor_email` visível na listagem e no detalhe do tenant → migration aplicada no staging
4. Badge de role nunca fica em branco — exibe "Sem role" quando array vazio
5. Criar usuário admin → modal com senha temporária aparece → botão Copiar funciona
6. Erro ao criar usuário admin → notificação exibe mensagem específica do backend
