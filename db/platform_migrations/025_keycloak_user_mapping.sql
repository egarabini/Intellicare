-- 025_keycloak_user_mapping.sql
-- Mapeia Keycloak sub (JWT subject) -> platform.pessoa.id
-- Separa a identidade civil (CPF em pessoa_fisica) da identidade de autenticação (sub Keycloak)
-- Permite que um mesmo sub acesse múltiplos realms no futuro sem duplicação de pessoa

CREATE TABLE IF NOT EXISTS platform.keycloak_user_mapping (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    keycloak_sub VARCHAR(255) NOT NULL,
    realm        VARCHAR(100) NOT NULL DEFAULT 'intellicare',
    pessoa_id    UUID         NOT NULL REFERENCES platform.pessoa(id) ON DELETE CASCADE,
    created_at   TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP    NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_keycloak_sub_realm UNIQUE (keycloak_sub, realm)
);

CREATE INDEX IF NOT EXISTS idx_keycloak_user_mapping_sub
    ON platform.keycloak_user_mapping(keycloak_sub);

CREATE INDEX IF NOT EXISTS idx_keycloak_user_mapping_pessoa_id
    ON platform.keycloak_user_mapping(pessoa_id);
