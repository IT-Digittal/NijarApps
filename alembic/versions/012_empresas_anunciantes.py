"""Empresas anunciantes (módulo de publicidad del destino).

Revision ID: 012_empresas_anunciantes
Revises: 011_documentos_puntos
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_empresas_anunciantes"
down_revision: Union[str, None] = "011_documentos_puntos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "empresas_anunciantes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(30), nullable=False),
        sa.Column("descripcion", sa.Text),
        sa.Column("descripcion_i18n", sa.JSON),
        sa.Column("nucleo", sa.String(120)),
        sa.Column("direccion", sa.String(255)),
        sa.Column("telefono", sa.String(40)),
        sa.Column("web", sa.String(255)),
        sa.Column("email", sa.String(255)),
        sa.Column("imagenes", postgresql.ARRAY(sa.String)),
        sa.Column("latitud", sa.Float),
        sa.Column("longitud", sa.Float),
        sa.Column("destacado", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("prioridad", sa.Integer, nullable=False, server_default="0"),
        sa.Column("publicado", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("campana_desde", sa.DateTime(timezone=True)),
        sa.Column("campana_hasta", sa.DateTime(timezone=True)),
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
    op.create_index("ix_empresas_anunciantes_nombre", "empresas_anunciantes", ["nombre"])
    op.create_index("ix_empresas_anunciantes_sector", "empresas_anunciantes", ["sector"])
    op.create_index("ix_empresas_anunciantes_publicado", "empresas_anunciantes", ["publicado"])


def downgrade() -> None:
    op.drop_index("ix_empresas_anunciantes_publicado", table_name="empresas_anunciantes")
    op.drop_index("ix_empresas_anunciantes_sector", table_name="empresas_anunciantes")
    op.drop_index("ix_empresas_anunciantes_nombre", table_name="empresas_anunciantes")
    op.drop_table("empresas_anunciantes")
