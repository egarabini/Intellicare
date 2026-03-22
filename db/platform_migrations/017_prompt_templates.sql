-- DEM-073: Prompt versioning para Florence e Oswaldo.
-- Tabelas de plataforma vivem em public neste repositório.

CREATE TABLE IF NOT EXISTS public.prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_key VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL CHECK (version > 0),
    content TEXT NOT NULL,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by TEXT,
    created_by_email TEXT,
    activated_at TIMESTAMPTZ,
    activated_by TEXT,
    activated_by_email TEXT,
    CONSTRAINT uq_prompt_templates_key_version UNIQUE (prompt_key, version)
);

CREATE INDEX IF NOT EXISTS idx_prompt_templates_key_version
    ON public.prompt_templates (prompt_key, version DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_prompt_templates_active_per_key
    ON public.prompt_templates (prompt_key)
    WHERE is_active = true;

INSERT INTO public.prompt_templates
    (prompt_key, version, content, notes, is_active, activated_at, activated_by, activated_by_email)
VALUES
    (
        'florence_soap',
        1,
        'Você é um assistente clínico. Com base nas informações abaixo, preencha os campos SOAP de forma objetiva e concisa, em português, para uma nota clínica médica.',
        'Seed fallback inicial Florence SOAP',
        true,
        now(),
        'migration-017',
        'system@intellicare'
    ),
    (
        'florence_free_text',
        1,
        'Motivo da consulta: {chief_complaint}\nMotivo do agendamento: {appointment_reason}\nNotas anteriores relevantes: {recent_notes}\n\nResponda APENAS com um JSON no formato:\n{{"S": "...", "O": "...", "A": "...", "P": "..."}}',
        'Seed fallback inicial Florence texto livre',
        true,
        now(),
        'migration-017',
        'system@intellicare'
    ),
    (
        'oswaldo_cid10',
        1,
        'Você é um assistente clínico. Com base nas informações abaixo, sugira:\n1. O CID-10 mais provável (código e descrição curta)',
        'Seed fallback inicial Oswaldo CID10',
        true,
        now(),
        'migration-017',
        'system@intellicare'
    ),
    (
        'oswaldo_prescription',
        1,
        '2. Uma prescrição inicial com até 3 itens (medicamento, posologia, duração)\n\nQueixa principal: {chief_complaint}\nDiagnósticos anteriores: {recent_diagnoses}\nMedicamentos em uso: {current_medications}\n\nResponda APENAS com JSON no formato:\n{{\n  "cid10_code": "X00",\n  "cid10_desc": "Descrição curta",\n  "items": [\n    {{"drug": "Nome 500mg", "posology": "1 comp 8/8h", "duration": "5 dias"}}\n  ]\n}}',
        'Seed fallback inicial Oswaldo prescrição',
        true,
        now(),
        'migration-017',
        'system@intellicare'
    )
ON CONFLICT (prompt_key, version) DO NOTHING;
