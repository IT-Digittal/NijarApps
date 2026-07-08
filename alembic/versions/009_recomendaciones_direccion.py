"""Estado persistido de las recomendaciones de dirección.

Revision ID: 009_recomendaciones_direccion
Revises: 008_roles
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_recomendaciones_direccion"
down_revision: Union[str, None] = "008_roles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recomendaciones_direccion",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("clave", sa.String(80), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("area", sa.String(80), nullable=False),
        sa.Column("prioridad", sa.String(20), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("comentario", sa.String(500)),
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
    op.create_index(
        "ix_recomendaciones_direccion_clave",
        "recomendaciones_direccion",
        ["clave"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_recomendaciones_direccion_clave", table_name="recomendaciones_direccion")
    op.drop_table("recomendaciones_direccion")
