"""Tabla incidencias (ticketing del mantenimiento C.1).

Fuente real del informe mensual de servicio: disponibilidad por componente,
recuento por severidad, tiempos y cumplimiento ANS.

Revision ID: 003_incidencias
Revises: 002_contexto_turistico
Create Date: 2026-06-18 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_incidencias"
down_revision: Union[str, None] = "002_contexto_turistico"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incidencias",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("severidad", sa.String(20), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("componente", sa.String(60), nullable=False),
        sa.Column("detectada_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column("estado", sa.String(20), nullable=False, server_default="abierta"),
        sa.Column("origen", sa.String(20), nullable=False, server_default="ticketing"),
        sa.Column("afecta_disponibilidad", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("es_preventiva", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("es_evento_seguridad", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("incidente_confirmado", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("respondida_en", sa.DateTime(timezone=True)),
        sa.Column("resuelta_en", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_incidencias_severidad", "incidencias", ["severidad"])
    op.create_index("ix_incidencias_componente", "incidencias", ["componente"])
    op.create_index("ix_incidencias_detectada_en", "incidencias", ["detectada_en"])
    op.create_index("ix_incidencias_estado", "incidencias", ["estado"])
    op.create_index(
        "ix_incidencias_severidad_detectada", "incidencias", ["severidad", "detectada_en"]
    )
    op.create_index(
        "ix_incidencias_estado_detectada", "incidencias", ["estado", "detectada_en"]
    )


def downgrade() -> None:
    op.drop_index("ix_incidencias_estado_detectada", table_name="incidencias")
    op.drop_index("ix_incidencias_severidad_detectada", table_name="incidencias")
    op.drop_index("ix_incidencias_estado", table_name="incidencias")
    op.drop_index("ix_incidencias_detectada_en", table_name="incidencias")
    op.drop_index("ix_incidencias_componente", table_name="incidencias")
    op.drop_index("ix_incidencias_severidad", table_name="incidencias")
    op.drop_table("incidencias")
