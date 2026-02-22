"""TenantService — CRUD + business logic for tenant management."""

import re
import math
import logging
from datetime import datetime, timedelta, UTC
from typing import Optional

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from admin.models.tenant import Tenant, TenantModule, generate_slug, validate_cnpj
from admin.models.plan import Plan
from admin.models.audit import GlobalAuditLog
from admin.schemas.tenant_schemas import (
    TenantCreate, TenantUpdate, TenantResponse, TenantListResponse, ModuleUpdate,
)

logger = logging.getLogger(__name__)


class TenantService:
    """Manages tenant lifecycle in the platform schema."""

    def __init__(self, session: AsyncSession, trial_duration_days: int = 30):
        self._session = session
        self._trial_days = trial_duration_days

    # ── CRUD ──────────────────────────────────────────────────

    async def create(self, data: TenantCreate, actor_id: str) -> Tenant:
        """Create a new tenant. Raises ValueError for invalid data."""

        # Validate CNPJ
        if not validate_cnpj(data.cnpj):
            raise ValueError("CNPJ inválido")

        # Check CNPJ uniqueness
        existing = await self._session.execute(
            select(Tenant).where(Tenant.cnpj == data.cnpj)
        )
        if existing.scalar_one_or_none():
            raise ValueError("CNPJ já cadastrado")

        # Generate slug
        slug = generate_slug(data.nome_fantasia)

        # Check slug uniqueness
        existing_slug = await self._session.execute(
            select(Tenant).where(Tenant.tenant_id == slug)
        )
        if existing_slug.scalar_one_or_none():
            # Append number suffix
            slug = f"{slug}_{int(datetime.now(UTC).timestamp()) % 10000}"

        # Resolve plan
        plan = None
        if data.plan_name:
            result = await self._session.execute(
                select(Plan).where(Plan.name == data.plan_name)
            )
            plan = result.scalar_one_or_none()

        # Create tenant
        tenant = Tenant(
            tenant_id=slug,
            nome_fantasia=data.nome_fantasia,
            razao_social=data.razao_social,
            cnpj=data.cnpj,
            email_admin=data.email_admin,
            logo_url=data.logo_url,
            cor_primaria=data.cor_primaria,
            cor_secundaria=data.cor_secundaria,
            dominio_custom=data.dominio_custom,
            plan_id=plan.id if plan else None,
            max_users=plan.max_users if plan else 5,
            max_sms_month=plan.max_sms_month if plan else 100,
            status="trial",
            trial_expires_at=datetime.now(UTC) + timedelta(days=self._trial_days),
        )

        self._session.add(tenant)

        # Create default modules based on plan
        if plan and plan.modules_included:
            for module_name in plan.modules_included:
                module = TenantModule(
                    tenant_id=slug,
                    module_name=module_name,
                    enabled=True,
                )
                self._session.add(module)

        # Audit log
        audit = GlobalAuditLog(
            actor_id=actor_id,
            action="tenant.created",
            resource_type="tenant",
            resource_id=slug,
            target_tenant_id=slug,
            details={"cnpj": data.cnpj, "plan": data.plan_name},
        )
        self._session.add(audit)

        await self._session.flush()
        logger.info("Tenant created: %s (CNPJ: %s)", slug, data.cnpj)
        return tenant

    async def get(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        result = await self._session.execute(
            select(Tenant).where(Tenant.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def list_tenants(
        self,
        page: int = 1,
        size: int = 20,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> TenantListResponse:
        """Paginated tenant listing with optional filters."""
        query = select(Tenant)
        count_query = select(func.count(Tenant.id))

        if status_filter:
            query = query.where(Tenant.status == status_filter)
            count_query = count_query.where(Tenant.status == status_filter)

        if search:
            like = f"%{search}%"
            query = query.where(
                (Tenant.nome_fantasia.ilike(like))
                | (Tenant.cnpj.ilike(like))
                | (Tenant.tenant_id.ilike(like))
            )
            count_query = count_query.where(
                (Tenant.nome_fantasia.ilike(like))
                | (Tenant.cnpj.ilike(like))
                | (Tenant.tenant_id.ilike(like))
            )

        # Count total
        total_result = await self._session.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(Tenant.created_at.desc())
        result = await self._session.execute(query)
        items = result.scalars().all()

        return TenantListResponse(
            items=[TenantResponse.model_validate(t) for t in items],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if size > 0 else 0,
        )

    async def update(self, tenant_id: str, data: TenantUpdate, actor_id: str) -> Optional[Tenant]:
        """Update tenant fields."""
        tenant = await self.get(tenant_id)
        if not tenant:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Handle plan change
        if "plan_name" in update_data:
            plan_name = update_data.pop("plan_name")
            result = await self._session.execute(
                select(Plan).where(Plan.name == plan_name)
            )
            plan = result.scalar_one_or_none()
            if plan:
                tenant.plan_id = plan.id
                tenant.max_users = plan.max_users
                tenant.max_sms_month = plan.max_sms_month

        for key, value in update_data.items():
            setattr(tenant, key, value)

        # Audit
        audit = GlobalAuditLog(
            actor_id=actor_id,
            action="tenant.updated",
            resource_type="tenant",
            resource_id=tenant_id,
            target_tenant_id=tenant_id,
            details={"fields_changed": list(data.model_dump(exclude_unset=True).keys())},
        )
        self._session.add(audit)

        await self._session.flush()
        return tenant

    # ── Status Actions ────────────────────────────────────────

    async def suspend(self, tenant_id: str, reason: str, actor_id: str) -> Optional[Tenant]:
        """Suspend a tenant."""
        tenant = await self.get(tenant_id)
        if not tenant:
            return None

        tenant.status = "suspended"
        tenant.suspended_at = datetime.now(UTC)

        audit = GlobalAuditLog(
            actor_id=actor_id,
            action="tenant.suspended",
            resource_type="tenant",
            resource_id=tenant_id,
            target_tenant_id=tenant_id,
            details={"reason": reason},
        )
        self._session.add(audit)

        await self._session.flush()
        logger.warning("Tenant suspended: %s reason=%s", tenant_id, reason)
        return tenant

    async def activate(self, tenant_id: str, actor_id: str) -> Optional[Tenant]:
        """Reactivate a suspended tenant."""
        tenant = await self.get(tenant_id)
        if not tenant:
            return None

        tenant.status = "active"
        tenant.suspended_at = None

        audit = GlobalAuditLog(
            actor_id=actor_id,
            action="tenant.activated",
            resource_type="tenant",
            resource_id=tenant_id,
            target_tenant_id=tenant_id,
        )
        self._session.add(audit)

        await self._session.flush()
        logger.info("Tenant activated: %s", tenant_id)
        return tenant

    # ── Module Management ─────────────────────────────────────

    async def update_modules(
        self,
        tenant_id: str,
        modules: list[ModuleUpdate],
        actor_id: str,
    ) -> list[TenantModule]:
        """Enable/disable modules for a tenant. Validates against plan."""
        tenant = await self.get(tenant_id)
        if not tenant:
            raise ValueError("Tenant não encontrado")

        # Get plan modules
        allowed_modules = set()
        if tenant.plan:
            allowed_modules = set(tenant.plan.modules_included or [])

        results = []
        for mod in modules:
            # Validate against plan
            if mod.enabled and mod.module_name not in allowed_modules:
                raise ValueError(
                    f"Módulo '{mod.module_name}' não disponível no plano '{tenant.plan.name if tenant.plan else 'nenhum'}'"
                )

            # Find or create
            result = await self._session.execute(
                select(TenantModule).where(
                    TenantModule.tenant_id == tenant_id,
                    TenantModule.module_name == mod.module_name,
                )
            )
            tm = result.scalar_one_or_none()

            if tm:
                tm.enabled = mod.enabled
                if mod.config_json is not None:
                    tm.config_json = mod.config_json
            else:
                tm = TenantModule(
                    tenant_id=tenant_id,
                    module_name=mod.module_name,
                    enabled=mod.enabled,
                    config_json=mod.config_json or {},
                )
                self._session.add(tm)

            results.append(tm)

        # Audit
        audit = GlobalAuditLog(
            actor_id=actor_id,
            action="tenant.modules_updated",
            resource_type="tenant",
            resource_id=tenant_id,
            target_tenant_id=tenant_id,
            details={"modules": [m.model_dump() for m in modules]},
        )
        self._session.add(audit)

        await self._session.flush()
        return results
