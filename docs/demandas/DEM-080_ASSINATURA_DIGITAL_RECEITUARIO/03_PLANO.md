---
tipo: plano-execucao
demanda: DEM-080
titulo: Assinatura Digital Receituário
status: em-execucao
dev: DEV-1
criado: 2026-03-22
---

# DEM-080 — Plano de Execução

## Estimativa

Tempo estimado: ~5h | Complexidade: alta

`pyhanko` é uma biblioteca madura mas com API verbosa. Reservar tempo para testar a assinatura com um certificado A1 de teste real (pode ser gerado com OpenSSL — ver Bloco 1). A validação visual no Adobe Reader é obrigatória antes do commit.

---

## Ordem de execução

### Bloco 1 — Certificado A1 de teste (30min)
1. Gerar certificado A1 autoassinado para testes (não requer ICP-Brasil real em dev/staging):
```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/CN=DR TESTE SILVA/OU=CRM-SP 123456/O=IntelliCare/C=BR"
openssl pkcs12 -export -out test_cert.pfx -inkey key.pem -in cert.pem -passout pass:TestPass123
```
2. Guardar `test_cert.pfx` em `tests/fixtures/` — usado nos testes automatizados

### Bloco 2 — Migration e storage (45min)
3. Criar `019_professional_certificates.sql`
4. Implementar `encrypt_certificate()` / `decrypt_certificate()` em `shared/crypto.py`
5. Adicionar `SERVER_ENCRYPTION_KEY` em `settings.py` e `.env.example`
6. Implementar `upload_certificate()`, `get_certificate()`, `delete_certificate()` em `professionals/services.py`

### Bloco 3 — `pdf_signer.py` (60min)
7. Implementar `sign_pdf()` em `oswaldo/pdf_signer.py`
8. Testar isolado: `sign_pdf(pdf_bytes, pfx_bytes, "TestPass123")` → PDF assinado
9. Abrir o PDF resultante no Adobe Reader / Chrome — verificar painel de assinaturas mostra assinatura válida
10. Testar falha: senha errada → `ValueError` capturado, não propaga para o usuário

### Bloco 4 — Integração `generate_receituario()` (30min)
11. Modificar `generate_receituario()` para chamar `sign_pdf()` se certificado disponível
12. Garantir try/except — falha na assinatura nunca bloqueia geração do PDF

### Bloco 5 — Endpoints e Frontend (60min)
13. Criar endpoints em `professionals/routes.py` (POST upload, GET status, DELETE)
14. Em `ClinicoUI/ProfilePage.tsx`, adicionar seção "Certificado Digital":
    - Se sem certificado: campo file (.pfx) + campo senha + botão "Enviar Certificado"
    - Se com certificado: exibir nome (`subject_name`) + validade + botão "Remover"

### Bloco 6 — Testes (30min)
15. Criar `test_assinatura_digital.py` com os 4 testes usando `test_cert.pfx` das fixtures
16. `pytest test_assinatura_digital.py test_oswaldo_receituario.py -v` — sem regressões

---

## Gotcha — `pyhanko` exige PDF já finalizado

`pyhanko` usa `IncrementalPdfFileWriter` — o PDF precisa estar completo antes da assinatura. Chamar `sign_pdf()` **após** `render_pdf()` retornar os bytes finais. Nunca tentar assinar um PDF ainda sendo gerado pelo WeasyPrint.

---

## Gotcha — `SERVER_ENCRYPTION_KEY` deve ser estável

Se a `SERVER_ENCRYPTION_KEY` for rotacionada (trocada no `.env`), todos os certificados armazenados no banco ficam ilegíveis — o Fernet não consegue descriptografar com chave diferente. Documentar isso explicitamente no `.env.example`.

Para staging: gerar uma chave fixa e registrar em local seguro antes do deploy:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

---

## Gotcha — validação do certificado A1 no staging

O certificado de teste (autoassinado) não terá cadeia de confiança ICP-Brasil. Adobe Reader pode mostrar "Certificado não confiável" mas a assinatura estará tecnicamente válida. Para produção, o médico usa certificado emitido por AC credenciada ICP-Brasil — aí o Adobe mostrará como válido e confiável.

---

## Entrega

```
feat(receituario): assinatura digital ICP-Brasil A1 — pyhanko, upload certificado, sign_pdf
```
Hash → enviar ao ARQUITETO após `git push origin HEAD:main` confirmado.
