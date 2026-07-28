"""Capas geográficas del gemelo 2D (planeamiento, catastro, clasificación).

Revision ID: 008_capas_geograficas
Revises: 007_consumo_ia
"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_capas_geograficas"
down_revision: Union[str, None] = "007_consumo_ia"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "capas_geograficas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("codigo", sa.String(80), nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("grupo", sa.String(30), nullable=False),
        sa.Column("tipo_geometria", sa.String(20), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column("color", sa.String(9), nullable=False, server_default="#7C6BF0"),
        sa.Column("color_borde", sa.String(9), nullable=False, server_default="#3A2FA0"),
        sa.Column("opacidad", sa.Float, nullable=False, server_default="0.35"),
        sa.Column("campo_etiqueta", sa.String(80)),
        sa.Column("orden", sa.Integer, nullable=False, server_default="0"),
        sa.Column("activa", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("fuente", sa.String(255)),
        sa.Column("metadatos", sa.JSON()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_capas_geograficas_codigo", "capas_geograficas", ["codigo"], unique=True)
    op.create_index("ix_capas_geograficas_grupo", "capas_geograficas", ["grupo"])

    op.create_table(
        "elementos_geograficos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "capa_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("capas_geograficas.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column(
            "geometria",
            geoalchemy2.types.Geometry(
                geometry_type="GEOMETRY", srid=4326, spatial_index=False
            ),
            nullable=False,
        ),
        sa.Column("codigo", sa.String(120)),
        sa.Column("referencia_catastral", sa.String(20)),
        sa.Column("propiedades", sa.JSON()),
        sa.Column("orden", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_elementos_geograficos_capa", "elementos_geograficos", ["capa_id", "orden"])
    op.create_index(
        "ix_elementos_geograficos_refcat", "elementos_geograficos", ["referencia_catastral"]
    )
    op.execute(
        "CREATE INDEX ix_elementos_geograficos_geom "
        "ON elementos_geograficos USING GIST(geometria)"
    )


def downgrade() -> None:
    op.drop_index("ix_elementos_geograficos_geom", table_name="elementos_geograficos")
    op.drop_index("ix_elementos_geograficos_refcat", table_name="elementos_geograficos")
    op.drop_index("ix_elementos_geograficos_capa", table_name="elementos_geograficos")
    op.drop_table("elementos_geograficos")
    op.drop_index("ix_capas_geograficas_grupo", table_name="capas_geograficas")
    op.drop_index("ix_capas_geograficas_codigo", table_name="capas_geograficas")
    op.drop_table("capas_geograficas")
