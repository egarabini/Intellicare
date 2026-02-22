# Relatório de Análise — Erros Docker no Servidor de Staging

**Data:** 2026-02-22  
**Módulos afetados:** oswaldo, donabedian, comunicacao  
**Objetivo:** Identificar causa raiz e procedimentos para correção (sem alterações de código)

---

## 1. Resumo Executivo

| Módulo | Erro | Causa raiz |
|--------|------|------------|
| **oswaldo** | `sqlalchemy.exc.MissingGreenlet` | Incompatibilidade: URL usa driver async (`asyncpg`) com engine síncrono (`create_engine`) |
| **donabedian** | `ModuleNotFoundError: No module named 'intellicare_auth'` | Pacote `intellicare-auth` não instalado na imagem Docker |
| **comunicacao** | `ImportError: email-validator is not installed` | Dependência `email-validator` não presente no ambiente de execução |

---

## 2. Análise Detalhada por Módulo

### 2.1. Oswaldo — MissingGreenlet

**Erro completo:**
```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here.
Was IO attempted in an unexpected place?
```

**Causa raiz:**

- O `.env.homologacao` define `INTELLICARE_OSWALDO_DATABASE_URL=postgresql+asyncpg://...`
- O driver `asyncpg` é **assíncrono** e exige contexto async (greenlet/event loop)
- O módulo Oswaldo usa `FHIRDataStore` (`intellicare-oswaldo/oswaldo/datastore/fhir_datastore.py`), que chama `create_engine(db_url)` — engine **síncrono**
- Ao passar URL com `postgresql+asyncpg`, o SQLAlchemy tenta usar asyncpg em contexto síncrono, gerando o `MissingGreenlet`

**Procedimento para o desenvolvedor:**

1. **Opção A (recomendada):** Alterar a URL no `.env` de homologação para driver síncrono:
   - De: `postgresql+asyncpg://...`
   - Para: `postgresql+psycopg://...` ou `postgresql://...` (psycopg é o padrão)
2. **Opção B:** Refatorar o Oswaldo para usar `create_async_engine` e sessões async em todo o fluxo (mais trabalhoso).
3. Garantir que `psycopg` (ou `psycopg[binary]`) esteja em `intellicare-oswaldo/requirements.txt` ou `pyproject.toml` — já está em `requirements.txt`.

---

### 2.2. Donabedian — ModuleNotFoundError: intellicare_auth

**Erro completo:**
```
ModuleNotFoundError: No module named 'intellicare_auth'
  File "/app/src/donabedian/api/routes/indicators.py", line 23, in <module>
    from intellicare_auth import get_current_user, requires_role
```

**Causa raiz:**

- O código importa `intellicare_auth` em `indicators.py` e `pillars.py`
- O `pyproject.toml` do donabedian **não** declara `intellicare-auth` como dependência (há apenas comentário: "Add local path: pip install -e ../intellicare-auth")
- O `Dockerfile` do donabedian instala apenas `intellicare-core` e o próprio módulo; **não instala** `intellicare-auth`
- O pacote `intellicare-auth` existe em `intellicare-auth/` na raiz do projeto, mas não é copiado nem instalado no build da imagem

**Procedimento para o desenvolvedor:**

1. **Incluir `intellicare-auth` no build do Donabedian:**
   - No `intellicare-donabedian/Dockerfile`, após instalar `intellicare-core`, adicionar:
     ```dockerfile
     COPY ./intellicare-auth /tmp/intellicare-auth
     RUN pip install --no-cache-dir -e /tmp/intellicare-auth
     ```
   - Ou declarar `intellicare-auth` como dependência no `pyproject.toml` e garantir que o build tenha acesso ao pacote (path local ou PyPI).
2. **Alternativa:** Se a autenticação não for usada em staging, tornar o import condicional (ex.: `try/except` com fallback) — isso exige alteração de código e deve ser avaliado com cuidado.

---

### 2.3. Comunicacao — email-validator is not installed

**Erro completo:**
```
ImportError: email-validator is not installed, run `pip install 'pydantic[email]'`
```

**Causa raiz:**

- O módulo usa `EmailStr` do Pydantic em `comunicacao/channels/email/models.py` (ex.: `recipient: EmailStr`)
- O Pydantic exige o pacote `email-validator` para validar `EmailStr`
- O `pyproject.toml` do comunicacao declara `email-validator = "^2.0.0"`, mas:
  - O `requirements.txt` não inclui `email-validator` nem `pydantic[email]`
  - O `Dockerfile` pode estar usando `requirements.txt` em algum estágio, ou a instalação via `pip install .` pode não estar resolvendo corretamente as dependências no contexto do build

**Procedimento para o desenvolvedor:**

1. **Garantir a dependência no build:**
   - Incluir explicitamente no `intellicare-comunicacao/requirements.txt` (se usado no Docker):
     ```
     email-validator>=2.0.0
     ```
   - Ou `pydantic[email]>=2.0.0`
2. **No `pyproject.toml`:** Confirmar que `email-validator` está em `[tool.poetry.dependencies]` (já está) e que o `Dockerfile` instala via `pip install -e .` **depois** de copiar o código completo.
3. **Reconstruir a imagem** sem cache para garantir instalação atualizada:
   ```bash
   docker-compose -f docker-compose.full.yml build --no-cache comunicacao
   ```

---

## 3. Ordem de Correção Sugerida

1. **Oswaldo** — Ajuste de URL no `.env` (rápido).
2. **Comunicacao** — Inclusão de `email-validator` no fluxo de instalação e rebuild.
3. **Donabedian** — Inclusão de `intellicare-auth` no `Dockerfile` e rebuild.

---

## 4. Checklist para o Desenvolvedor

- [ ] **Oswaldo:** Alterar `INTELLICARE_OSWALDO_DATABASE_URL` em `.env.homologacao` de `postgresql+asyncpg://` para `postgresql+psycopg://` (ou `postgresql://`)
- [ ] **Donabedian:** Adicionar instalação de `intellicare-auth` no `Dockerfile` (COPY + pip install)
- [ ] **Comunicacao:** Garantir `email-validator` em `requirements.txt` e/ou validar instalação via `pyproject.toml` no build
- [ ] Rebuild das imagens: `docker-compose -f docker-compose.full.yml build --no-cache oswaldo donabedian comunicacao`
- [ ] Redeploy e validação com smoke tests

---

## 5. Referências

- SQLAlchemy asyncpg: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.asyncpg
- MissingGreenlet: https://sqlalche.me/e/20/xd2s
- Pydantic EmailStr: https://docs.pydantic.dev/latest/concepts/types/#emailstr
- `intellicare-oswaldo/oswaldo/datastore/fhir_datastore.py` — usa `create_engine` (sync)
- `intellicare-donabedian/Dockerfile` — não instala intellicare-auth
- `intellicare-comunicacao/comunicacao/channels/email/models.py` — usa `EmailStr`
