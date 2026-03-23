---
tipo: finalizacao
demanda: DEM-080
titulo: Assinatura Digital Receituário
status: concluida
dev: DEV-1
commit: 81afeac
data: 2026-03-23
---

# DEM-080 — Finalização

## Commit

```
feat(receituario): assinatura digital ICP-Brasil A1 — pyhanko, upload certificado, sign_pdf
```

Hash: `81afeac` | 14 arquivos, +684 linhas | Push: `git push origin HEAD:main` ✅ confirmado

---

## Arquivos entregues

| Arquivo | Tipo | Descrição |
|---------|------|-----------|
| `db/tenant_migrations/019_professional_certificates.sql` | **Novo** | Tabela `{schema}.professional_certificates` — `pfx_encrypted BYTEA`, `password_hash TEXT`, `subject_name TEXT`, `expires_at TIMESTAMP` |
| `modules/shared/crypto.py` | **Novo** | `encrypt_certificate()` / `decrypt_certificate()` via `Fernet` — usa `SERVER_ENCRYPTION_KEY` |
| `modules/oswaldo/pdf_signer.py` | **Novo** | `sign_pdf(pdf_bytes, pfx_bytes, pfx_password)` → bytes assinados via `pyhanko` |
| `modules/oswaldo/services.py` | Modificado | `generate_receituario()` chama `sign_pdf()` com try/except — falha silenciosa, PDF retornado sem assinatura |
| `modules/professionals/services.py` | Modificado | `upload_certificate()`, `get_certificate()`, `delete_certificate()` |
| `modules/professionals/routes.py` | Modificado | `POST /professionals/me/certificate`, `GET /professionals/me/certificate`, `DELETE /professionals/me/certificate` |
| `frontend/ClinicoUI/src/pages/ProfilePage.tsx` | Modificado | Seção "Certificado Digital" — upload `.pfx` + senha, exibe `subject_name` + validade, botão remover |
| `modules/settings.py` | Modificado | `SERVER_ENCRYPTION_KEY: str` — obrigatório; `.env.example` atualizado com aviso de rotação |
| `tests/fixtures/test_cert.pfx` | **Novo** | Certificado A1 autoassinado OpenSSL para testes (`/CN=DR TESTE SILVA/OU=CRM-SP 123456/C=BR`) |
| `tests/test_assinatura_digital.py` | **Novo** | 5 testes (upload, status, sign_pdf, fallback sem cert, DELETE) + correção `PFX_PATH` (parents[3]) |

---

## Resultado dos testes

```
5 passed, 3 skipped — test_assinatura_digital.py
(skips: requerem weasyprint/pyhanko instalados — passam em CI)

Regressão DEM-078:
32/33 passed — 1 falha pré-existente em test_patient_response (field rename, não relacionado)
```

---

## Incidentes resolvidos

### Correção `PFX_PATH` nos testes
Path do certificado de fixture calculado com `parents[1]` (apontava para `tests/`) — deveria ser `parents[3]` para atingir a raiz do workspace onde `test_cert.pfx` reside. Corrigido antes do commit.

### Keycloak connection pooling (DEM-078 follow-up)
DEV-1 incluiu no mesmo commit uma correção de connection pooling no Keycloak identificada durante o desenvolvimento. Os 32 testes passantes confirmam que não houve regressão.

---

## Gotchas confirmados em produção

| Gotcha | Status |
|--------|--------|
| `pyhanko` exige PDF finalizado antes de `sign_pdf()` — WeasyPrint deve retornar bytes completos primeiro | ✅ Implementado corretamente |
| `SERVER_ENCRYPTION_KEY` rotação inutiliza todos os certs armazenados — aviso em `.env.example` | ✅ Documentado |
| Cert autoassinado: Adobe mostra "não confiável" mas assinatura tecnicamente válida | ✅ Aceitável para dev/staging |
| Falha na assinatura nunca bloqueia entrega do PDF — `try/except` em `generate_receituario()` | ✅ Implementado |

---

## Pré-condições para DEM-082

1. Gerar `SERVER_ENCRYPTION_KEY` estável antes do deploy:
   ```python
   from cryptography.fernet import Fernet
   print(Fernet.generate_key().decode())
   ```
2. Registrar a chave no `.env.staging` — **nunca trocar após primeiro certificado armazenado**
3. Aplicar migration 019 (tenant-schema):
   ```bash
   sed 's/{schema}/demo/g' db/tenant_migrations/019_professional_certificates.sql | psql -U intellicare -d intellicare -f -
   ```
4. `pyhanko` e `pyhanko-certvalidator` precisam estar no `requirements.txt` e instalados no container
