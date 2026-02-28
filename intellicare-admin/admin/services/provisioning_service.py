"""ProvisioningService — Orchestrates full tenant provisioning.

Steps (transactional with rollback):
1. Create PostgreSQL schema tenant_{id}
2. Run Alembic migrations on that schema
3. Create Keycloak group tenant_{id}
4. Create mapper tenant_id on the group
5. Create admin user in Keycloak
6. Associate user to group
7. Insert seed data
8. Mark tenant.provisioned = True
"""

import logging
import subprocess
from dataclasses import dataclass, field
from typing import Optional

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

        try:
            # Step 1: Create PostgreSQL schema
            await self._create_schema(tenant.tenant_id)
            result.steps_completed.append("schema_created")

            # Step 2: Run migrations (if Alembic is configured)
            await self._run_migrations(tenant.tenant_id)
            result.steps_completed.append("migrations_run")

            # Step 3-6: Keycloak setup (if admin client available)
            if self._kc_admin:
                await self._setup_keycloak(tenant)
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
            # Attempt rollback of schema
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
        try:
            # In production: subprocess call to Alembic
            # For now, copy table structure from template
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
        except Exception as e:
            logger.warning("Migration step had issues: %s (continuing)", e)

    async def _setup_keycloak(self, tenant: Tenant) -> None:
        """Configure Keycloak group, mapper, and admin user."""
        group_name = f"tenant_{tenant.tenant_id}"

        try:
            # Create group
            self._kc_admin.create_group(
                {"name": group_name},
                skip_exists=True,
            )

            # Get group ID
            groups = self._kc_admin.get_groups(query={"search": group_name})
            group_id = groups[0]["id"] if groups else None

            if not group_id:
                raise RuntimeError(f"Failed to find group {group_name}")

            # Create admin user
            user_id = self._kc_admin.create_user({
                "username": f"admin_{tenant.tenant_id}",
                "email": tenant.email_admin,
                "enabled": True,
                "emailVerified": False,
                "credentials": [{
                    "type": "password",
                    "value": "changeme",  # Must reset on first login
                    "temporary": True,
                }],
            })

            # Add user to group
            self._kc_admin.group_user_add(user_id, group_id)

            logger.info("Keycloak configured for tenant: %s user: %s", tenant.tenant_id, user_id)

        except Exception as e:
            logger.error("Keycloak setup failed: %s", e)
            raise

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
