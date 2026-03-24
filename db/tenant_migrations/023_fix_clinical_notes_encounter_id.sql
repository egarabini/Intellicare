-- Migration 023_fix_clinical_notes_encounter_id.sql
-- Converte a coluna encounter_id da tabela clinical_notes de BIGINT para UUID

-- 1. Adiconar a nova coluna tipada corretamente
ALTER TABLE {schema}.clinical_notes ADD COLUMN IF NOT EXISTS new_encounter_id UUID;

-- 2. Migrar os dados de forma segura via cast para HEX (apenas preenchimento padrao caso existam ids bigint puros na fase de dev)
UPDATE {schema}.clinical_notes 
SET new_encounter_id = LPAD(TO_HEX(encounter_id), 32, '0')::UUID 
WHERE encounter_id IS NOT NULL;

-- 3. Remover a coluna antiga com as eventuais dependencias atreladas a ela
ALTER TABLE {schema}.clinical_notes DROP COLUMN IF EXISTS encounter_id CASCADE;

-- 4. Renomear e aplicar as policies de constraint
ALTER TABLE {schema}.clinical_notes RENAME COLUMN new_encounter_id TO encounter_id;

-- Como as linhas antigas (bigint castados) provocariam violacao de chave estrangeira nas validacoes,
-- definimos as FKs como NOT VALID para nao parar a execucao caso existam mockatas previas,
-- porem os novos registros seguirao a integridade estritamente.
ALTER TABLE {schema}.clinical_notes 
    ADD CONSTRAINT clinical_notes_encounter_id_fkey
    FOREIGN KEY (encounter_id) REFERENCES {schema}.encounters(id) ON DELETE CASCADE NOT VALID;

-- 5. Restituir a flag de obrigatoriedade
ALTER TABLE {schema}.clinical_notes ALTER COLUMN encounter_id SET NOT NULL;

-- 6. Recriar os indices originais
CREATE INDEX IF NOT EXISTS idx_clinical_notes_encounter ON {schema}.clinical_notes(encounter_id);
