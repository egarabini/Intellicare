"""Seed das 6 roles padrão e settings iniciais do tenant.

Executado pelo ProvisioningService (intellicare-admin) ao criar um tenant,
ou manualmente via:

    python -m gestor.scripts.seed_roles
"""

import asyncio
import sys
from datetime import UTC, datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from intellicare_core.tenant import TenantAwareSessionFactory, TenantContext

from gestor.config import settings
from gestor.models.role import Role
from gestor.models.settings import TenantSetting

DEFAULT_ROLES = [
    {
        "name": "admin_local",
        "display_name": "Administrador Local",
        "is_system": True,
        "permissions": ["*"],
    },
    {
        "name": "gestor_setor",
        "display_name": "Gestor de Setor",
        "is_system": True,
        "permissions": ["gestor.usuarios", "gestor.setores"],
    },
    {
        "name": "medico",
        "display_name": "Médico",
        "is_system": True,
        "permissions": [
            "oswaldo.*",
            "florence.ver_resultados",
            "geralda.*",
            "comunicacao.enviar_email",
        ],
    },
    {
        "name": "enfermeiro",
        "display_name": "Enfermeiro(a)",
        "is_system": True,
        "permissions": ["florence.*", "geralda.ver", "comunicacao.enviar_email"],
    },
    {
        "name": "tecnico",
        "display_name": "Técnico",
        "is_system": True,
        "permissions": ["florence.ver_resultados", "zilda.ver"],
    },
    {
        "name": "recepcao",
        "display_name": "Recepção",
        "is_system": True,
        "permissions": ["zilda.buscar", "comunicacao.ver"],
    },
]

DEFAULT_SETTINGS = [
    {"category": "branding", "key": "nome_exibicao", "value": "", "value_type": "string"},
    {"category": "branding", "key": "fuso_horario", "value": "America/Sao_Paulo", "value_type": "string"},
    {"category": "branding", "key": "logo_url", "value": "", "value_type": "string"},
    {"category": "comunicacao", "key": "sms_provider", "value": "twilio", "value_type": "string"},
    {"category": "comunicacao", "key": "email_smtp_host", "value": "", "value_type": "string"},
    {"category": "comunicacao", "key": "email_smtp_port", "value": "587", "value_type": "number"},
    {"category": "modulos", "key": "oswaldo_alerta_drc_estadio", "value": "3", "value_type": "number"},
]


async def seed_tenant(session: AsyncSession) -> None:
    """Insere roles e settings padrão se ainda não existirem."""
    seeded_roles = 0
    for role_data in DEFAULT_ROLES:
        existing = await session.execute(
            select(Role).where(Role.name == role_data["name"])
        )
        if existing.scalar_one_or_none() is None:
            role = Role(**role_data)
            session.add(role)
            seeded_roles += 1

    seeded_settings = 0
    for setting_data in DEFAULT_SETTINGS:
        existing = await session.execute(
            select(TenantSetting).where(TenantSetting.key == setting_data["key"])
        )
        if existing.scalar_one_or_none() is None:
            setting = TenantSetting(**setting_data)
            session.add(setting)
            seeded_settings += 1

    await session.commit()
    print(f"✅ Seed completo: {seeded_roles} roles + {seeded_settings} settings inseridos")


async def main(tenant_id: str = "default") -> None:
    if not config.database_url:
        print("❌ INTELLICARE_DATABASE_URL não configurada")
        sys.exit(1)

    factory = TenantAwareSessionFactory(settings.DATABASE_URL)
    ctx = TenantContext(
        tenant_id=tenant_id,
        tenant_schema=f"tenant_{tenant_id}" if tenant_id != "default" else "public",
        user_id="system",
    )
    session = await factory.get_session(ctx)
    try:
        await seed_tenant(session)
    finally:
        await session.close()
        await factory.dispose()


if __name__ == "__main__":
    tenant = sys.argv[1] if len(sys.argv) > 1 else "default"
    asyncio.run(main(tenant))
