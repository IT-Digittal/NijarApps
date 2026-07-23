"""Documentos adjuntos a puntos del territorio (gemelo digital).

Revision ID: 011_documentos_puntos
Revises: 010_historico_verticales
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011_documentos_puntos"
down_revision: Union[str, None] = "010_historico_verticales"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documentos_puntos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entidad_tipo", sa.String(30), nullable=False),
        sa.Column("entidad_id", sa.String(255), nullable=False),
        sa.Column("entidad_nombre", sa.String(255), nullable=False),
        sa.Column("latitud", sa.Float),
        sa.Column("longitud", sa.Float),
        sa.Column("nombre_archivo", sa.String(255), nullable=False),
        sa.Column("descripcion", sa.String(500)),
        sa.Column("tipo_mime", sa.String(120), nullable=False),
        sa.Column("tamano_bytes", sa.Integer, nullable=False),
        sa.Column("ruta_almacen", sa.String(500), nullable=False),
        sa.Column("subido_por", sa.String(255)),
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
    op.create_index("ix_documentos_entidad", "documentos_puntos", ["entidad_tipo", "entidad_id"])
    op.create_index(
        "ix_documentos_puntos_entidad_tipo", "documentos_puntos", ["entidad_tipo"]
    )
    op.create_index("ix_documentos_puntos_entidad_id", "documentos_puntos", ["entidad_id"])


def downgrade() -> None:
    op.drop_index("ix_documentos_puntos_entidad_id", table_name="documentos_puntos")
    op.drop_index("ix_documentos_puntos_entidad_tipo", table_name="documentos_puntos")
    op.drop_index("ix_documentos_entidad", table_name="documentos_puntos")
    op.drop_table("documentos_puntos")
