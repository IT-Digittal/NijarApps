"""Serie histórica mensual de métricas por vertical (interanual real).

Revision ID: 010_historico_verticales
Revises: 009_recomendaciones_direccion
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_historico_verticales"
down_revision: Union[str, None] = "009_recomendaciones_direccion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "metricas_historicas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vertical", sa.String(30), nullable=False),
        sa.Column("indicador", sa.String(60), nullable=False),
        sa.Column("periodo", sa.String(10), nullable=False),
        sa.Column("valor", sa.Float, nullable=False),
        sa.Column("unidad", sa.String(20)),
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
    )
    op.create_index(
        "ux_metricas_hist_vertical_indicador_periodo",
        "metricas_historicas",
        ["vertical", "indicador", "periodo"],
        unique=True,
    )
    op.create_index("ix_metricas_historicas_vertical", "metricas_historicas", ["vertical"])
    op.create_index("ix_metricas_historicas_indicador", "metricas_historicas", ["indicador"])
    op.create_index("ix_metricas_historicas_periodo", "metricas_historicas", ["periodo"])


def downgrade() -> None:
    op.drop_index("ix_metricas_historicas_periodo", table_name="metricas_historicas")
    op.drop_index("ix_metricas_historicas_indicador", table_name="metricas_historicas")
    op.drop_index("ix_metricas_historicas_vertical", table_name="metricas_historicas")
    op.drop_index("ux_metricas_hist_vertical_indicador_periodo", table_name="metricas_historicas")
    op.drop_table("metricas_historicas")
