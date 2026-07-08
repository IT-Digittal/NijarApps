"""Roles RBAC editables con permisos por módulo.

Revision ID: 008_roles
Revises: 007_consumo_ia
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_roles"
down_revision: Union[str, None] = "007_consumo_ia"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(50), nullable=False),
        sa.Column("display", sa.String(120), nullable=False),
        sa.Column("descripcion", sa.String(255)),
        sa.Column("permisos", postgresql.ARRAY(sa.String())),
        sa.Column("es_sistema", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_roles_slug", "roles", ["slug"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_roles_slug", table_name="roles")
    op.drop_table("roles")
