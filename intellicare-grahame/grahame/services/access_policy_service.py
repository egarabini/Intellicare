"""AccessPolicyService — CRUD + composition helpers for FHIR Access Policies."""

from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.models.access_policy import AccessPolicy, TenantMembership


class AccessPolicyService:
    def __init__(self, session: AsyncSession, tenant_id: str) -> None:
        self.session = session
        self.tenant_id = tenant_id

    # ── AccessPolicy CRUD ──────────────────────────────────────────────────

    async def create(self, data: dict) -> AccessPolicy:
        policy = AccessPolicy(
            tenant_id=self.tenant_id,
            name=data["name"],
            description=data.get("description"),
            resource_rules=data.get("resourceRules", data.get("resource_rules", [])),
            compartment_ref=data.get("compartmentRef", data.get("compartment_ref")),
            ip_access_rules=data.get("ipAccessRules", data.get("ip_access_rules")),
        )
        self.session.add(policy)
        await self.session.commit()
        await self.session.refresh(policy)
        return policy

    async def get(self, policy_id: str) -> Optional[AccessPolicy]:
        result = await self.session.execute(
            select(AccessPolicy).where(
                AccessPolicy.id == policy_id,
                AccessPolicy.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list(self, *, limit: int = 50, offset: int = 0) -> list[AccessPolicy]:
        result = await self.session.execute(
            select(AccessPolicy)
            .where(AccessPolicy.tenant_id == self.tenant_id)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update(self, policy_id: str, data: dict) -> Optional[AccessPolicy]:
        policy = await self.get(policy_id)
        if policy is None:
            return None
        if "name" in data:
            policy.name = data["name"]
        if "description" in data:
            policy.description = data["description"]
        if "resourceRules" in data:
            policy.resource_rules = data["resourceRules"]
        elif "resource_rules" in data:
            policy.resource_rules = data["resource_rules"]
        if "compartmentRef" in data or "compartment_ref" in data:
            policy.compartment_ref = data.get("compartmentRef") or data.get("compartment_ref")
        policy.updated_at = datetime.datetime.utcnow()
        await self.session.commit()
        await self.session.refresh(policy)
        return policy

    async def delete(self, policy_id: str) -> bool:
        policy = await self.get(policy_id)
        if policy is None:
            return False
        await self.session.delete(policy)
        await self.session.commit()
        return True

    # ── TenantMembership CRUD ──────────────────────────────────────────────

    async def assign_policy(
        self,
        user_id: str,
        policy_id: Optional[str],
        *,
        parameters: Optional[dict] = None,
        is_admin: bool = False,
    ) -> TenantMembership:
        """Assign an AccessPolicy to a user (upsert by user_id + policy_id)."""
        # Check for existing membership with same (tenant, user, policy)
        result = await self.session.execute(
            select(TenantMembership).where(
                TenantMembership.tenant_id == self.tenant_id,
                TenantMembership.user_id == user_id,
                TenantMembership.access_policy_id == policy_id,
            )
        )
        membership = result.scalar_one_or_none()

        if membership:
            membership.parameters = parameters
            membership.is_admin = is_admin
        else:
            membership = TenantMembership(
                tenant_id=self.tenant_id,
                user_id=user_id,
                access_policy_id=policy_id,
                parameters=parameters,
                is_admin=is_admin,
            )
            self.session.add(membership)

        await self.session.commit()
        await self.session.refresh(membership)
        return membership

    async def get_memberships(self, user_id: str) -> list[TenantMembership]:
        result = await self.session.execute(
            select(TenantMembership).where(
                TenantMembership.tenant_id == self.tenant_id,
                TenantMembership.user_id == user_id,
            )
        )
        return list(result.scalars().all())

    async def remove_membership(self, membership_id: str) -> bool:
        result = await self.session.execute(
            select(TenantMembership).where(
                TenantMembership.id == membership_id,
                TenantMembership.tenant_id == self.tenant_id,
            )
        )
        membership = result.scalar_one_or_none()
        if membership is None:
            return False
        await self.session.delete(membership)
        await self.session.commit()
        return True

    # ── PolicyBuilder callables ────────────────────────────────────────────

    async def fetch_memberships_for_user(
        self, tenant_id: str, user_id: str
    ) -> list:
        """Injectable MembershipFetcher for PolicyBuilder (returns Pydantic records)."""
        try:
            from intellicare_core.access.models import TenantMembershipRecord  # noqa: PLC0415
        except ImportError:
            return []

        result = await self.session.execute(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == user_id,
            )
        )
        rows = list(result.scalars().all())
        return [TenantMembershipRecord.model_validate(r) for r in rows]

    async def fetch_policy_by_id(self, policy_id: str) -> object:
        """Injectable PolicyFetcher for PolicyBuilder (returns Pydantic record or None)."""
        try:
            from intellicare_core.access.models import (  # noqa: PLC0415
                AccessPolicyRecord,
                ResourceRule,
            )
        except ImportError:
            return None

        result = await self.session.execute(
            select(AccessPolicy).where(AccessPolicy.id == policy_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None

        rules = [ResourceRule.model_validate(r) for r in (row.resource_rules or [])]
        return AccessPolicyRecord(
            id=row.id,
            tenant_id=row.tenant_id,
            name=row.name,
            description=row.description,
            resource_rules=rules,
            compartment_ref=row.compartment_ref,
        )
