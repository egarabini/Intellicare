"""Pydantic models for FHIR Access Policies — no SQLAlchemy in core."""

from __future__ import annotations

import datetime
import uuid
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ResourceRule(BaseModel):
    """A single rule granting access to a FHIR resource type.

    Equivalent to one entry in Medplum's AccessPolicy.resource[].
    """

    resource_type: str
    """FHIR resource type, e.g. 'Patient', 'Observation', or '*' for any."""

    interaction: Optional[list[Literal["search", "read", "create", "update", "delete"]]] = None
    """Allowed interactions. None = all interactions allowed (unless readonly=True)."""

    criteria: Optional[str] = None
    """FHIR search criteria for resource-level filtering, e.g. 'Patient?status=active'."""

    readonly: bool = False
    """If True, the entire resource is read-only (no create/update/delete)."""

    readonly_fields: Optional[list[str]] = None
    """Fields that cannot be modified by the user."""

    hidden_fields: Optional[list[str]] = None
    """Fields removed from responses entirely (not visible to the user)."""


class IPAccessRule(BaseModel):
    """IP-based access restriction."""

    cidr: str
    """CIDR notation, e.g. '192.168.1.0/24'."""

    action: Literal["allow", "deny"] = "allow"


class AccessPolicyRecord(BaseModel):
    """A named access policy that can be assigned to users."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    description: Optional[str] = None
    resource_rules: list[ResourceRule] = Field(default_factory=list)
    compartment_ref: Optional[str] = None
    """Organizational compartment, e.g. 'Organization/setor-a'."""

    ip_access_rules: Optional[list[IPAccessRule]] = None
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    updated_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    model_config = {"from_attributes": True}


class TenantMembershipRecord(BaseModel):
    """Assignment of an AccessPolicy to a user within a tenant."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    """Keycloak user ID (sub claim)."""

    access_policy_id: Optional[str] = None
    parameters: Optional[dict[str, Any]] = None
    """Parameter substitutions: {'%profile': 'Practitioner/123'}."""

    is_admin: bool = False
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

    model_config = {"from_attributes": True}


class EffectiveAccessPolicy(BaseModel):
    """Composed access policy after resolving all memberships.

    This is the object injected into request.state.access_policy.
    """

    rules: list[ResourceRule] = Field(default_factory=list)
    is_admin: bool = False
    compartment_ref: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None

    def is_empty(self) -> bool:
        return not self.is_admin and not self.rules
