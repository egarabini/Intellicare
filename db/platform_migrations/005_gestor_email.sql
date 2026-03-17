-- DEM-037: adicionar gestor_email à tabela de tenants
ALTER TABLE public.tenants
    ADD COLUMN IF NOT EXISTS gestor_email TEXT;
