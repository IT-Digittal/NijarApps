"""Registro de eventos de las verticales y último estado conocido de cada activo.

Revision ID: 019_registros_verticales
Revises: 018_origen_metricas
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "019_registros_verticales"
down_revision: Union[str, None] = "018_origen_metricas"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _marcas() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "registros_verticales",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vertical", sa.String(20), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("severidad", sa.String(10), nullable=False),
        sa.Column("mensaje", sa.Text(), nullable=False),
        sa.Column("momento", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activo_codigo", sa.String(60), nullable=True),
        sa.Column("activo_nombre", sa.String(200), nullable=True),
        sa.Column("origen", sa.String(30), nullable=False, server_default="plataforma"),
        sa.Column("datos", sa.JSON(), nullable=True),
        sa.Column("demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        *_marcas(),
    )
    op.create_index("ix_registros_vertical_momento", "registros_verticales", ["vertical", "momento"])
    op.create_index("ix_registros_activo", "registros_verticales", ["vertical", "activo_codigo"])
    op.create_index("ix_registros_verticales_tipo", "registros_verticales", ["tipo"])
    op.create_index("ix_registros_verticales_severidad", "registros_verticales", ["severidad"])
    op.create_index("ix_registros_verticales_momento", "registros_verticales", ["momento"])
    op.create_index("ix_registros_verticales_demo", "registros_verticales", ["demo"])
    op.create_table(
        "estados_activos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("vertical", sa.String(20), nullable=False),
        sa.Column("codigo", sa.String(60), nullable=False),
        sa.Column("estado", sa.String(60), nullable=False),
        *_marcas(),
        sa.UniqueConstraint("vertical", "codigo", name="uq_estado_activo"),
    )


def downgrade() -> None:
    op.drop_table("estados_activos")
    op.drop_table("registros_verticales")
