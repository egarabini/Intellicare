# ADR-003 — MinIO: Storage Massivo de Exames Médicos

**Status:** `PROPOSTO` — aguarda gatilho de implementação
**Data:** 2026-03-21
**Autor:** Eduardo (ARQUITETO)
**Referência:** ADR-001 (Executor Matrix) — MinIO é infraestrutura `Worker` (serviço stateful puro, sem lógica de negócio)

---

## Contexto

Hoje o IntelliCare V3 armazena documentos clínicos de duas formas:

- **Banco de dados PostgreSQL** — notas SOAP/FREE (Florence), prescrições (Oswaldo), dados estruturados de jornadas (CarePlanner)
- **WeasyPrint em tempo real** — PDFs gerados on-demand (`GET /encontros/{id}/report.pdf`) e servidos diretamente via resposta HTTP

Esse modelo é suficiente enquanto o volume de arquivos binários é baixo. O problema surge quando a plataforma precisar lidar com:

- **Exames de imagem** — laudos em PDF, radiografias DICOM, ecocardiogramas
- **Anexos de jornada** — documentos enviados por pacientes via WhatsApp/Portal
- **PDFs clínicos persistidos** — ao invés de gerados on-demand, armazenados para histórico
- **Arquivos FHIR** — bundles JSON/XML grandes para integração com outros sistemas

Guardar binários grandes no PostgreSQL (via `bytea`) é um antipadrão: infla o banco, degrada vacuum, impede streaming eficiente e torna backups desproporcionalmente pesados.

---

## Decisão

Adotar **MinIO** como camada de object storage S3-compatible quando o volume de arquivos binários justificar a adição de um serviço dedicado. MinIO roda como um único container Docker, expõe API 100% compatível com AWS S3, e pode ser adicionado ao `docker-compose.yml` sem alterar nenhuma lógica de negócio existente — apenas o destino de escrita/leitura de arquivos.

---

## Alternativas consideradas

### ❌ PostgreSQL `bytea` / `large object`
Funciona para volumes pequenos, mas degrada performance do banco em escala. Backups ficam pesados. Sem streaming nativo. **Rejeitado para arquivos > 1MB recorrentes.**

### ❌ Disco local no container
Arquivos no filesystem do container são perdidos no próximo redeploy. Não suporta múltiplas réplicas. **Rejeitado.**

### ❌ AWS S3 / GCP Storage direto
Cria dependência de vendor e custo variável. Inviável para clínicas com orçamento restrito ou requisitos de soberania de dados (dados médicos no Brasil → LGPD, CFM). **Rejeitado como solução principal.**

### ✅ MinIO self-hosted (escolhida)
S3-compatible, open source Apache 2.0, um único container, < 100MB de imagem, suporta buckets, políticas de acesso, presigned URLs e retenção de objetos. Pode ser migrado para AWS S3 no futuro apenas trocando as variáveis de ambiente — o código Python não muda.

---

## Arquitetura proposta

```
ClinicoUI / PacienteUI / GestorUI
        │
        ▼
[ FastAPI IntelliCare ]
        │
        ├── Dados estruturados → PostgreSQL (como hoje)
        │
        └── Arquivos binários → MinIO
                │
                ├── bucket: exames-{tenant_slug}
                │     ├── dicom/
                │     ├── laudos/
                │     └── eletros/
                │
                ├── bucket: anexos-jornada-{tenant_slug}
                │     └── whatsapp/, portal/
                │
                └── bucket: relatorios-clinicos-{tenant_slug}
                      └── encontros/, jornadas/
```

### Acesso via Presigned URL

O IntelliCare **nunca serve o arquivo binário diretamente** — gera uma URL temporária assinada e redireciona o cliente:

```python
# packages/intellicare-core/intellicare_core/storage.py (futuro)

from minio import Minio
from datetime import timedelta

minio_client = Minio(
    settings.MINIO_ENDPOINT,          # "minio:9000" interno
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False                       # TLS via Traefik externamente
)

def get_presigned_url(bucket: str, object_name: str, expires_minutes: int = 15) -> str:
    return minio_client.presigned_get_object(
        bucket, object_name,
        expires=timedelta(minutes=expires_minutes)
    )

def upload_exam(tenant_slug: str, file_type: str, file_bytes: bytes, filename: str) -> str:
    bucket = f"exames-{tenant_slug}"
    _ensure_bucket(bucket)
    object_name = f"{file_type}/{filename}"
    minio_client.put_object(bucket, object_name, BytesIO(file_bytes), len(file_bytes))
    return object_name
```

