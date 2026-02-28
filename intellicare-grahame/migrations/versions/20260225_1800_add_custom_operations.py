"""Add custom operations registry and audit tables.

Revision ID: 20260225_1800
Revises: 20260225_1200
Create Date: 2026-02-25 18:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260225_1800"
down_revision: Union[str, None] = "20260225_1200"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "custom_operations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("op_type", sa.String(length=16), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("handler_type", sa.String(length=16), nullable=False),
        sa.Column("handler_config", sa.JSON(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", "resource_type", name="uq_custom_operations_tenant_name_resource"),
    )
    op.create_index(op.f("ix_custom_operations_name"), "custom_operations", ["name"], unique=False)
    op.create_index(op.f("ix_custom_operations_tenant_id"), "custom_operations", ["tenant_id"], unique=False)

    op.create_table(
        "custom_operation_audit",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=128), nullable=False),
        sa.Column("operation_id", sa.String(length=36), nullable=False),
        sa.Column("operation_name", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("http_status_code", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requester", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_custom_operation_audit_operation_id"), "custom_operation_audit", ["operation_id"], unique=False)
    op.create_index(op.f("ix_custom_operation_audit_tenant_id"), "custom_operation_audit", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_custom_operation_audit_tenant_id"), table_name="custom_operation_audit")
    op.drop_index(op.f("ix_custom_operation_audit_operation_id"), table_name="custom_operation_audit")
    op.drop_table("custom_operation_audit")

    op.drop_index(op.f("ix_custom_operations_tenant_id"), table_name="custom_operations")
    op.drop_index(op.f("ix_custom_operations_name"), table_name="custom_operations")
    op.drop_table("custom_operations")
