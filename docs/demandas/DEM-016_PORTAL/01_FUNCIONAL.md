# DEM-016 — Portal de Entrada IntelliCare

## 1. Contexto e Motivação

O IntelliCare V3 possui três interfaces distintas (AdminUI, GestorUI, ClinicoUI), mas não existe um ponto de entrada unificado. O usuário precisa conhecer a URL exata da sua interface, o que é inviável em produção. O Portal resolve isso: é a única URL que o usuário precisa saber — `https://app.intellicare.com.br` — e o sistema cuida do resto.

---

## 2. Escopo

### Incluído

| Funcionalidade | Detalhe |
|---|---|
| Login único | OIDC via Keycloak realm `intellicare` |
| Roteamento por role | Lê o JWT e redireciona para a UI correta |
| Logout centralizado | Encerra sessão Keycloak e retorna ao portal |
| Tela de acesso negado | Para usuários autenticados sem role reconhecido |
| Tela de loading | Enquanto o token é validado |
| Identidade visual | Logo IntelliCare, fundo clean, responsivo |

### Fora do Escopo

- Cadastro de novos usuários (fluxo do AdminUI)
- Recuperação de senha (fluxo do Keycloak)
- Página de marketing/institucional

---

## 3. Fluxo Principal

```
Usuário acessa /
       ↓
Portal verifica sessão OIDC
       ↓
   Não autenticado → redireciona para Keycloak login
       ↓
   Autenticado → lê role do JWT
       ↓
   PLATFORM_ADMIN  → /admin-ui/
   TENANT_GESTOR   → /gestor-ui/
   CLINICO         → /clinico-ui/
   role desconhecido → tela "Acesso não autorizado"
```

---

## 4. Requisitos Funcionais

| ID | Requisito |
|---|---|
| RF-01 | Usuário não autenticado é redirecionado para login Keycloak automaticamente |
| RF-02 | Após login, portal lê o role do JWT e redireciona sem interação manual |
| RF-03 | PLATFORM_ADMIN vai para `/admin-ui/` |
| RF-04 | TENANT_GESTOR vai para `/gestor-ui/` |
| RF-05 | CLINICO vai para `/clinico-ui/` |
| RF-06 | Role não reconhecido exibe tela de erro com opção de logout |
| RF-07 | Logout encerra sessão no Keycloak e retorna ao portal |
| RF-08 | Portal é servido em `/` pelo FastAPI |

---

## 5. Requisitos Não Funcionais

| ID | Requisito |
|---|---|
| RNF-01 | Tempo de redirecionamento < 1 s após login |
| RNF-02 | Bundle < 100 KB gzip (portal é mínimo — só lógica de roteamento) |
| RNF-03 | Sem uso de localStorage (tokens apenas em memória) |
| RNF-04 | Responsivo — funciona em mobile e desktop |

---

## 6. Critérios de Aceite

- [ ] Acessar `/` sem sessão redireciona para Keycloak
- [ ] Login com `platform-admin` redireciona para `/admin-ui/`
- [ ] Login com `gestor-dev` redireciona para `/gestor-ui/`
- [ ] Login com `clinico-dev` redireciona para `/clinico-ui/`
- [ ] Usuário sem role reconhecido vê tela "Acesso não autorizado" com botão Sair
- [ ] Logout retorna para `/` (portal) com sessão encerrada
- [ ] FastAPI serve `GET /` com status 200
- [ ] Bundle < 100 KB gzip

---

## 7. Dependências

| DEM | Razão |
|---|---|
| DEM-004 | Keycloak realm com roles e usuários configurados |
| DEM-006 | AdminUI disponível em `/admin-ui/` |
| DEM-012 | GestorUI disponível em `/gestor-ui/` |
| DEM-015 | ClinicoUI disponível em `/clinico-ui/` |
