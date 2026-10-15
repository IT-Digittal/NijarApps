"""Datos eléctricos de Datadis: agregado diario municipal y curva horaria por CUPS.

Revision ID: 016_energia_datadis
Revises: 015_mediciones_gemelo
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "016_energia_datadis"
down_revision: Union[str, None] = "015_mediciones_gemelo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _tiempos() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "energia_municipio_diario",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("sector", sa.String(60), nullable=False),
        sa.Column("tension", sa.String(60), nullable=False),
        sa.Column("contratos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("energia_kwh", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("municipio", sa.String(80), nullable=False, server_default="NÍJAR"),
        sa.Column("fuente", sa.String(30), nullable=False, server_default="datadis"),
        *_tiempos(),
        sa.UniqueConstraint("fecha", "sector", "tension", name="uq_energia_municipio_dia"),
    )
    op.create_index("ix_energia_municipio_fecha", "energia_municipio_diario", ["fecha"])

    op.create_table(
        "energia_consumos_horarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cups", sa.String(30), nullable=False),
        sa.Column("momento", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumo_kwh", sa.Numeric(12, 4), nullable=False, server_default="0"),
        sa.Column("excedente_kwh", sa.Numeric(12, 4), nullable=True),
        sa.Column("autoconsumo_kwh", sa.Numeric(12, 4), nullable=True),
        sa.Column("metodo", sa.String(20), nullable=True),
        *_tiempos(),
        sa.UniqueConstraint("cups", "momento", name="uq_energia_consumo_cups_momento"),
    )
    op.create_index(
        "ix_energia_consumos_cups_momento", "energia_consumos_horarios", ["cups", "momento"]
    )


def downgrade() -> None:
    op.drop_index("ix_energia_consumos_cups_momento", table_name="energia_consumos_horarios")
    op.drop_table("energia_consumos_horarios")
    op.drop_index("ix_energia_municipio_fecha", table_name="energia_municipio_diario")
    op.drop_table("energia_municipio_diario")
