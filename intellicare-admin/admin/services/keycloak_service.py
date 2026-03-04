import logging
from keycloak import KeycloakAdmin

logger = logging.getLogger(__name__)

class KeycloakService:
    def __init__(self, server_url: str, username: str, password: str, realm_name: str, target_realm: str):
        self.target_realm = target_realm
        self.admin = KeycloakAdmin(
            server_url=server_url,
            username=username,
            password=password,
            realm_name=realm_name,
            user_realm_name=realm_name,
            verify=False
        )
        # Ensure we operate on the correct realm
        self.admin.realm_name = target_realm

    async def create_estabelecimento_group(self, estabelecimento_id: str, nome: str) -> str:
        """Cria grupo para o estabelecimento no Keycloak"""
        group_name = f"estabelecimento_{estabelecimento_id}"
        logger.info(f"Creating group: {group_name}")
        
        group_id = self.admin.create_group(
            payload={
                "name": group_name,
                "attributes": {
                    "estabelecimento_id": [estabelecimento_id],
                    "estabelecimento_nome": [nome],
                    "tipo": ["estabelecimento"]
                }
            }
        )
        return group_id

    async def create_gestor_user(
        self,
        estabelecimento_id: str,
        nome: str,
        email: str,
        password: str
    ) -> str:
        """Cria usuário gestor (PLATFORM_GESTOR) do estabelecimento"""
        logger.info(f"Creating user gestor: {email} for estabelecimento: {estabelecimento_id}")
        
        parts = nome.split(" ")
        first_name = parts[0]
        last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        user_id = self.admin.create_user(
            payload={
                "username": email,
                "email": email,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": True,
                "groups": [f"estabelecimento_{estabelecimento_id}"],
                "credentials": [{
                    "type": "password",
                    "value": password,
                    "temporary": True
                }],
                "attributes": {
                    "estabelecimento_id": [estabelecimento_id],
                    "role": ["PLATFORM_GESTOR"]
                }
            }
        )

        # Buscar IDs para assign role
        platform_gestor_role = self.admin.get_realm_role("PLATFORM_GESTOR")
        
        if platform_gestor_role:
             self.admin.assign_realm_roles(
                user_id=user_id,
                roles=[platform_gestor_role]
            )

        return user_id

    async def revoke_estabelecimento_tokens(self, estabelecimento_id: str):
        """Revoga todos os tokens do estabelecimento (suspensão)"""
        group_name = f"estabelecimento_{estabelecimento_id}"
        group_id = self.admin.get_group_by_path(f"/{group_name}")
        
        if not group_id:
            return
            
        members = self.admin.get_group_members(group_id['id'])

        for member in members:
            self.admin.logout(user_id=member["id"])
