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

## 2.2 Criacao de tenant (tela "Novo Tenant")

### Campos da tela

- `Nome` (obrigatorio)
- `Slug` (gerado automaticamente, identificador tecnico)
- `Email do gestor` (obrigatorio)

### Regras de preenchimento

- `Nome`: minimo 3 caracteres.
- `Slug`: 3 a 30 caracteres, apenas minusculas, numeros e `_`.
- `Email do gestor`: formato valido de e-mail.

### Exemplo preenchido

- Nome: `Clinica Sao Lucas`
- Slug: `clinica_sao_lucas`
- Email do gestor: `gestor.saolucas@cliente.com`

### Resultado esperado

- Notificacao de sucesso.
- Tenant aparece na lista.
- Gestor pode iniciar operacao no ambiente do tenant.

## 2.3 Edicao de tenant

### O que pode alterar

- Nome
- Email do gestor

### O que nao pode alterar

- `Slug` (imutavel apos criacao).

## 2.4 Boas praticas operacionais do perfil Admin

- Padronizar naming de tenant com cidade ou unidade.
- Validar e-mail do gestor antes de salvar.
- Revisar dashboard ao menos 1 vez por dia.
- Exportar PDF de tenants para fechamento semanal.
- Usar auditoria para rastrear mudancas sensiveis.
