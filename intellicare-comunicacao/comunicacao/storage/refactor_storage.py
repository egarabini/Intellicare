import os
import re

storage_dir = r"c:\Users\egara\INTELLICARE\intellicare-comunicacao\comunicacao\storage"

# Create a tenant_utils.py file to hold the synchronous context manager
tenant_utils_code = """
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
"""

with open(os.path.join(storage_dir, "tenant_utils.py"), "w", encoding="utf-8") as f:
    f.write(tenant_utils_code)


for fname in os.listdir(storage_dir):
    if fname.endswith(".py") and fname not in ("tenant_utils.py", "__init__.py"):
        filepath = os.path.join(storage_dir, fname)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        changed = False

        if "with get_tenant_conn(self.engine, ctx) as conn:" in content:
            changed = True
            
            # Make sure tenant_utils is imported
            if "from comunicacao.storage.tenant_utils import get_tenant_conn" not in content:
                content = "from comunicacao.storage.tenant_utils import get_tenant_conn\n" + content
            
            # Inject ctx=None into method signatures that don't have it yet 
            # (since we didn't add ctx to template_repository and rule_repository yet)
            
            methods_to_patch = [
                r"def save_intent(self, intent: CommunicationIntentRecord) -> None:",
                r"def get_intent(self, intent_id: str) -> CommunicationIntentRecord | None:",
                r"def list_intents(self) -> list[CommunicationIntentRecord]:",
                r"def update_intent(self, intent: CommunicationIntentRecord) -> None:",
                r"def append_delivery(self, delivery: DeliveryResultRecord) -> None:",
                r"def get_deliveries(self, intent_id: str) -> list[DeliveryResultRecord]:",
                r"def find_by_source_event(self, source_module: str, source_event_id: str) -> CommunicationIntentRecord | None:",
                
                # template_repository.py
                r"def get(self, template_id: str) -> TemplateRecord | None:",
                r"def list_templates(self) -> list[TemplateRecord]:",
                r"def save(self, template: TemplateRecord) -> None:",
                r"def delete(self, template_id: str) -> bool:",
                
                # rule_repository.py
                r"def save_rule(self, rule: RoutingRule) -> None:",
                r"def get_rule(self, rule_id: str) -> RoutingRule | None:",
                r"def list_rules(self) -> list[RoutingRule]:",
                r"def delete_rule(self, rule_id: str) -> bool:",
                r"def get_active_rules_by_priority(self) -> list[RoutingRule]:",

                # repository.py PatientRoomRepository
                r"def upsert_link(self, patient_id: str, room_id: str) -> None:",
                r"def get_room_id(self, patient_id: str) -> str | None:",
                r"def list_links(self, limit: int, offset: int) -> list[dict[str, str]]:",
                r"def delete_link(self, patient_id: str) -> bool:",
            ]
            
            for m in methods_to_patch:
                m_with_ctx = m.replace(r")", r", ctx: Any = None)").replace("None: None", "None") # hacky regex fix
                # manual fix for the typed return
                m_with_ctx = m_with_ctx.replace(", ctx: Any = None) -> None:", ", ctx: Any = None) -> None:")
                m_with_ctx = re.sub(r") ->", r", ctx: Any = None) ->", m)
                content = re.sub(m, m_with_ctx, content)
            
            # Now replace the actual connection statement
            content = content.replace("with get_tenant_conn(self.engine, ctx) as conn:", "with get_tenant_conn(self.engine, ctx) as conn:")

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Updated {fname}")

