CREATE SCHEMA IF NOT EXISTS platform;

CREATE TABLE IF NOT EXISTS platform.pessoa (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo VARCHAR(10) NOT NULL CHECK (tipo IN ('FISICA', 'JURIDICA')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS platform.pessoa_fisica (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pessoa_id UUID NOT NULL UNIQUE REFERENCES platform.pessoa(id) ON DELETE CASCADE,
    nome_completo VARCHAR(255) NOT NULL,
    cpf VARCHAR(11),
    data_nascimento DATE,
    genero VARCHAR(20),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_pessoa_fisica_cpf
    ON platform.pessoa_fisica(cpf)
    WHERE cpf IS NOT NULL;

CREATE TABLE IF NOT EXISTS platform.pessoa_juridica (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pessoa_id UUID NOT NULL UNIQUE REFERENCES platform.pessoa(id) ON DELETE CASCADE,
    razao_social VARCHAR(255) NOT NULL,
    nome_fantasia VARCHAR(255),
    cnpj VARCHAR(14),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_pessoa_juridica_cnpj
    ON platform.pessoa_juridica(cnpj)
    WHERE cnpj IS NOT NULL;

CREATE TABLE IF NOT EXISTS platform.pessoa_contato (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pessoa_id UUID NOT NULL REFERENCES platform.pessoa(id) ON DELETE CASCADE,
    tipo_contato VARCHAR(20) NOT NULL CHECK (tipo_contato IN ('TELEFONE', 'EMAIL', 'ENDERECO')),
    valor TEXT NOT NULL,
    subtipo VARCHAR(50),
    principal BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (pessoa_id, tipo_contato, valor)
);

CREATE TABLE IF NOT EXISTS platform.pessoa_estabelecimento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pessoa_id UUID NOT NULL REFERENCES platform.pessoa(id) ON DELETE CASCADE,
    tenant_slug VARCHAR(100) NOT NULL,
    data_vinculo TIMESTAMP NOT NULL DEFAULT NOW(),
    data_desvinculo TIMESTAMP,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (pessoa_id, tenant_slug)
);

CREATE INDEX IF NOT EXISTS idx_pessoa_estabelecimento_tenant
    ON platform.pessoa_estabelecimento(tenant_slug)
    WHERE ativo = TRUE;
