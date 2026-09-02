"""Mediciones guardadas de la regla del Gemelo vivo 2D.

Revision ID: 015_mediciones_gemelo
Revises: 014_capas_geograficas
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "015_mediciones_gemelo"
down_revision: Union[str, None] = "014_capas_geograficas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mediciones_gemelo",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("puntos", sa.JSON(), nullable=False),
        sa.Column("distancia_m", sa.Float(), nullable=False),
        sa.Column("area_m2", sa.Float(), nullable=True),
        sa.Column("creado_por", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_mediciones_gemelo_creado_por", "mediciones_gemelo", ["creado_por"])


def downgrade() -> None:
    op.drop_index("ix_mediciones_gemelo_creado_por", table_name="mediciones_gemelo")
    op.drop_table("mediciones_gemelo")
