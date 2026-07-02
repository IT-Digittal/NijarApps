"""Ficha del cliente, campañas turísticas y flujo editorial de contenidos.

Añade:
- Tabla ``clientes`` (bloque 1 del pliego: ficha general del Ayuntamiento).
- Tabla ``campanas`` (bloque 9: campañas de promoción turística).
- Columnas ``fecha_aprobacion`` / ``fecha_publicacion`` en ``contenidos`` para
  medir el KPI de tiempo de publicación (≤ 24 h desde la aprobación).

Revision ID: 004_cliente_campana_contenidos
Revises: 003_incidencias
Create Date: 2026-07-02 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_cliente_campana_contenidos"
down_revision: Union[str, None] = "003_incidencias"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------------- clientes
    op.create_table(
        "clientes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("area_responsable", sa.String(255)),
        sa.Column("proyecto", sa.String(255)),
        sa.Column("descripcion", sa.Text()),
        sa.Column("cif", sa.String(20)),
        sa.Column("direccion", sa.String(500)),
        sa.Column("municipio", sa.String(100), nullable=False, server_default="Níjar"),
        sa.Column("provincia", sa.String(100), nullable=False, server_default="Almería"),
        sa.Column("responsable_municipal", sa.JSON()),
        sa.Column("responsables_tecnicos", sa.JSON()),
        sa.Column("canales_oficiales", sa.JSON()),
        sa.Column("idiomas_activos", postgresql.ARRAY(sa.String())),
        sa.Column("fecha_inicio_explotacion", sa.DateTime(timezone=True)),
        sa.Column("fecha_fin_mantenimiento", sa.DateTime(timezone=True)),
        sa.Column("hitos", sa.JSON()),
        sa.Column("activo", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("metadata_adicional", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_clientes_nombre", "clientes", ["nombre"])

    # ---------------------------------------------------------------- campanas
    op.create_table(
        "campanas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("nombre", sa.String(255), nullable=False),
        sa.Column("fecha_inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fecha_fin", sa.DateTime(timezone=True), nullable=False),
        sa.Column("slug", sa.String(120)),
        sa.Column("descripcion", sa.Text()),
        sa.Column("objetivo", sa.String(30), nullable=False, server_default="difusion"),
        sa.Column("publico_objetivo", sa.String(255)),
        sa.Column("canales", postgresql.ARRAY(sa.String())),
        sa.Column("presupuesto", sa.Numeric(12, 2)),
        sa.Column("landing_url", sa.String(500)),
        sa.Column(
            "recurso_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recursos_turisticos.id", ondelete="SET NULL"),
        ),
        sa.Column("estado", sa.String(20), nullable=False, server_default="planificada"),
        sa.Column("kpis_objetivo", sa.JSON()),
        sa.Column("resultados", sa.JSON()),
        sa.Column("etiquetas", postgresql.ARRAY(sa.String())),
        sa.Column("metadata_adicional", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_campanas_nombre", "campanas", ["nombre"])
    op.create_index("ix_campanas_slug", "campanas", ["slug"], unique=True)
    op.create_index("ix_campanas_fecha_inicio", "campanas", ["fecha_inicio"])
    op.create_index("ix_campanas_fecha_fin", "campanas", ["fecha_fin"])
    op.create_index("ix_campanas_estado", "campanas", ["estado"])
    op.create_index("ix_campanas_recurso_id", "campanas", ["recurso_id"])
    op.create_index("ix_campanas_fechas", "campanas", ["fecha_inicio", "fecha_fin"])
    op.create_index("ix_campanas_estado_inicio", "campanas", ["estado", "fecha_inicio"])

    # -------------------------------------------------- columnas en contenidos
    op.add_column(
        "contenidos",
        sa.Column("fecha_aprobacion", sa.DateTime(timezone=True)),
    )
    op.add_column(
        "contenidos",
        sa.Column("fecha_publicacion", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_column("contenidos", "fecha_publicacion")
    op.drop_column("contenidos", "fecha_aprobacion")

    op.drop_index("ix_campanas_estado_inicio", table_name="campanas")
    op.drop_index("ix_campanas_fechas", table_name="campanas")
    op.drop_index("ix_campanas_recurso_id", table_name="campanas")
    op.drop_index("ix_campanas_estado", table_name="campanas")
    op.drop_index("ix_campanas_fecha_fin", table_name="campanas")
    op.drop_index("ix_campanas_fecha_inicio", table_name="campanas")
    op.drop_index("ix_campanas_slug", table_name="campanas")
    op.drop_index("ix_campanas_nombre", table_name="campanas")
    op.drop_table("campanas")

    op.drop_index("ix_clientes_nombre", table_name="clientes")
    op.drop_table("clientes")
