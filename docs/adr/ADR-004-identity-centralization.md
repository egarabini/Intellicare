# ADR-004 - Centralizacao de Identidade em `platform.pessoa`

## Status
Accepted

## Contexto

O IntelliCare opera em multi-tenancy por schema PostgreSQL. Hoje, a mesma pessoa fisica pode
existir em varios schemas de tenant como registros independentes. Isso cria tres problemas
estruturais:

- duplicacao cross-tenant de identidade para o mesmo CPF
- divergencia de dados cadastrais entre estabelecimentos
- dificuldade operacional e juridica para LGPD, auditoria e reconciliacao

Na pratica, um paciente pode atualizar telefone em uma clinica e permanecer desatualizado nas
demais. O mesmo vale para profissionais e, futuramente, para empresas conveniadas. Com o
crescimento da rede, esse custo operacional deixa de ser excecao e vira propriedade do sistema.

Ao mesmo tempo, o IntelliCare ja consolidou a estrategia de multi-tenancy por schema e nao deve
romper essa base com uma mudanca abrupta ou com uma dependencia externa prematura.

## Decisao

Criar `platform.pessoa` como Single Source of Truth para identidade cross-tenant.

A fundacao sera composta por:

- `platform.pessoa` como entidade base
- `platform.pessoa_fisica` para atributos civis de pessoa fisica
- `platform.pessoa_juridica` para atributos civis de pessoa juridica
- `platform.pessoa_contato` para contatos unificados
- `platform.pessoa_estabelecimento` para vinculo pessoa x tenant com semantica de consentimento

Os schemas de tenant permanecem com seus dados operacionais. A relacao futura entre registros
operacionais e a identidade central sera feita por `pessoa_id` UUID logico na aplicacao.

## Alternativas Consideradas

### 1. Manter duplicacao por tenant

Descartado. Escala mal para LGPD, conciliacao, auditoria e governanca de dados.

### 2. Centralizar em `public`

Descartado. O projeto ja usa `public` como namespace operacional legado e de apoio. Misturar
identidade fundacional com o namespace padrao aumenta acoplamento e ambiguidade sem ganho tecnico.

### 3. Criar um microservico externo de identidade

Descartado. Introduz complexidade de rede, deploy, observabilidade e consistencia distribuida antes
de o problema exigir essa separacao. Nesta fase, a centralizacao no mesmo banco e suficiente.

## Consequencias

- Novos fluxos que precisarem de identidade unificada devem executar `find-or-create` por CPF antes
  de criar registros operacionais de tenant.
- Dados existentes nao serao migrados nesta DEM. A reconciliacao historica sera gradual.
- `pessoa_id` em schemas de tenant sera uma FK logica, nao fisica, para preservar portabilidade
  entre bancos e evitar acoplamento estrutural entre schemas.
- Consultas cross-tenant de identidade passam a existir no schema `platform`, com responsabilidade
  de acesso mais restrita do que os modulos tenant-scoped.

## Plano de Migracao Gradual

1. Criar a fundacao de identidade em `platform`.
2. Expor modulo `identity` com lookup e `find-or-create` por CPF.
3. Nas DEMs seguintes, adicionar `pessoa_id` logico aos registros de paciente e profissional.
4. Migrar dados historicos por reconciliacao de CPF, com auditoria e tratamento de ambiguidades.

## Relacao com outros ADRs

- ADR-001 continua valido: `identity` e um executor do tipo `Worker`/servico de apoio, sem efeito
  externo irreversivel por si so.
- ADR-002 continua valido: a camada de IA consome contexto clinico, nao define a fonte de verdade
  de identidade.
