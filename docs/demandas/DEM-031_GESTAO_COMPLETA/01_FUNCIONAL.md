# DEM-031 — Gestão Completa (GestorUI)

## Objetivo

Fechar o módulo de Gestão do IntelliCare V3. O TENANT_GESTOR passa a ter controle total de sua organização: unidades de saúde, equipes alocadas em cada unidade e usuários do tenant.

---

## Estado atual do GestorUI

| Área | Status |
|------|--------|
| Dashboard | ✅ funcionando |
| Lista de Pacientes | ✅ funcionando |
| Documentos | ✅ funcionando |
| Relatório de Uso | ✅ funcionando |
| **Unidades** | ❌ não implementado |
| **Usuários do Tenant** | ❌ não implementado |

---

## 1. Unidades de Saúde

Gestão das unidades físicas ou virtuais que compõem o tenant (UBS, hospital, clínica, secretaria, etc.).

### Listagem
- Tabela: nome, tipo, CNES (se aplicável), cidade/estado, gestor responsável, status (ativa/inativa)
- Filtros: status, tipo
- Badge colorido por status

### Cadastro / Edição
- Campos: nome*, tipo* (UBS/Hospital/Clínica/Secretaria/Outro), CNES, endereço completo, telefone, e-mail, gestor responsável (usuário do tenant), status*
- Validações: campos obrigatórios marcados com *

### Detalhe da Unidade
- Informações gerais
- Aba **Equipe**: profissionais alocados nesta unidade (nome, especialidade, carga horária)
- Aba **Pacientes**: contador de pacientes vinculados

### Ações
- Adicionar unidade
- Editar unidade
- Ativar / Desativar
- Alocar / Remover profissional da unidade

---

## 2. Usuários do Tenant

Gestão de quem acessa o sistema dentro do tenant, com controle de papel e unidade de alocação.

### Perfis (roles dentro do tenant)
| Perfil | Acesso |
|--------|--------|
| `gestor` | Acesso total ao GestorUI |
| `clinico` | Acesso ao ClinicoUI |
| `recepcionista` | Agenda + cadastro de pacientes (futuro) |

### Listagem
- Tabela: nome, e-mail, perfil, unidade alocada, status (ativo/inativo), último acesso

### Cadastro
- Campos: nome*, e-mail*, perfil*, unidade* (select das unidades ativas)
- Convite por e-mail via Keycloak (senha temporária)

### Ações
- Convidar usuário
- Alterar perfil / unidade
- Ativar / Desativar
- Remover

---

## Critérios de aceitação

1. Unidades acessíveis via sidebar do GestorUI
2. Usuários do Tenant acessíveis via sidebar
3. Dashboard atualizado com contagem de unidades ativas
4. Filtros e paginação em todas as listagens
5. Feedback visual em todas as ações
