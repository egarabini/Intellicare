"""REST API for FHIR Access Policies — CRUD + TenantMembership management."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from grahame.services.access_policy_service import AccessPolicyService

router = APIRouter(tags=["Access Policies"])


def _get_svc(request: Request) -> AccessPolicyService:
    session = request.state.db
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    return AccessPolicyService(session, tenant_id)


# ── AccessPolicy CRUD ──────────────────────────────────────────────────────


@router.post("/fhir/AccessPolicy", status_code=201)
async def create_access_policy(body: dict, request: Request):
    """Create a new AccessPolicy."""
    svc = _get_svc(request)
    policy = await svc.create(body)
    return {
        "resourceType": "AccessPolicy",
        "id": policy.id,
        "name": policy.name,
        "description": policy.description,
        "resourceRules": policy.resource_rules,
        "compartmentRef": policy.compartment_ref,
    }


@router.get("/fhir/AccessPolicy")
async def list_access_policies(request: Request, limit: int = 50, offset: int = 0):
    """List all AccessPolicies for the tenant."""
    svc = _get_svc(request)
    policies = await svc.list(limit=limit, offset=offset)
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(policies),
        "entry": [
            {
                "resource": {
                    "resourceType": "AccessPolicy",
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "resourceRules": p.resource_rules,
                    "compartmentRef": p.compartment_ref,
                }
            }
            for p in policies
        ],
    }


@router.get("/fhir/AccessPolicy/{policy_id}")
async def get_access_policy(policy_id: str, request: Request):
    """Get an AccessPolicy by ID."""
    svc = _get_svc(request)
    policy = await svc.get(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"AccessPolicy/{policy_id} not found")
    return {
        "resourceType": "AccessPolicy",
        "id": policy.id,
        "name": policy.name,
        "description": policy.description,
        "resourceRules": policy.resource_rules,
        "compartmentRef": policy.compartment_ref,
        "ipAccessRules": policy.ip_access_rules,
    }


@router.put("/fhir/AccessPolicy/{policy_id}")
async def update_access_policy(policy_id: str, body: dict, request: Request):
    """Update an AccessPolicy."""
    svc = _get_svc(request)
    policy = await svc.update(policy_id, body)
    if policy is None:
        raise HTTPException(status_code=404, detail=f"AccessPolicy/{policy_id} not found")
    return {
        "resourceType": "AccessPolicy",
        "id": policy.id,
        "name": policy.name,
        "description": policy.description,
        "resourceRules": policy.resource_rules,
        "compartmentRef": policy.compartment_ref,
    }


@router.delete("/fhir/AccessPolicy/{policy_id}", status_code=204)
async def delete_access_policy(policy_id: str, request: Request):
    """Delete an AccessPolicy."""
    svc = _get_svc(request)
    ok = await svc.delete(policy_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"AccessPolicy/{policy_id} not found")


# ── TenantMembership ──────────────────────────────────────────────────────


@router.post("/fhir/AccessPolicy/{policy_id}/assign", status_code=201)
async def assign_policy_to_user(policy_id: str, body: dict, request: Request):
    """Assign an AccessPolicy to a user.

    Body: {userId, parameters?, isAdmin?}
    """
    user_id = body.get("userId")
    if not user_id:
        raise HTTPException(status_code=422, detail="userId is required")

    svc = _get_svc(request)
    membership = await svc.assign_policy(
        user_id=user_id,
        policy_id=policy_id,
        parameters=body.get("parameters"),
        is_admin=body.get("isAdmin", False),
    )
    return {
        "resourceType": "TenantMembership",
        "id": membership.id,
        "userId": membership.user_id,
        "accessPolicyId": membership.access_policy_id,
        "parameters": membership.parameters,
        "isAdmin": membership.is_admin,
    }


@router.get("/fhir/AccessPolicy/memberships/{user_id}")
async def get_user_memberships(user_id: str, request: Request):
    """Get all AccessPolicy memberships for a user."""
    svc = _get_svc(request)
    memberships = await svc.get_memberships(user_id)
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(memberships),
        "entry": [
            {
                "resource": {
                    "resourceType": "TenantMembership",
                    "id": m.id,
                    "userId": m.user_id,
                    "accessPolicyId": m.access_policy_id,
                    "parameters": m.parameters,
                    "isAdmin": m.is_admin,
                }
            }
            for m in memberships
        ],
    }


@router.delete("/fhir/AccessPolicy/memberships/entry/{membership_id}", status_code=204)
async def remove_membership(membership_id: str, request: Request):
    """Remove a TenantMembership."""
    svc = _get_svc(request)
    ok = await svc.remove_membership(membership_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Membership/{membership_id} not found")
