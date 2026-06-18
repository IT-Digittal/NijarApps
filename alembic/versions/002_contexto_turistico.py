"""Tabla contexto_turistico (backfill de fuentes públicas oficiales).

Añade el "background poblacional" del observatorio Big Data: series
históricas oficiales (INE Frontur/Egatur/EOH, Junta de Andalucía, AENA).

Revision ID: 002_contexto_turistico
Revises: 001_initial
Create Date: 2026-06-18 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_contexto_turistico"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contexto_turistico",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("fuente", sa.String(40), nullable=False),
        sa.Column("indicador", sa.String(120), nullable=False),
        sa.Column("periodo", sa.String(10), nullable=False),
        sa.Column("valor", sa.Numeric(18, 4), nullable=False),
        sa.Column("unidad", sa.String(40)),
        sa.Column("ambito", sa.String(40), nullable=False, server_default="provincia_almeria"),
        sa.Column("metadatos", postgresql.JSON()),
        sa.Column("capturado_en", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_contexto_turistico_fuente", "contexto_turistico", ["fuente"])
    op.create_index("ix_contexto_turistico_indicador", "contexto_turistico", ["indicador"])
    op.create_index("ix_contexto_turistico_periodo", "contexto_turistico", ["periodo"])
    op.create_index("ix_contexto_turistico_ambito", "contexto_turistico", ["ambito"])
    op.create_index(
        "ux_contexto_fuente_indicador_periodo_ambito",
        "contexto_turistico",
        ["fuente", "indicador", "periodo", "ambito"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_contexto_fuente_indicador_periodo_ambito", table_name="contexto_turistico")
    op.drop_index("ix_contexto_turistico_ambito", table_name="contexto_turistico")
    op.drop_index("ix_contexto_turistico_periodo", table_name="contexto_turistico")
    op.drop_index("ix_contexto_turistico_indicador", table_name="contexto_turistico")
    op.drop_index("ix_contexto_turistico_fuente", table_name="contexto_turistico")
    op.drop_table("contexto_turistico")
