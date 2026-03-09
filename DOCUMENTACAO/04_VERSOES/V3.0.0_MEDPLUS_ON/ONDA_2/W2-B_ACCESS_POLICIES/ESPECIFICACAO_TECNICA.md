# 🔧 W2-B — Especificação Técnica: FHIR Access Policies

## 1. Arquitetura

```
intellicare-core/
├── intellicare_core/
│   ├── access/                        # [NOVO] Package de Access Policies
│   │   ├── __init__.py
│   │   ├── models.py                  # AccessPolicy, TenantMembership models
│   │   ├── policy_builder.py          # Composição de policies por membership
│   │   ├── policy_evaluator.py        # Avaliação de policy contra recurso
│   │   ├── field_filter.py            # Filtro de campos (readonly, hidden)
│   │   ├── compartment.py             # Compartment-based scoping
│   │   └── smart_scopes.py            # SMART scope → policy translation

intellicare-auth/
├── intellicare_auth/
│   ├── access_middleware.py           # [NOVO] Middleware de Access Policy
│   └── policy_resolver.py            # [NOVO] Resolve policy do JWT
```

## 2. Modelos de Dados

```sql
CREATE TABLE access_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    resource_rules JSONB NOT NULL,        -- Array de ResourceRule
    compartment_ref TEXT,                  -- "Organization/setor-a"
    ip_access_rules JSONB,                -- Array de {cidr, action}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tenant_membership_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    user_id TEXT NOT NULL,                 -- Keycloak user ID
    access_policy_id UUID REFERENCES access_policies(id),
    parameters JSONB,                      -- {"profile": "Practitioner/123"}
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, user_id, access_policy_id)
);
```

## 3. Componentes

### 3.1 Policy Builder (`policy_builder.py`)

```python
class PolicyBuilder:
    """Compõe uma AccessPolicy efetiva a partir de múltiplas policies do membership."""
    
    async def build_effective_policy(
        self, tenant_id: str, user_id: str, smart_scopes: Optional[str] = None
    ) -> EffectiveAccessPolicy:
        memberships = await self._get_memberships(tenant_id, user_id)
        rules = []
        for membership in memberships:
            policy = await self._load_policy(membership.access_policy_id)
            parameterized = self._apply_parameters(policy, membership.parameters)
            rules.extend(parameterized.resource_rules)
        
        effective = EffectiveAccessPolicy(rules=rules)
        
        if smart_scopes:
            effective = apply_smart_scopes(effective, smart_scopes)
        
        return effective
```

### 3.2 Policy Evaluator (`policy_evaluator.py`)

```python
class PolicyEvaluator:
    """Avalia se uma operação é permitida pela policy."""
    
    def can_access(
        self,
        policy: EffectiveAccessPolicy,
        resource_type: str,
        interaction: str,           # search, read, create, update, delete
        resource: Optional[dict] = None,  # Para criteria matching
    ) -> bool:
        rule = self._find_matching_rule(policy, resource_type)
        if not rule:
            return False
        
        if rule.readonly and interaction in ("create", "update", "delete"):
            return False
        
        if rule.interaction and interaction not in rule.interaction:
            return False
        
        if rule.criteria and resource:
            if not self._matches_criteria(resource, rule.criteria):
                return False
        
        return True
    
    def filter_fields(
        self,
        policy: EffectiveAccessPolicy,
        resource_type: str,
        resource: dict,
    ) -> dict:
        """Remove hidden fields e marca readonly fields."""
        rule = self._find_matching_rule(policy, resource_type)
        if not rule:
            return {}
        
        filtered = dict(resource)
        for field in rule.hidden_fields or []:
            filtered.pop(field, None)
        
        return filtered
```

### 3.3 Access Middleware (`access_middleware.py`)

```python
class AccessPolicyMiddleware:
    """Middleware FastAPI que aplica Access Policies."""
    
    async def __call__(self, request: Request, call_next):
        tenant_id = get_tenant_from_request(request)
        user_id = get_user_from_jwt(request)
        smart_scopes = get_smart_scopes(request)
        
        policy = await self.policy_builder.build_effective_policy(
            tenant_id, user_id, smart_scopes
        )
        
        request.state.access_policy = policy
        response = await call_next(request)
        return response
```

### 3.4 Integração nos Módulos

```python
# Em qualquer endpoint FHIR do Grahame:
@router.get("/fhir/{resource_type}/{id}")
async def read_resource(resource_type: str, id: str, request: Request):
    policy = request.state.access_policy
    
    if not evaluator.can_access(policy, resource_type, "read"):
        raise HTTPException(403, "Access denied")
    
    resource = await repo.read(resource_type, id)
    
    # Aplicar criteria (resource-level)
    if not evaluator.can_access(policy, resource_type, "read", resource):
        raise HTTPException(403, "Access denied by criteria")
    
    # Filtrar campos hidden
    filtered = evaluator.filter_fields(policy, resource_type, resource)
    return filtered
```

## 4. Plano de Implementação

### Sprint 1 (7 dias)
- **Dia 1-2:** Models + migrations + CRUD API de AccessPolicy
- **Dia 3-4:** PolicyBuilder (composição + parametrização)
- **Dia 5-6:** PolicyEvaluator (interaction check + criteria matching)
- **Dia 7:** FieldFilter (hidden + readonly) + testes

### Sprint 2 (7 dias)
- **Dia 8-9:** AccessPolicyMiddleware + integração com JWT
- **Dia 10-11:** Compartment scoping
- **Dia 12:** SMART scopes (basic support)
- **Dia 13:** Integração no Grahame (CRUD endpoints)
- **Dia 14:** Testes e2e + documentação + merge

## 5. Critérios de Aceite

1. ✅ 5 policies exemplo funcionais (médico, enfermeiro, recepcionista, admin, sistema)
2. ✅ Field-level control (hidden + readonly) comprovado
3. ✅ Criteria-based access com parametrização
4. ✅ Compartment scoping funcional
5. ✅ Integração com Keycloak JWT
6. ✅ Multi-tenancy isolado
7. ✅ Cobertura de testes ≥ 85%
