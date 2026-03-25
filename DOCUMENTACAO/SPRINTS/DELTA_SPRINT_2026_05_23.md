# DELTA Sprint 2026-05-23 — Atualizações UTILIZACAO

> Para: DEV-4
> Sprint: 2026-05-23 | Status: ⏳ Pendente
> DEMs entregues: DEM-087, DEM-088, DEM-089, DEM-090

---

## O que mudou para o usuário final

### DEM-088 — Cadastro de Profissional com Identidade Centralizada

A partir desta sprint, o cadastro de novos profissionais de saúde (médicos, enfermeiros, etc.) também é integrado ao sistema de identidade central do IntelliCare. O comportamento é idêntico ao cadastro de pacientes (DEM-084).

**Atualizar em** `UTILIZACAO/` (seção de cadastro de profissionais ou guia do módulo Clínico):
- O campo CPF no cadastro de profissional agora é recomendado para garantir identificação centralizada
- Quando CPF é informado, o profissional recebe um identificador único que o acompanha em todos os estabelecimentos IntelliCare
- Não há mudança visual no formulário — comportamento transparente

### DEM-089 — Admin: Página de Identidade Centralizada

Uma nova página foi adicionada ao módulo Administrativo (`/admin-ui/identity`).

**Atualizar em** `UTILIZACAO/` (guia do módulo Administrativo):
- Nova seção "Identidade" no painel admin
- Exibe: total de pessoas cadastradas, vínculos por estabelecimento, percentual de cobertura
- Botão "Reconciliar identidades": processa pacientes e profissionais existentes que têm CPF cadastrado mas ainda não têm vínculo de identidade central

---

## O que NÃO precisa ser documentado pelo DEV-4

- DEM-087 (JWT issuer + Traefik) — fix de infraestrutura, invisível ao usuário
- Migration 024 — operacional
- Detalhes de `find_or_create_by_cpf()`, `platform.pessoa`, `pessoa_estabelecimento` — internos
- DEM-090 staging sync — operacional

---

## Pendências DEV-4 acumuladas

> ⚠️ Lembrete: as seguintes sprints ainda têm DELTA pendente de aplicação:

| Sprint | DELTA | DEMs a documentar |
|--------|-------|-------------------|
| 2026-05-02 | `DELTA_SPRINT_2026_05_02.md` | DEM-075/076/077 |
| 2026-05-09 | `DELTA_SPRINT_2026_05_09.md` | DEM-079/080/081 |
| 2026-05-16 | `DELTA_SPRINT_2026_05_16.md` | DEM-084 |
| 2026-05-23 | Este arquivo | DEM-088/089 |
