"""Métricas de publicidad: impresiones y toques diarios por anunciante.

Revision ID: 013_metricas_publicidad
Revises: 012_empresas_anunciantes
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013_metricas_publicidad"
down_revision: Union[str, None] = "012_empresas_anunciantes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "metricas_publicidad",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "empresa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("empresas_anunciantes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fecha", sa.Date, nullable=False),
        sa.Column("impresiones", sa.Integer, nullable=False, server_default="0"),
        sa.Column("toques", sa.Integer, nullable=False, server_default="0"),
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
        sa.UniqueConstraint("empresa_id", "fecha", name="uq_metricas_publicidad_dia"),
    )
    op.create_index("ix_metricas_publicidad_fecha", "metricas_publicidad", ["fecha"])
    op.create_index("ix_metricas_publicidad_empresa", "metricas_publicidad", ["empresa_id"])


def downgrade() -> None:
    op.drop_index("ix_metricas_publicidad_empresa", table_name="metricas_publicidad")
    op.drop_index("ix_metricas_publicidad_fecha", table_name="metricas_publicidad")
    op.drop_table("metricas_publicidad")
