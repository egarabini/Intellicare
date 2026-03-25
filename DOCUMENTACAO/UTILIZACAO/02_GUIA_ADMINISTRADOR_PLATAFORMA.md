# 2. Guia do Administrador da Plataforma (AdminUI)

## Menu principal

- `Dashboard`
- `Tenants`
- `Servidores`
- `Modulos`
- `Financeiro`
- `Usuarios Admin`
- `Auditoria`

## 2.1 Dashboard da plataforma

### O que o admin visualiza

- Total de tenants
- Tenants ativos
- Tenants suspensos
- Receita mensal
- Servidores ativos
- Custo de infraestrutura mensal
- Lista embarcada de tenants
- Exportacao de PDF de tenants ativos

### Exemplo de leitura de resultado

- Total tenants: `18`
- Ativos: `16`
- Suspensos: `2`
- Receita mensal: `R$ 124.500,00`
- Custo infra: `R$ 21.700,00`

Interpretacao: margem operacional positiva e 2 tenants com necessidade de acao comercial/suporte.

## 2.2 Provisionamento de tenant (TenantsManager)

### Fluxo atual (DEM-065)

No menu `Tenants`, o Admin opera pela tela **Gestao de Tenants** (`TenantsManager`) com dois caminhos:

- `Provisionar Tenant` (fluxo recomendado para onboarding completo);
- `Novo Tenant` (cadastro direto quando necessario).

### Campos de provisionamento

- `Slug` (identificador tecnico)
- `Nome`
- `Email do Gestor`
- `Plano` (quando habilitado na instancia/politica do ambiente)

### Regras de preenchimento

- `Slug`: 3-30 caracteres, minusculas, numeros e `_`.
- `Nome`: minimo 3 caracteres.
- `Email do Gestor`: formato valido.
- `Plano`: selecionar o plano vigente do contrato do tenant.

### Exemplo de provisionamento

- Slug: `clinica_sao_lucas`
- Nome: `Clinica Sao Lucas`
- Email do Gestor: `gestor.saolucas@cliente.com`
- Plano: `PRO`

### Resultado esperado

- Tenant provisionado com sucesso.
- Tenant aparece na grade com status inicial.
- Admin pode abrir detalhe e configuracoes do tenant.

## 2.3 Operacao do ciclo de vida do tenant

### Acoes operacionais no TenantsManager

- `Suspender`: bloqueia operacao do tenant para novas requisicoes.
- `Reativar`: retorna tenant suspenso ao estado ativo.
- `Configurações`: abre `TenantConfigPage` para parametros do tenant (incluindo plano, quando aplicavel).
- `Remover (soft-delete)`: remove acesso sem apagar schema.

### Boas praticas de governanca

- Suspender tenant somente com registro de motivo operacional/comercial.
- Reativar apenas apos regularizacao de pendencia.
- Manter configuracoes (ex.: plano) coerentes com contrato vigente.

## 2.4 Boas praticas operacionais do perfil Admin

- Padronizar naming de tenant com cidade ou unidade.
- Validar e-mail do gestor antes de salvar.
- Revisar dashboard ao menos 1 vez por dia.
- Exportar PDF de tenants para fechamento semanal.
- Usar auditoria para rastrear mudancas sensiveis.

## 2.5 Portal de Agentes

> As imagens dos agentes foram renomeadas — o sufixo `_ia` foi removido. Padrão atual: `agente_florence.png`, `agente_oswaldo.png`, `agente_marie.png` (sem `_ia`). Não afeta a interface visual.

## 2.6 Identidade Centralizada

Nova página disponível em AdminUI → "Identidade" (`/admin-ui/identity`).

### Cards de totais
- Total de pessoas cadastradas na plataforma
- Vínculos por estabelecimento
- Cobertura percentual

### Tabela por tenant
- Pacientes e profissionais com/sem identidade vinculada
- Percentual de cobertura por tenant

### Botão "Reconciliar identidades"
- Processa registros existentes que têm CPF mas ainda não têm vínculo de identidade central
- Exige confirmação antes de executar
- Retorna relatório: quantos registros foram processados e vinculados
- Operação idempotente: pode ser executada mais de uma vez sem risco
