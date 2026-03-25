# DEM-088 — Especificação Técnica

## Migration 024

```sql
-- db/tenant_migrations/024_professionals_pessoa_id.sql
ALTER TABLE professionals
  ADD COLUMN IF NOT EXISTS pessoa_id UUID;

-- Sem NOT NULL, sem FK física — igual ao padrão DEM-084/ADR-004
-- FK lógica: pessoa_id referencia platform.pessoa_fisica(id)
-- Nullable: profissionais cadastrados antes desta migration mantêm NULL
```

## Integração no backend

### Localização

```
modules/cuidado/
  service.py          ← create_professional(), update_professional() — SQL direto
  schemas.py          ← ProfessionalCreate, ProfessionalUpdate (Pydantic)
  router.py           ← endpoints POST /cuidado/professionals
```

> ⚠️ **Gotcha descoberto durante implementação:** a spec indicava `modules/clinico/professionals/`. O módulo real é `modules/cuidado/`. Não existe submódulo `professionals/` separado — o serviço usa `service.py` monolítico com SQL direto, padrão do projeto.

### Padrão implementado (DEM-088 real)

```python
# modules/cuidado/service.py — create_professional()
# Padrão: PessoaFisicaIn como wrapper — idêntico ao DEM-084
async def create_professional(db, ctx, data):
    pessoa_id = None
    if data.cpf:
        cpf_digits = re.sub(r'\D', '', data.cpf)
        pessoa = await find_or_create_by_cpf(PessoaFisicaIn(
            cpf=cpf_digits,
            nome_completo=data.nome,   # campo real mapeado
            tenant_id=ctx.tenant_id
        ))
        pessoa_id = pessoa.id

    # SQL direto — sem ORM
    await db.execute(text("""
        INSERT INTO professionals (..., pessoa_id)
        VALUES (..., :pessoa_id)
    """), {..., "pessoa_id": pessoa_id})
```

> **Nota de implementação:** `find_or_create_by_cpf()` recebe `PessoaFisicaIn` (Pydantic), não `platform_db` raw. O módulo identity gerencia internamente sua própria conexão à platform. Essa é a interface correta — não expor `platform_db` como Depends externo quando `find_or_create_by_cpf()` já encapsula o acesso.

### Endpoints afetados

- `POST /clinico/professionals` — criação com pessoa_id
- `PUT /clinico/professionals/{id}` — atualização: se CPF foi adicionado/alterado, reconciliar pessoa_id

---

## Testes

```python
# test_professional_identity.py

def test_create_professional_with_cpf_links_pessoa():
    """Criar profissional com CPF → pessoa_id preenchido"""

def test_create_professional_without_cpf_ok():
    """Criar profissional sem CPF → pessoa_id NULL (sem erro)"""

def test_create_same_cpf_two_tenants_same_pessoa_id():
    """Mesmo CPF em 2 tenants → mesmo pessoa_id (idempotência platform)"""

def test_update_professional_adds_cpf_links_pessoa():
    """Profissional sem CPF → UPDATE com CPF → pessoa_id preenchido"""

def test_professional_pessoa_id_foreign_logical():
    """pessoa_id é UUID válido em platform.pessoa_fisica"""
```

Total esperado: 5 testes (espelha DEM-084 com 7 — profissional tem escopo ligeiramente menor)

---

## O que NÃO entra nesta DEM

- Backfill de profissionais existentes sem CPF — fora de escopo
- UI de busca por `pessoa_id` — não há mudança visual
- Endpoint de consulta consolidada por `pessoa_id` — escopo ADR-004 futuro
