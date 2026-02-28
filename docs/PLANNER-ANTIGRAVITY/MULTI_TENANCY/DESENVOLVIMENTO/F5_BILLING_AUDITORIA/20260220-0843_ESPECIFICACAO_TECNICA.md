# F5 — Especificação Técnica: Billing + Auditoria Global

> **Módulo:** `intellicare-admin` (expandir) + novo worker  
> **Schema:** `platform` | **Stack:** Python 3.11+, FastAPI, Celery/APScheduler

---

## 1. Modelos ORM Adicionais

### 1.1 — UsageMetric

```python
class UsageMetric(Base):
    __tablename__ = "usage_metrics"
    __table_args__ = {"schema": "platform"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(100), ForeignKey("platform.tenants.tenant_id"), index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Contadores diários
    api_requests = Column(Integer, default=0)
    sms_sent = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    storage_bytes = Column(BigInteger, default=0)
    
    # Por módulo (JSON)
    module_usage = Column(JSON, default={})  # {"zilda": 150, "oswaldo": 80, ...}
    
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    __table_args__ = (
        UniqueConstraint("tenant_id", "date", name="uq_usage_tenant_date"),
        {"schema": "platform"},
    )
```

### 1.2 — Alert

```python
class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = {"schema": "platform"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(100), index=True)
    alert_type = Column(String(50))  # "sms_limit_80", "trial_expiring", "overdue"
    severity = Column(String(20))  # "warning", "critical"
    message = Column(Text)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
```

---

## 2. Serviços

### 2.1 — UsageCollector (Worker)

```python
class UsageCollector:
    """Consome métricas de uso via Redis pub/sub."""
    
    async def consume_usage_event(self, event: dict):
        """
        Cada módulo publica: 
        {tenant_id, module, metric, value, timestamp}
        
        O collector agrega por (tenant, date) e faz UPSERT.
        """
        await self._upsert_daily_metric(
            tenant_id=event["tenant_id"],
            date=date.today(),
            metric=event["metric"],
            increment=event["value"],
        )
```

### 2.2 — BillingService

```python
class BillingService:
    async def generate_monthly_billing(self, period: date):
        """Gera billing para todos os tenants ativos."""
        tenants = await self._get_active_tenants()
        for tenant in tenants:
            usage = await self._get_monthly_usage(tenant.tenant_id, period)
            plan = await self._get_plan(tenant.plan_id)
            
            # Calcular excedentes
            sms_excess = max(0, usage.sms_sent - plan.max_sms_month)
            user_excess = max(0, usage.active_users - plan.max_users)
            
            amount = plan.price_monthly
            amount += sms_excess * Decimal("0.15")
            amount += user_excess * Decimal("29.90")
            
            record = BillingRecord(
                tenant_id=tenant.tenant_id,
                period_start=period.replace(day=1),
                period_end=last_day_of_month(period),
                plan_name=plan.name,
                active_users=usage.active_users,
                sms_sent=usage.sms_sent,
                amount=amount,
                payment_status="pending",
            )
            await self._save(record)
    
    async def check_overdue(self):
        """Job diário: verifica faturas overdue e suspende tenants."""
        overdue = await self._get_overdue_records(days=15)
        for record in overdue:
            if not record.grace_until or date.today() > record.grace_until:
                await self._suspend_tenant(record.tenant_id, reason="billing_overdue")
```

### 2.3 — AlertService

```python
class AlertService:
    async def check_usage_limits(self):
        """Job diário: verifica limites de uso."""
        tenants = await self._get_active_tenants()
        for tenant in tenants:
            usage = await self._get_current_month_usage(tenant.tenant_id)
            plan = await self._get_plan(tenant.plan_id)
            
            # SMS 80%
            if usage.sms_sent >= plan.max_sms_month * 0.8:
                await self._create_alert(tenant.tenant_id, "sms_limit_80", "warning")
            
            # SMS 100%
            if usage.sms_sent >= plan.max_sms_month:
                await self._create_alert(tenant.tenant_id, "sms_limit_100", "critical")
            
            # Trial expirando
            if tenant.status == "trial" and tenant.trial_expires_at:
                days_left = (tenant.trial_expires_at - datetime.now(UTC)).days
                if days_left <= 7:
                    await self._create_alert(tenant.tenant_id, "trial_expiring", "warning")
```

---

## 3. Jobs Agendados

| Job | Frequência | Descrição |
|---|---|---|
| `usage_collector` | Contínuo (Redis consumer) | Agrega métricas de uso em tempo real |
| `check_overdue` | Diário 08:00 | Suspende tenants inadimplentes |
| `check_usage_limits` | Diário 00:30 | Gera alertas de limite |
| `generate_billing` | Mensal dia 1 às 06:00 | Gera faturas do mês anterior |
| `trial_expiration` | Diário 09:00 | Suspende trials expirados |

**Implementação:** APScheduler (embarcado) ou Celery Beat (produção).

---

## 4. Arquivos Novos/Modificados

| Arquivo | Ação | Descrição |
|---|---|---|
| `admin/models/usage.py` | NOVO | UsageMetric, Alert |
| `admin/services/usage_collector.py` | NOVO | Consumer de métricas |
| `admin/services/billing_service.py` | EXPANDIR | Geração e check de overdue |
| `admin/services/alert_service.py` | NOVO | Verificação de limites |
| `admin/api/billing_routes.py` | EXPANDIR | Novos endpoints |
| `admin/api/alert_routes.py` | NOVO | CRUD alertas |
| `admin/workers/scheduler.py` | NOVO | Jobs agendados |

---

## 5. Emissão de Métricas pelos Módulos

Cada módulo deve publicar métricas no Redis ao final de cada request:

```python
# Middleware para publicar métricas (adicionar em cada módulo)
class UsageMetricsMiddleware:
    async def __call__(self, request, call_next):
        response = await call_next(request)
        
        ctx = getattr(request.state, "tenant_context", None)
        if ctx:
            await redis.publish("usage_events", json.dumps({
                "tenant_id": ctx.tenant_id,
                "module": self.module_name,
                "metric": "api_request",
                "value": 1,
                "timestamp": datetime.now(UTC).isoformat(),
            }))
        
        return response
```
