from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

class ProvisioningService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tenant_schema(self, tenant_id: UUID) -> bool:
        """Cria schema para o estabelecimento e apenas tabelas base necessárias"""
        schema_name = f"tenant_{str(tenant_id).replace('-', '_')}"
        logger.info(f"Creating schema: {schema_name}")
        
        try:
            # Em PostgreSQL não dá para rodar CREATE SCHEMA via parâmetros bind padrão facilmente,
            # então formatamos a string de query mas com cuidado para SQL Injection (são IDs estáticos).
            await self.session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            
            # Seed Data do Gestor (Fase 3): Roles, Settings, Sectors, Users, etc.
            # Criamos tabelas mínimas necessárias para o Gestor rodar se o Alembic da Fase 0 não criar na hora.
            # Idealmente, o Alembic cuidaria das tabelas, mas inserimos o Seed Data aqui conforme specs F2.
            await self.session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.roles (
                    id UUID PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    display_name VARCHAR(255),
                    is_system BOOLEAN DEFAULT FALSE,
                    permissions JSONB DEFAULT '[]',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))

            await self.session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.settings (
                    id UUID PRIMARY KEY,
                    category VARCHAR(100) NOT NULL,
                    key VARCHAR(255) NOT NULL UNIQUE,
                    value TEXT,
                    value_type VARCHAR(20) DEFAULT 'string',
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_by UUID
                )
            """))

            # Inserir Roles Default
            roles_seed = [
                ("gen_random_uuid()", "'admin_local'", "'Administrador Local'", "TRUE", "'[\"*\"]'::jsonb"),
                ("gen_random_uuid()", "'gestor_setor'", "'Gestor de Setor'", "TRUE", "'[\"gestor.usuarios\", \"gestor.setores\"]'::jsonb"),
                ("gen_random_uuid()", "'medico'", "'Médico'", "TRUE", "'[\"oswaldo.*\", \"florence.ver_resultados\", \"geralda.*\", \"comunicacao.enviar_email\"]'::jsonb"),
                ("gen_random_uuid()", "'enfermeiro'", "'Enfermeiro(a)'", "TRUE", "'[\"florence.*\", \"geralda.ver\", \"comunicacao.enviar_email\"]'::jsonb"),
                ("gen_random_uuid()", "'tecnico'", "'Técnico'", "TRUE", "'[\"florence.ver_resultados\", \"zilda.ver\"]'::jsonb"),
                ("gen_random_uuid()", "'recepcao'", "'Recepção'", "TRUE", "'[\"zilda.buscar\", \"comunicacao.ver\"]'::jsonb")
            ]
            for r_id, name, dname, sys, perms in roles_seed:
                await self.session.execute(text(f"""
                    INSERT INTO {schema_name}.roles (id, name, display_name, is_system, permissions)
                    VALUES ({r_id}, {name}, {dname}, {sys}, {perms})
                    ON CONFLICT (name) DO NOTHING
                """))

            # Inserir Settings Default
            settings_seed = [
                ("'branding'", "'nome_exibicao'", "''", "'string'"),
                ("'branding'", "'fuso_horario'", "'America/Sao_Paulo'", "'string'"),
                ("'comunicacao'", "'sms_provider'", "'twilio'", "'string'"),
                ("'comunicacao'", "'email_smtp_host'", "''", "'string'")
            ]
            for cat, key, val, val_type in settings_seed:
                await self.session.execute(text(f"""
                    INSERT INTO {schema_name}.settings (id, category, key, value, value_type)
                    VALUES (gen_random_uuid(), {cat}, {key}, {val}, {val_type})
                    ON CONFLICT (key) DO NOTHING
                """))

            await self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating schema {schema_name}: {e}")
            await self.session.rollback()
            return False

    async def drop_tenant_schema(self, tenant_id: UUID) -> bool:
        schema_name = f"tenant_{str(tenant_id).replace('-', '_')}"
        try:
            await self.session.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
            await self.session.commit()
            return True
        except Exception as e:
             logger.error(f"Error dropping schema {schema_name}: {e}")
             await self.session.rollback()
             return False