### Endpoint FastAPI

```python
# GET /encontros/{encounter_id}/exames/{exam_id}/download
# → Retorna redirect 302 para presigned URL MinIO (15 min TTL)
```

O frontend React nunca vê as credenciais MinIO — apenas a URL temporária.

---

## Container no docker-compose.yml

```yaml
# Adição futura em infra/docker-compose.yml

minio:
  image: minio/minio:latest
  command: server /data --console-address ":9001"
  environment:
    - MINIO_ROOT_USER=${MINIO_ACCESS_KEY}
    - MINIO_ROOT_PASSWORD=${MINIO_SECRET_KEY}
  volumes:
    - minio_data:/data
  ports:
    - "9001:9001"   # Console web (dev/staging apenas — não expor em prod)
  networks: [intellicare-net]
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
    interval: 30s
    timeout: 10s
    retries: 3

volumes:
  minio_data:
```

**Variáveis de ambiente a adicionar ao `.env.example`:**
```
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=intellicare-storage
MINIO_SECRET_KEY=<senha-forte>
MINIO_PUBLIC_URL=https://storage.intellicare.ia.br   # para presigned URLs públicas
```

---

## Isolamento multi-tenant

O IntelliCare usa schema-per-tenant no PostgreSQL. No MinIO, o isolamento é por **bucket com prefixo de tenant**:

- `exames-clinica-alfa` — bucket exclusivo da tenant `clinica-alfa`
- Políticas IAM por bucket (quando necessário multi-usuário MinIO)
- `tenant_slug` vem do `TenantContext` já presente em todos os módulos

Essa convenção evita cross-tenant data leaks sem complexidade adicional.

---

## LGPD e soberania de dados

MinIO self-hosted mantém todos os dados no VPS da clínica (ou em datacenter nacional). Não há transferência para provedores estrangeiros — requisito importante para dados de saúde no Brasil (LGPD art. 33, Resolução CFM 1.821/2007).

A migração futura para AWS S3 (se necessário) é transparente no código: apenas `MINIO_ENDPOINT` muda para `s3.amazonaws.com` e `secure=True`.

---

## Impacto nos módulos existentes

| Módulo | Hoje | Com MinIO |
|--------|------|-----------|
| Florence (PDFs on-demand) | Gerado e devolvido direto | Gerado + salvo no MinIO + presigned URL |
| Oswaldo (futuro: receituário digital) | Não implementado | PDF salvo em `relatorios-clinicos/` |
| CarePlanner (anexos WhatsApp) | Não implementado | Binário salvo em `anexos-jornada/` |
| Portal Paciente (upload exames) | Não implementado | Upload direto via presigned PUT URL |

---

## Gatilho de implementação

**NÃO implementar agora.** MinIO deve ser adicionado quando **qualquer uma** dessas condições for verdadeira:

1. Primeira demanda de upload de exame real (DICOM, laudo PDF, ECG)
2. PDFs clínicos precisarem ser persistidos (auditoria, histórico imutável)
3. Volume de anexos CarePlanner (WhatsApp) gerar pressão no banco PostgreSQL
4. Necessidade de integração FHIR com bundles de imagem

---

## Relação com Módulo Marie (ADR-002)

O MinIO e a Marie são complementares para RAG longitudinal: exames históricos armazenados no MinIO podem ser indexados pela Marie (Dify) para enriquecer o contexto clínico. O flow seria:

```
Exame armazenado no MinIO
    → Marie indexa no Vector DB (Weaviate/pgvector)
    → Oswaldo/Florence consultam Marie com contexto histórico enriquecido
```

---

## Próximos passos (quando o gatilho for acionado)

- [ ] Criar `DEM-070 MinIO — Bootstrap storage + storage.py`
- [ ] Adicionar container `minio` ao `docker-compose.yml`
- [ ] Implementar `packages/intellicare-core/intellicare_core/storage.py`
- [ ] Criar buckets padrão no startup (`seed_storage.py`)
- [ ] Adicionar variáveis `MINIO_*` ao `.env.example` e `.env.staging.example`
- [ ] Primeiro uso: persistir PDFs clínicos do Florence ao invés de gerar on-demand
- [ ] Smoke no staging: upload + presigned URL retorna arquivo correto
