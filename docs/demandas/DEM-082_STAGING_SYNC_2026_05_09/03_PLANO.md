---
tipo: plano-execucao
demanda: DEM-082
titulo: Staging Sync 2026-05-09
status: em-execucao
dev: DEV-1
criado: 2026-03-22
---

# DEM-082 — Plano de Execução

## Estimativa

Tempo estimado: ~3h | Complexidade: média-alta

Mais complexo que syncs anteriores por três razões: ativação do Marie (primeira vez com `true`), validação visual do PDF assinado, e migrations em schema de tenant. Reservar tempo extra para o workflow Florence no Dify.

---

## Pré-condições

- [ ] DEM-079 mergeado e push confirmado
- [ ] DEM-080 mergeado e push confirmado
- [ ] DEM-081 mergeado e push confirmado
- [ ] `SERVER_ENCRYPTION_KEY` gerada e registrada em local seguro
- [ ] Workflow `cid10_rag` ainda funcionando no Dify (DEM-075)

---

## Ordem de execução

### Bloco 1 — Pull, rebuild e migrations (30min)
1. `git pull origin main` — confirmar 3 commits
2. Adicionar `SERVER_ENCRYPTION_KEY` e `MARIE_ENABLED=true` ao `.env.staging`
3. `docker compose build api gestorui clinicoui && docker compose up -d`
4. Aplicar migrations 019 e 020 (ver `02_TECNICA.md` §2)

### Bloco 2 — Workflow Florence no Dify (30min)
5. Acessar Dify web → criar workflow `florence_soap_rag` (ver DEM-079 `02_TECNICA.md`)
6. Publicar → `docker compose restart api`
7. Verificar log: `docker compose logs api | grep marie` — sem erros de conexão

### Bloco 3 — Certificado de teste e smokes (60min)
8. Gerar certificado autoassinado (ver `02_TECNICA.md` §4)
9. Upload via API — confirmar `subject_name` retornado
10. Smoke Florence com Marie (ver `02_TECNICA.md` §5)
11. Smoke receituário assinado — abrir PDF no Chrome, verificar painel assinatura
12. Smoke KPIs — confirmar JSON com todos os campos
13. Smoke manual GestorUI `/indicadores`

### Bloco 4 — Testes e fechamento (30min)
14. `pytest test_florence_marie.py test_assinatura_digital.py test_clinical_kpis.py -v`
15. Todos passando → staging aprovado

---

## Gotcha — Marie pode não estar respondendo após `MARIE_ENABLED=true`

Se a API Key do Dify foi gerada no sprint anterior com TTL, pode ter expirado. Verificar:
```bash
curl -s -H "Authorization: Bearer $MARIE_API_KEY" \
  http://staging:5001/v1/parameters | jq '.result'
# Se "unauthorized": gerar nova API Key no Dify e atualizar .env.staging
```

---

## Gotcha — Migrations 019/020 são de tenant, não de platform

Diferente das migrations 017/018 (que ficam em `db/platform_migrations/`), estas ficam em `db/tenant_migrations/` e devem ser aplicadas **em cada schema de tenant**. Para o staging com schema `demo`:

```bash
# Substituir {schema} por "demo" nos scripts antes de aplicar
sed 's/{schema}/demo/g' db/tenant_migrations/019_professional_certificates.sql | \
  docker compose exec -T db psql -U postgres -d intellicare
```

---

## Gotcha — PDF assinado com cert autoassinado

Chrome mostrará "A identidade do signatário não pôde ser verificada" — isso é esperado (certificado não emitido por AC ICP-Brasil). O importante é que a assinatura aparece no painel e os dados do signatário estão corretos (CN, data). Para produção, o médico usa certificado de AC credenciada.

---

## Entrega

```
chore(staging): sync 2026-05-09 — Marie ativo, PDF assinado, KPIs, migrations 019/020
```
Hash → enviar ao ARQUITETO após `git push origin HEAD:main` confirmado.
