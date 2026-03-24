---
tipo: diario
demanda: DEM-085
autor: DEV-1
data: 2026-05-16
---

# Diário de Bordo — DEM-085 (Saneamento Técnico)

## Execução:

1. **Auditoria Git**: 
   Verificamos que o histórico de commits do `main` encontrava-se propriamente up-to-date. Não houve detecção de commit solto real. O diretório indesejado de contexto local `estudos/` não versionado foi blindado adicionando-o dentro de `.gitignore`. Gravamos o reporte `AUDITORIA_GIT_2026_05_16.md`.
2. **Redis CarePlanner e Marie**:
   Ficou explícito que o container `intellicare-service` falhava no startup no staging não pelas queries do compose si cruzarem, mas pela quebra literal do parser de string de conexões do python `redis://` devido ao fato do `REDIS_PASSWORD` conter `#` no STAGING (`IC_Staging#Redis2025`). Para sanear para sempre a URL truncation (o que reportava "invalid username or password"), injetamos nas declarações de `docker-compose.yml` e nos perfis `.env.staging` o bypass seguro `REDIS_PASSWORD_URLENC` via *fallback* interpolado nativo e atualizamos o override de `redis_pubsub.py` para invocar urllib `quote()` por padrão se a env faltasse. Reiniciamos os contêineres e obteve-se êxito, destravando o service worker e os índices de migration locais do DB.
3. **Migration 023 (UUID - clinical_notes)**:
   Percebeu-se a disforia do backend SQL apontando a chave estrangeira `encounter_id` em BIGINT dentro da tabela `clinical_notes`, sendo que `encounters` exigia UUID genérico de string de 32 hexs. Projetou-se a `023_fix_clinical_notes_encounter_id.sql`, orquestrando `ALTER TABLE ... USING LPAD TO_HEX(...)` num fluxo seguro que adicionou nova col, converteu em batch, e comutou os rótulos apagando a coluna arcaica limpamente. Relocalizou-se o índex associado sem bloquear as constraints globalmente.
4. **Paciente Response Pytest Fix**:
   Detectamos uma incompatibilidade semântica de kwargs na instânciação simulada pela regressão entre `test_patient_response` e a interface `PatientResponse` do módulo Cuidado. O field `full_name` passava onde apenas a chave string `name` devia existir. Ajustado injetando a chave exata para alinhar com Pydantic v2 do Backend. Evaporou as quedas do pipeline do módulo Cuidado. 

## PR e Finalização Próxima
Os passos validados garantem encerramento destas quatro dívidas isoladas sem efeitos prejudiciais na stack cruzada. O ambiente e staging estão aptos e alinhados.
