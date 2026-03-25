# DELTA Sprint 2026-05-16 — Atualizações UTILIZACAO

> Para: DEV-4
> Sprint: 2026-05-16 | Status: ⏳ Pendente
> DEMs entregues: DEM-083, DEM-084, DEM-085, DEM-086

---

## O que mudou para o usuário final

### DEM-084 — Cadastro de Paciente com Identidade Centralizada

A partir desta sprint, o cadastro de novos pacientes é integrado ao sistema de identidade central do IntelliCare. Quando o CPF é informado no cadastro, o sistema garante automaticamente que o mesmo paciente não será duplicado entre estabelecimentos.

**Atualizar em** `UTILIZACAO/` (seção de cadastro de pacientes ou guia do módulo Clínico):
- Mencionar que o campo CPF no cadastro de paciente agora é recomendado (não obrigatório, mas importante para a identificação centralizada)
- Quando CPF é informado, o paciente recebe um identificador único no sistema que o acompanha em todos os estabelecimentos IntelliCare
- Não há mudança visual no formulário de cadastro — comportamento transparente para o usuário

---

## O que NÃO precisa ser documentado pelo DEV-4

- Detalhes do `modules/identity/`, `platform.pessoa`, `find_or_create_by_cpf()` — são internos
- ADR-004 — é documentação técnica de arquitetura, não de utilização
- Migrations 021/022/023 — operacionais, não afetam o usuário final
- Fix Redis, fix clinical_notes — não visíveis ao usuário

---

## Ação urgente — Eduardo (não DEV-4)

**Keycloak PLATFORM_ADMIN — ação requerida pendente.**
O DEV-1 reportou que o usuário `PLATFORM_ADMIN` no Keycloak tem uma "ação requerida pendente" que bloqueia o login e impediu o smoke live de idempotência do identity service em staging.

Verificar no console Keycloak (`http://auth.intellicare.ia.br/auth/admin`):
1. Realm `intellicare` → Users → `platform-admin`
2. Aba "Details" → verificar campo "Required User Actions"
3. Remover qualquer ação pendente (ex: `UPDATE_PASSWORD`, `VERIFY_EMAIL`)
4. Confirmar: login com `platform-admin` / `Admin@2025!` funciona no AdminUI

Isso é pré-condição para o smoke live do identity service na próxima sync.
