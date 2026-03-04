import logging
from uuid import UUID

from admin.db import async_session_maker
from admin.services.provisioning import ProvisioningService
from admin.services.tenant_service import TenantRepository
# mock:
# from admin.services.keycloak_service import KeycloakService

logger = logging.getLogger(__name__)

async def process_provisioning_queue(tenant_id: UUID, gestor_data: dict, tenant_nome: str):
    logger.info(f"Iniciando worker de provisionamento para o tenant {tenant_id}")
    
    async with async_session_maker() as session:
        tenant_repo = TenantRepository(session)
        prov_service = ProvisioningService(session)
        
        try:
            # 1. Cria schema
            success = await prov_service.create_tenant_schema(tenant_id)
            if not success:
                raise Exception("Falha ao criar schema PostgreSQL")

            # 2. Keycloak integration
            # admin = KeycloakService(...)
            # group_id = await admin.create_estabelecimento_group(str(tenant_id), tenant_nome)
            # gestor_pwd = generate_password()
            # if gestor_data and gestor_data.get("email"):
            #    user_id = await admin.create_gestor_user(str(tenant_id), gestor_data["nome"], gestor_data["email"], gestor_pwd)
            #    await send_credentials_email(tenant_nome, gestor_data["email"], gestor_pwd)

            # 3. Atualizar status do tenant
            tenant = await tenant_repo.get_tenant(tenant_id)
            tenant.status = "active"
            await session.commit()
            logger.info(f"Provisionamento concluído para {tenant_id}")

        except Exception as e:
            logger.error(f"Erro no provisionamento do tenant {tenant_id}: {e}")
            await rollback_provisioning(tenant_id, session)

async def rollback_provisioning(tenant_id: UUID, session):
    logger.warning(f"Executando rollback para {tenant_id}")
    prov_service = ProvisioningService(session)
    await prov_service.drop_tenant_schema(tenant_id)
    # Também deveria remover grupos e usuarios do KC...
