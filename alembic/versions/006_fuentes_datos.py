"""Catálogo de fuentes de datos e integraciones de la plataforma.

Inventario de fuentes propias (las genera nuestra solución) y externas
(accesos a facilitar por el Ayuntamiento), con su estado de integración.

Revision ID: 006_fuentes_datos
Revises: 005_smart_city_verticales
Create Date: 2026-07-03 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_fuentes_datos"
down_revision: Union[str, None] = "005_smart_city_verticales"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fuentes_datos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo", sa.String(20), nullable=False, unique=True),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("categoria", sa.String(60), nullable=False),
        sa.Column("origen", sa.String(20), nullable=False),
        sa.Column("estado", sa.String(30), nullable=False),
        sa.Column("tipo_conexion", sa.String(60)),
        sa.Column("sistema", sa.String(200)),
        sa.Column("responsable", sa.String(120)),
        sa.Column("requiere_credenciales", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("credenciales_desc", sa.String(300)),
        sa.Column("endpoint_url", sa.String(300)),
        sa.Column("periodicidad", sa.String(60)),
        sa.Column("formato", sa.String(60)),
        sa.Column("kpis_asociados", postgresql.ARRAY(sa.String())),
        sa.Column("notas", sa.Text()),
        sa.Column("metadatos", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_fuentes_datos_codigo", "fuentes_datos", ["codigo"])
    op.create_index("ix_fuentes_datos_categoria", "fuentes_datos", ["categoria"])
    op.create_index("ix_fuentes_datos_origen", "fuentes_datos", ["origen"])
    op.create_index("ix_fuentes_datos_estado", "fuentes_datos", ["estado"])


def downgrade() -> None:
    op.drop_table("fuentes_datos")
