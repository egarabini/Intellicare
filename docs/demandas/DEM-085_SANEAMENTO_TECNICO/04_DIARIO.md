# Diário de Bordo — DEM-085: Saneamento Técnico

## 2026-05-16
- **Auditoria Git:** Sincronizado o tracking contra remotos efetuados com `git pull --rebase`. O diretório `estudos/` foi encapsulado via `.gitignore` mantendo isolamento do ambiente principal.
- **Conector Local (Redis):** O dispatcher sofria de problemas de auth local atrelado aos caracteres `#` do enviroment de production `intellicare_dev_password`. Variáveis codificadas criadas `REDIS_PASSWORD_URLENC` que emularam o parsing sem falhas.
- **Tipagens Estritas de Entidades (`clinical_notes.encounter_id`):** Construído bloco de SQL `LPAD(TO_HEX(x), 32, '0')` validando downgrades seguros em bases não tipadas para a migração Universal `UUID`.
- **Testes Resilientes (Cuidado):** Ajustados esquemas de DTO Unitários onde a validação interna utilizava dummy field `full_name`. Testes agora invocam unicamente via `name` na extração de assert.
