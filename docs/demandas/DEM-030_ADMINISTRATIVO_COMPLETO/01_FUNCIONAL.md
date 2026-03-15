# DEM-030 — Administrativo Completo

## Objetivo

Fechar o módulo Administrativo do IntelliCare V3, cobrindo as 4 áreas que ainda não estão implementadas: **Servidores**, **Módulos**, **Financeiro** e **Usuários Administrativos**. Ao final, o PLATFORM_ADMIN terá controle total da plataforma a partir de uma única interface.

---

## Estado atual do AdminUI

| Área | Status |
|------|--------|
| Dashboard (stats gerais) | ✅ funcionando |
| Tenants — listagem + CRUD | ✅ funcionando |
| Auditoria de plataforma | ✅ funcionando |
| **Servidores** | ❌ não implementado |
| **Módulos** | ❌ não implementado |
| **Financeiro** | ❌ não implementado |
| **Usuários Administrativos** | ❌ não implementado |

---

## 1. Servidores

Controle da infraestrutura física/cloud utilizada pela plataforma.

### Listagem
- Tabela com: nome, tipo (VPS/Dedicado/Cloud), provedor (Hetzner/AWS/GCP/Azure/DigitalOcean), região, CPU, RAM, disco, custo mensal (R$), status (ativo/inativo/manutenção)
- Filtros por: status, tipo, provedor
- Badge colorido por status

### Cadastro / Edição
- Campos: nome*, tipo*, provedor*, região*, IP/hostname, vCPU*, RAM (GB)*, disco (GB)*, custo mensal (R$)*, status*, observações
- Validações: campos obrigatórios marcados com *

### Dashboard (card no painel principal)
- Total de servidores ativos
- Custo mensal total de infraestrutura

### Ações
- Adicionar servidor
- Editar servidor
- Alterar status (ativo/inativo/manutenção)
- Remover servidor (somente se não tiver tenants associados)

---

## 2. Módulos

Controle dos módulos da plataforma e quais estão habilitados por tenant.

### Listagem de Módulos da Plataforma
- Tabela com: nome, slug, versão, descrição, status global (ativo/inativo/em desenvolvimento)
- Status "em desenvolvimento" bloqueia habilitação por tenants
- Indicador de quantos tenants têm o módulo ativo

### Configuração por Tenant
- Na tela de detalhe do tenant: aba "Módulos" com toggle ativo/inativo para cada módulo disponível
- Módulos "em desenvolvimento" aparecem desabilitados (não podem ser ativados)

### Ações
- Alterar status global do módulo (ativo/inativo/em desenvolvimento)
- Ativar/desativar módulo por tenant

---

## 3. Financeiro

Visão financeira completa da plataforma: receitas, despesas e resultado.

### Dashboard Financeiro
- Receita do mês corrente (faturas pagas)
- Despesa do mês corrente (servidores + despesas avulsas)
- Resultado (receita − despesa)
- Gráfico de tendência: últimos 6 meses (receita vs despesa)
- Inadimplência: valor em aberto de faturas vencidas

### Faturas (Receita)
- Listagem por tenant: valor, vencimento, status (pendente/pago/vencido), data pagamento
- Filtros: status, tenant, mês/ano
- Ações: marcar como pago, gerar nova fatura, cancelar

### Despesas
- Listagem: categoria (infraestrutura/licença/pessoal/outro), descrição, valor, data, tenant relacionado (opcional)
- Ações: adicionar despesa, editar, remover

### Relatório Mensal (simples)
- Tabela: mês | receita | despesa | resultado
- Últimos 12 meses

---

## 4. Usuários Administrativos

Gestão de quem pode acessar o painel administrativo e com qual nível de acesso.

### Perfis (roles dentro do PLATFORM_ADMIN)
| Perfil | Acesso |
|--------|--------|
| `admin` | Acesso total |
| `financ` | Somente área Financeiro + Dashboard |
| `coordenador` | Tenants + Módulos + Dashboard (sem Financeiro e sem Usuários) |

### Listagem
- Tabela: nome, e-mail, perfil, status (ativo/inativo), último acesso, data criação

### Cadastro
- Campos: nome*, e-mail*, perfil*, status*
- Envio de convite por e-mail (cria usuário no Keycloak com senha temporária)

### Ações
- Convidar novo usuário
- Alterar perfil
- Ativar/desativar acesso
- Remover usuário

---

## Critérios de aceitação globais

1. Todas as 4 novas áreas acessíveis via sidebar do AdminUI
2. Dashboard principal atualizado com card de infraestrutura (custo mensal servidores)
3. Nenhuma área existente (Tenants, Auditoria) deve ser quebrada
4. Filtros e paginação em todas as listagens
5. Feedback visual em todas as ações (loading, sucesso, erro)
6. Responsivo (funciona em telas 1280px+)
