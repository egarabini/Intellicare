"""Utilitarios de tenant para o modulo de comunicacao.

Fornece helper de conexao com schema isolation para multi-tenancy.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any


@contextmanager
def get_tenant_conn(engine: Any, ctx: Any = None):
    """Context manager para conexao com schema de tenant.

    Configura o search_path do PostgreSQL para o schema do tenant
    antes de executar qualquer query.

    Args:
        engine: SQLAlchemy engine
        ctx: TenantContext com schema_name ou tenant_schema
    """
    schema = "public"
    if ctx is not None:
        if hasattr(ctx, "tenant_schema"):
            schema = ctx.tenant_schema
        elif hasattr(ctx, "schema_name"):
            schema = ctx.schema_name

    with engine.begin() as conn:
        if "postgresql" in str(engine.url):
            from sqlalchemy import text
            conn.execute(text(f"SET search_path TO {schema}, public"))
        yield conn
