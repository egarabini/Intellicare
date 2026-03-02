"""ProvisioningService — Orchestrates full tenant provisioning.

Steps (transactional with rollback):
1. Create PostgreSQL schema tenant_{id}
2. Run Alembic migrations on that schema
3. Create Keycloak group tenant_{id}
4. Ensure mapper tenant_id for portal tokens
5. Create admin user in Keycloak
6. Associate user to group
7. Insert seed data
8. Mark tenant.provisioned = True
"""

import logging
import secrets
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from admin.models.tenant import Tenant

logger = logging.getLogger(__name__)


@dataclass
class ProvisioningResult:
    """Result of a provisioning attempt."""
    success: bool
    tenant_id: str
    steps_completed: list[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class KeycloakProvisioningContext:
    """Tracks KC resources for rollback safety."""
    group_id: Optional[str] = None
    user_id: Optional[str] = None
    group_created: bool = False
    user_created: bool = False


class ProvisioningService:
    """Orchestrates the full provisioning of a new tenant."""

    def __init__(
        self,
        session: AsyncSession,
        keycloak_admin=None,
        keycloak_target_realm: str = "bemcuidar",
        migration_script_path: str = "./migrations",
    ):
        self._session = session
        self._kc_admin = keycloak_admin
        self._kc_realm = keycloak_target_realm
        self._migration_path = migration_script_path

    async def provision(self, tenant: Tenant) -> ProvisioningResult:
        """Run all provisioning steps. Rolls back on failure."""
        result = ProvisioningResult(success=False, tenant_id=tenant.tenant_id)
        kc_context = KeycloakProvisioningContext()

        try:
            # Step 1: Create PostgreSQL schema
            await self._create_schema(tenant.tenant_id)
            result.steps_completed.append("schema_created")

            # Step 2: Run migrations (if Alembic is configured)
            await self._run_migrations(tenant.tenant_id)
            result.steps_completed.append("migrations_run")

            # Step 3-6: Keycloak setup (if admin client available)
            if self._kc_admin:
                kc_context = await self._setup_keycloak(tenant)
                result.steps_completed.append("keycloak_configured")
            else:
                logger.warning(
                    "Keycloak admin not configured — skipping KC provisioning for %s",
                    tenant.tenant_id,
                )
                result.steps_completed.append("keycloak_skipped")

            # Step 7: Seed data
            await self._insert_seed_data(tenant.tenant_id)
            result.steps_completed.append("seed_data_inserted")

            # Step 8: Mark as provisioned
            tenant.provisioned = True
            await self._session.flush()
            result.steps_completed.append("tenant_marked_provisioned")

            result.success = True
            logger.info("Tenant provisioned successfully: %s", tenant.tenant_id)

        except Exception as e:
            result.error = str(e)
            logger.error(
                "Provisioning failed for tenant %s at step %s: %s",
                tenant.tenant_id,
                result.steps_completed[-1] if result.steps_completed else "start",
                e,
            )
            await self._rollback_keycloak(kc_context)
            await self._rollback_schema(tenant.tenant_id)

        return result

    # ── Internal Steps ────────────────────────────────────────

    async def _create_schema(self, tenant_id: str) -> None:
        """Create a PostgreSQL schema for the tenant."""
        schema_name = f"tenant_{tenant_id}"
        # Validate schema name (prevent SQL injection)
        if not all(c.isalnum() or c == "_" for c in schema_name):
            raise ValueError(f"Invalid schema name: {schema_name}")

        await self._session.execute(
            text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
        )
        logger.info("Schema created: %s", schema_name)

    async def _run_migrations(self, tenant_id: str) -> None:
        """Run Alembic migrations for the tenant schema.

        This calls the provision_tenant_schema.py script from F0.
        """
        # Using the provisioning script from intellicare-core
        # In production: run Alembic targeted to schema.
        # Current implementation copies table structure from tenant_template.
        schema_name = f"tenant_{tenant_id}"
        template_tables = await self._session.execute(
            text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'tenant_template'
                ORDER BY table_name
            """)
        )
        tables = [row[0] for row in template_tables.fetchall()]

        for table in tables:
            await self._session.execute(
                text(f'''
                    CREATE TABLE IF NOT EXISTS "{schema_name}"."{table}"
                    (LIKE "tenant_template"."{table}" INCLUDING ALL)
                ''')
            )

        logger.info("Migrations applied for schema: %s (%d tables)", schema_name, len(tables))

    async def _setup_keycloak(self, tenant: Tenant) -> KeycloakProvisioningContext:
        """Configure Keycloak group, mapper, and admin user."""
        context = KeycloakProvisioningContext()
        group_name = f"tenant_{tenant.tenant_id}"

        existing_group = self._find_group_by_name(group_name)
        if existing_group:
            context.group_id = existing_group["id"]
        else:
            created_group = self._kc_admin.create_group(
                {
                    "name": group_name,
                    "attributes": {
                        "tenant_id": [tenant.tenant_id],
                        "tenant_nome": [tenant.nome_fantasia],
                    },
                },
                skip_exists=True,
            )
            context.group_id = (
                created_group
                if isinstance(created_group, str)
                else created_group.get("id") if isinstance(created_group, dict) else None
            )
            if not context.group_id:
                created = self._find_group_by_name(group_name)
                context.group_id = created["id"] if created else None
            context.group_created = True

        if not context.group_id:
            raise RuntimeError(f"Failed to create/find group {group_name}")

        await self._ensure_tenant_mapper()

        username = f"admin_{tenant.tenant_id}"
        user = self._find_user_by_username(username)
        if user:
            context.user_id = user["id"]
            self._kc_admin.update_user(
                user_id=context.user_id,
                payload={
                    "email": tenant.email_admin,
                    "enabled": True,
                    "attributes": {
                        "tenant_id": [tenant.tenant_id],
                        "role": ["ADMIN"],
                        "nome": [f"Admin {tenant.nome_fantasia}"],
                        "tipo": ["ADMIN_LOCAL"],
                    },
                    "requiredActions": ["UPDATE_PASSWORD", "VERIFY_EMAIL"],
                },
            )
        else:
            temp_password = secrets.token_urlsafe(16)
            user_payload = {
                "username": username,
                "email": tenant.email_admin,
                "enabled": True,
                "emailVerified": False,
                "attributes": {
                    "tenant_id": [tenant.tenant_id],
                    "role": ["ADMIN"],
                    "nome": [f"Admin {tenant.nome_fantasia}"],
                    "tipo": ["ADMIN_LOCAL"],
                },
                "credentials": [
                    {
                        "type": "password",
                        "value": temp_password,
                        "temporary": True,
                    }
                ],
                "requiredActions": ["UPDATE_PASSWORD", "VERIFY_EMAIL"],
            }
            try:
                created_user = self._kc_admin.create_user(user_payload, exist_ok=False)
            except TypeError:
                created_user = self._kc_admin.create_user(user_payload)
            context.user_id = (
                created_user
                if isinstance(created_user, str)
                else created_user.get("id") if isinstance(created_user, dict) else None
            )
            if not context.user_id:
                created = self._find_user_by_username(username)
                context.user_id = created["id"] if created else None
            context.user_created = True

        if not context.user_id:
            raise RuntimeError(f"Failed to create/find user {username}")

        try:
            self._kc_admin.group_user_add(context.user_id, context.group_id)
        except Exception as exc:
            if "409" not in str(exc):
                raise
        self._send_password_reset(context.user_id)

        logger.info(
            "Keycloak configured for tenant=%s group=%s user=%s",
            tenant.tenant_id,
            context.group_id,
            context.user_id,
        )
        return context

    async def _ensure_tenant_mapper(self) -> None:
        """Ensure intellicare-portal has tenant_id mapper from user attribute."""
        client_id = self._kc_admin.get_client_id("intellicare-portal")
        if not client_id:
            logger.warning("Client intellicare-portal not found; skipping tenant mapper setup")
            return

        existing = self._get_client_mappers(client_id)
        if any(m.get("name") == "tenant_id" for m in existing):
            return

        mapper_payload = {
            "name": "tenant_id",
            "protocol": "openid-connect",
            "protocolMapper": "oidc-usermodel-attribute-mapper",
            "consentRequired": False,
            "config": {
                "user.attribute": "tenant_id",
                "claim.name": "tenant_id",
                "jsonType.label": "String",
                "id.token.claim": "true",
                "access.token.claim": "true",
                "userinfo.token.claim": "true",
            },
        }
        self._kc_admin.add_mapper_to_client(client_id, mapper_payload)

    def _get_client_mappers(self, client_id: str) -> list[dict[str, Any]]:
        """Read client mappers with compatibility across python-keycloak versions."""
        if hasattr(self._kc_admin, "get_mappers_from_client"):
            return self._kc_admin.get_mappers_from_client(client_id) or []
        if hasattr(self._kc_admin, "get_client_protocol_mappers"):
            return self._kc_admin.get_client_protocol_mappers(client_id) or []
        logger.warning("Could not inspect client mappers; mapper deduplication unavailable")
        return []

    def _find_group_by_name(self, group_name: str) -> Optional[dict[str, Any]]:
        groups = self._kc_admin.get_groups(query={"search": group_name})
        return next((g for g in groups if g.get("name") == group_name), None)

    def _find_user_by_username(self, username: str) -> Optional[dict[str, Any]]:
        users = self._kc_admin.get_users({"username": username, "exact": True})
        return users[0] if users else None

    def _send_password_reset(self, user_id: str) -> None:
        """Trigger Keycloak required action email without failing provisioning."""
        try:
            self._kc_admin.send_update_account(
                user_id=user_id,
                payload=["UPDATE_PASSWORD"],
            )
        except Exception as exc:
            logger.warning("Could not send UPDATE_PASSWORD email for user %s: %s", user_id, exc)

    async def _insert_seed_data(self, tenant_id: str) -> None:
        """Insert initial configuration data into the tenant schema."""
        schema_name = f"tenant_{tenant_id}"
        # Seed data is specific to each module's needs
        # For now, just log
        logger.info("Seed data would be inserted into %s", schema_name)

    async def _rollback_schema(self, tenant_id: str) -> None:
        """Attempt to rollback a failed provisioning."""
        schema_name = f"tenant_{tenant_id}"
        try:
            await self._session.execute(
                text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
            )
            logger.info("Rollback: dropped schema %s", schema_name)
        except Exception as e:
            logger.error("Rollback failed for schema %s: %s", schema_name, e)

    async def _rollback_keycloak(self, context: KeycloakProvisioningContext) -> None:
        """Rollback only resources that were created by this execution."""
        if not self._kc_admin:
            return

        if context.user_created and context.user_id:
            try:
                self._kc_admin.delete_user(context.user_id)
                logger.info("Rollback: deleted Keycloak user %s", context.user_id)
            except Exception as exc:
                logger.error("Rollback failed deleting Keycloak user %s: %s", context.user_id, exc)

        if context.group_created and context.group_id:
            try:
                self._kc_admin.delete_group(context.group_id)
                logger.info("Rollback: deleted Keycloak group %s", context.group_id)
            except Exception as exc:
                logger.error("Rollback failed deleting Keycloak group %s: %s", context.group_id, exc)
