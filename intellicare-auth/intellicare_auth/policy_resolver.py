"""PolicyResolver — resolve an EffectiveAccessPolicy from a decoded JWT payload.

Extracts user_id (sub), tenant_id, and SMART scopes from the JWT then delegates
composition to PolicyBuilder.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PolicyResolver:
    """Resolve AccessPolicy from a Keycloak JWT payload.

    Requires:
        - JWT payload dict (as returned by KeycloakClient.validate_token)
        - A configured PolicyBuilder (from intellicare_core.access)
    """

    def __init__(self, policy_builder: Any) -> None:
        """
        Args:
            policy_builder: An instance of ``intellicare_core.access.PolicyBuilder``.
        """
        self._builder = policy_builder

    def extract_user_id(self, jwt_payload: dict[str, Any]) -> str:
        """Extract user ID from JWT (Keycloak 'sub' claim)."""
        return jwt_payload.get("sub", "anonymous")

    def extract_tenant_id(self, jwt_payload: dict[str, Any], request_tenant: Optional[str] = None) -> str:
        """Extract tenant ID — from request header (preferred) or JWT claim."""
        if request_tenant:
            return request_tenant
        # Keycloak custom claim (configured in token mapper)
        return jwt_payload.get("tenant_id") or jwt_payload.get("tenantId") or "default"

    def extract_smart_scopes(self, jwt_payload: dict[str, Any]) -> Optional[str]:
        """Extract SMART-on-FHIR scopes from JWT 'scope' claim."""
        scope = jwt_payload.get("scope", "")
        if not scope:
            return None
        # Filter to SMART scope tokens (patient/*, user/*, system/*)
        smart_tokens = [
            t for t in scope.split()
            if t.startswith(("patient/", "user/", "system/"))
        ]
        return " ".join(smart_tokens) if smart_tokens else None

    async def resolve(
        self,
        jwt_payload: dict[str, Any],
        request_tenant: Optional[str] = None,
    ) -> Any:
        """Build and return an EffectiveAccessPolicy for the JWT user.

        Returns an EffectiveAccessPolicy (from intellicare_core.access).
        Returns an empty/unauthenticated policy if an error occurs.
        """
        try:
            user_id = self.extract_user_id(jwt_payload)
            tenant_id = self.extract_tenant_id(jwt_payload, request_tenant)
            smart_scopes = self.extract_smart_scopes(jwt_payload)

            policy = await self._builder.build_effective_policy(
                tenant_id=tenant_id,
                user_id=user_id,
                smart_scopes=smart_scopes,
            )
            logger.debug(
                "policy_resolver.resolved user=%s tenant=%s admin=%s rules=%d",
                user_id,
                tenant_id,
                policy.is_admin,
                len(policy.rules),
            )
            return policy

        except Exception as exc:
            logger.warning("policy_resolver.error %s — returning empty policy", exc)
            try:
                from intellicare_core.access.models import EffectiveAccessPolicy  # noqa: PLC0415
                return EffectiveAccessPolicy()
            except ImportError:
                return None
