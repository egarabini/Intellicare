# DEM-032 — Clínico: Gestão de Equipes e Profissionais

## Objetivo

Fechar o módulo Clínico do IntelliCare V3 com a gestão de quem atende. O CLINICO passa a visualizar e administrar os grupos de profissionais, os profissionais de saúde cadastrados e os usuários do ambiente clínico de sua unidade.

---

## Estado atual do ClinicoUI

| Área | Status |
|------|--------|
| Dashboard + Agenda | ✅ funcionando |
| Lista de Pacientes + Perfil | ✅ funcionando |
| Prontuário (Encontros + CID-10) | ✅ funcionando |
| AI Assistant | ✅ funcionando |
| Meu Perfil | ✅ funcionando |
| **Grupos de Profissionais** | ❌ não implementado |
| **Profissionais de Saúde** | ❌ não implementado |
| **Usuários do Clínico** | ❌ não implementado |

---

## 1. Grupos de Profissionais

Agrupamento lógico de profissionais por especialidade, equipe ou função (ex: Equipe de Saúde da Família, Equipe de Saúde Mental, Plantão UTI).

### Listagem
- Tabela: nome do grupo, tipo/especialidade, quantidade de profissionais, unidade associada, status (ativo/inativo)
- Filtros: status, unidade

### Cadastro / Edição
- Campos: nome*, tipo/especialidade*, unidade*, descrição, status*

### Detalhe do Grupo
- Lista de profissionais do grupo (nome, CRM/CRE, especialidade)
- Ações: adicionar / remover profissional do grupo

---

## 2. Profissionais de Saúde

Cadastro dos profissionais que atuam no tenant/unidade.

### Listagem
- Tabela: nome, conselho profissional (CRM/COREN/etc.), número, especialidade, grupo(s), unidade, status
- Filtros: status, especialidade, unidade, grupo

### Cadastro / Edição
- Campos: nome*, tipo de conselho* (CRM/COREN/CRO/CRP/CREFITO/Outro), número do conselho*, especialidade*, unidade*, grupo(s) (multiselect), telefone, e-mail, status*
- Link com usuário Keycloak (campo opcional: vincular ao e-mail do usuário existente)

### Ações
- Adicionar profissional
- Editar dados
- Ativar / Desativar
- Vincular / Desvincular de grupo
- Vincular conta de usuário

---

## 3. Usuários do Clínico

Visão dos usuários que têm acesso ao ClinicoUI dentro da unidade do profissional logado.

> **Nota:** Esta tela é somente leitura para o CLINICO — a gestão de convites é feita pelo GESTOR (DEM-031). O clínico visualiza quem está ativo na sua unidade.

### Listagem
- Tabela: nome, e-mail, função/especialidade, status (ativo/inativo), último acesso
- Filtro: status

---

## Critérios de aceitação

1. Grupos de Profissionais acessível via sidebar do ClinicoUI
2. Profissionais de Saúde acessível via sidebar
3. Usuários do Clínico acessível via sidebar (somente leitura)
4. Dashboard clínico atualizado com contagem de profissionais ativos e grupos
5. Filtros e paginação em todas as listagens
6. Feedback visual em todas as ações
