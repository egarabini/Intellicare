"""PolicyResolver — resolve an EffectiveAccessPolicy from a decoded JWT payload.

Checks Redis cache first. If cache missed, queries the database for the 
TenantMembershipPolicy and AccessPolicy. Replaces `%profile` and other
parameters before returning the effective policy.
"""

from __future__ import annotations

import logging
import json
from typing import Any, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class PolicyResolver:
    """Resolve AccessPolicy from the database and Redis cache."""

    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self.session = session
        self.redis = redis

    def extract_user_id(self, jwt_payload: dict[str, Any]) -> str:
        """Extract user ID from JWT (Keycloak 'sub' claim)."""
        return jwt_payload.get("sub", "anonymous")

    def extract_tenant_id(self, jwt_payload: dict[str, Any], request_tenant: Optional[str] = None) -> str:
        """Extract tenant ID — from request header (preferred) or JWT claim."""
        if request_tenant:
            return request_tenant
        return jwt_payload.get("tenant_id") or jwt_payload.get("tenantId") or "default"

    def _replace_parameters(self, rules: list, parameters: dict) -> list:
        """Replace placeholders like %profile in the rules criteria."""
        if not parameters or not rules:
            return rules

        rules_str = json.dumps(rules)
        for key, value in parameters.items():
            placeholder = f"%{key}"
            # Ensure safe replacement of strings in JSON
            # In a real scenario, consider AST parsing or proper FHIRPath substitution
            rules_str = rules_str.replace(placeholder, str(value))
        
        return json.loads(rules_str)

    async def resolve(
        self,
        tenant_id: str,
        user_id: str,
    ) -> dict:
        """Build and return an AccessPolicy dictionary.
        
        Follows precedence: Redis -> DB -> Default DenyAll
        """
        cache_key = f"policy:{tenant_id}:{user_id}"

        try:
            # 1. Check Redis Cache
            cached_policy = await self.redis.get(cache_key)
            if cached_policy:
                logger.debug(f"policy_resolver.cache_hit key={cache_key}")
                return json.loads(cached_policy)
                
        except Exception as e:
            logger.warning(f"policy_resolver.redis_error: {e}")

        # 2. Check Database (TenantMembership + AccessPolicy)
        try:
            # Dynamic import to avoid circular dependencies if used inside GRAHAME models
            from intellicare_core.access.models import TenantMembershipRecord, AccessPolicyRecord
            # We assume these models are SQLAlchemy ORM classes despite the `models.py` showing Pydantic initially.
            # In the W2-B spec, they were defined via SQL CREATE TABLE.
            # We will use SQLAlchemy core text or a declarative model if it gets mapped in grahame.

            # Using SQL text to fetch safely without depending on the exact ORM model placement
            from sqlalchemy import text
            
            query = text('''
                SELECT tmp.is_admin, tmp.parameters, ap.resource_rules
                FROM tenant_membership_policies tmp
                LEFT JOIN access_policies ap ON tmp.access_policy_id = ap.id
                WHERE tmp.tenant_id = :tenant_id AND tmp.user_id = :user_id
            ''')
            
            result = await self.session.execute(query, {"tenant_id": tenant_id, "user_id": user_id})
            row = result.fetchone()

            if not row:
                logger.debug(f"policy_resolver.not_found user={user_id} tenant={tenant_id}")
                return {} # Deny All

            is_admin, parameters, resource_rules = row
            
            if is_admin:
                policy_dict = {"is_admin": True, "resource_rules": []}
            else:
                rules = resource_rules if resource_rules else []
                # Handle parameter replacement like %profile -> Practitioner/123
                if parameters:
                    rules = self._replace_parameters(rules, parameters)
                
                policy_dict = {"is_admin": False, "resource_rules": rules}

            # 3. Cache the resolved policy for 5 minutes
            try:
                await self.redis.set(cache_key, json.dumps(policy_dict), ex=300)
            except Exception as e:
                logger.warning(f"policy_resolver.redis_set_error: {e}")

            return policy_dict

        except Exception as exc:
            logger.error(f"policy_resolver.db_error {exc} — returning empty policy")
            return {}
