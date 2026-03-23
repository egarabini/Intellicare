---
tipo: especificacao-tecnica
demanda: DEM-080
titulo: Assinatura Digital Receituário
---

# DEM-080 — Especificação Técnica

## Mapa de mudanças

| Arquivo | Tipo | O que muda |
|---------|------|-----------|
| `db/platform_migrations/019_professional_certificates.sql` | **Novo** | Tabela `professional_certificates` por tenant |
| `modules/professionals/services.py` | Modificar | `upload_certificate()`, `get_certificate()`, `delete_certificate()` |
| `modules/professionals/routes.py` | Modificar | `POST /professionals/me/certificate`, `DELETE /professionals/me/certificate` |
| `modules/professionals/schemas.py` | Modificar | `CertificateUploadResponse`, `CertificateStatusOut` |
| `modules/oswaldo/pdf_signer.py` | **Novo** | `sign_pdf(pdf_bytes, pfx_bytes, password) → bytes` via pyhanko |
| `modules/oswaldo/services.py` | Modificar | `generate_receituario()` — chama `sign_pdf()` se certificado disponível |
| `frontend/ClinicoUI/src/pages/ProfilePage.tsx` | Modificar | Seção "Certificado Digital" — upload .pfx + senha + status + remoção |
| `packages/intellicare-core/tests/test_assinatura_digital.py` | **Novo** | 4+ testes |

---

## Migration 019 — `professional_certificates`

```sql
-- Schema do tenant (não platform)
CREATE TABLE {schema}.professional_certificates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    professional_id UUID NOT NULL REFERENCES {schema}.professionals(id) ON DELETE CASCADE,
    pfx_encrypted   BYTEA NOT NULL,        -- certificado .pfx criptografado com SERVER_ENCRYPTION_KEY
    password_hash   TEXT NOT NULL,          -- senha criptografada (Fernet)
    subject_name    TEXT,                   -- CN do certificado (ex: "DR JOAO SILVA:12345678900")
    valid_until     DATE,                   -- data de validade do certificado
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_professional_certificate UNIQUE (professional_id)  -- 1 cert por profissional
);
```

---

## `modules/oswaldo/pdf_signer.py`

```python
from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec
from pyhanko import stamp
from pyhanko_certvalidator import CertificateValidator
import io

def sign_pdf(pdf_bytes: bytes, pfx_bytes: bytes, pfx_password: str) -> bytes:
    """
    Assina digitalmente um PDF com certificado PKCS#12 (A1 ICP-Brasil).
    Retorna PDF assinado. Lança ValueError se certificado inválido.
    """
    signer = signers.SimpleSigner.load_pkcs12(
        pfx_data=pfx_bytes,
        passphrase=pfx_password.encode(),
    )

    pdf_writer = IncrementalPdfFileWriter(io.BytesIO(pdf_bytes))

    sig_meta = signers.PdfSignatureMetadata(
        field_name="Signature",
        reason="Assinatura Digital ICP-Brasil",
        location="IntelliCare",
        certify=False,
    )

    output = io.BytesIO()
    signers.sign_pdf(
        pdf_writer,
        signature_meta=sig_meta,
        signer=signer,
        output=output,
    )
    return output.getvalue()
```

---

## `generate_receituario()` — integração

```python
def generate_receituario(prescription_id: UUID, type: PrescriptionType, ctx) -> bytes:
    # ... lógica existente ...
    pdf_bytes = render_pdf(template, receituario_data)

    # Tentar assinar se profissional tem certificado
    cert = get_certificate(prescription.professional_id, ctx)
    if cert:
        try:
            pfx_bytes = decrypt_certificate(cert.pfx_encrypted)
            pfx_password = decrypt_password(cert.password_hash)
            pdf_bytes = sign_pdf(pdf_bytes, pfx_bytes, pfx_password)
        except Exception as e:
            logger.warning(f"Assinatura falhou para professional_id={prescription.professional_id}: {e}")
            # Retorna PDF sem assinatura — nunca bloqueia a geração

    return pdf_bytes
```

---

## Endpoints

```
POST /professionals/me/certificate
Content-Type: multipart/form-data
Body: file (.pfx), password (string)
→ 201 CertificateUploadResponse {subject_name, valid_until, uploaded_at}

GET /professionals/me/certificate
→ 200 CertificateStatusOut {has_certificate, subject_name, valid_until} | 404

DELETE /professionals/me/certificate
→ 204 No Content
```

---

## Dependência nova

```bash
pip install pyhanko pyhanko-certvalidator cryptography
```

Adicionar ao `requirements.txt` do core package.

---

## Criptografia do certificado em repouso

O `.pfx` e a senha são criptografados antes de armazenar no banco usando `cryptography.fernet`:

```python
from cryptography.fernet import Fernet

def encrypt_certificate(pfx_bytes: bytes) -> bytes:
    f = Fernet(get_settings().server_encryption_key)
    return f.encrypt(pfx_bytes)

def decrypt_certificate(pfx_encrypted: bytes) -> bytes:
    f = Fernet(get_settings().server_encryption_key)
    return f.decrypt(pfx_encrypted)
```

Nova variável de ambiente: `SERVER_ENCRYPTION_KEY` — gerada com `Fernet.generate_key()`, deve ser estável (rotação de chave invalida certificados armazenados).

---

## Testes — `test_assinatura_digital.py`

| Teste | Cenário |
|-------|---------|
| `test_upload_certificate_stores_encrypted` | Upload .pfx → armazenado criptografado, não como texto plano |
| `test_receituario_signed_when_certificate_exists` | Médico com cert → PDF retornado tem assinatura digital |
| `test_receituario_unsigned_when_no_certificate` | Médico sem cert → PDF retornado sem assinatura, sem erro |
| `test_delete_certificate_removes_signature` | Após DELETE → próximo receituário sem assinatura |
