
import logging
import re
from contextlib import contextmanager
from typing import Any
from sqlalchemy import text

logger = logging.getLogger(__name__)
_SCHEMA_NAME_PATTERN = re.compile(r"^(tenant_[a-z0-9_]+|public|platform)$")

@contextmanager
def get_tenant_conn(engine: Any, ctx: Any = None):
    with engine.begin() as conn:
        if ctx and hasattr(ctx, "tenant_schema") and ctx.tenant_id != "default":
            schema = ctx.tenant_schema
            if _SCHEMA_NAME_PATTERN.match(schema):
                conn.execute(text(f"SET search_path TO {schema}, public"))
            else:
                logger.warning(f"Invalid schema name {schema}, fallback to default search_path")
        yield conn
